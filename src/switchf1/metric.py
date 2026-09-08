"""Aligned boundary F1, with optional lexical anchoring. See docs/method.md."""
from __future__ import annotations
from dataclasses import dataclass
import unicodedata

UNKNOWN = frozenset({"und", "mul", "ambiguous"})
MODES = frozenset({"anchored", "boundary", "boundary_exact"})
SPECIFICATIONS = {"boundary": "switchf1-boundary-v2",
                  "boundary_exact": "switchf1-boundary-v1", "anchored": "ase-f1-v1"}

@dataclass(frozen=True)
class Token:
    text: str
    lang: str | None

def normalize(text: str) -> str:
    """NFC and lowercase only. No marks, words, repetitions or scripts removed."""
    return unicodedata.normalize("NFC", text).lower()

def _tokens(items, reference):
    if isinstance(items,(str,bytes)):
        raise ValueError("A plain transcript has no token-language labels. Supply Token objects or {text,lang} dictionaries; see README 'Where do the labels come from?'")
    tokens=[]
    for item in items:
        token=item if isinstance(item,Token) else Token(text=item['text'],lang=item['lang'])
        if not isinstance(token.text,str) or not token.text.strip():
            raise ValueError("Every token needs nonempty text; use [] for an empty transcript")
        if token.lang is not None and (not isinstance(token.lang,str) or not token.lang.strip()):
            raise ValueError("lang must be an explicit nonempty label or null for neutral")
        if token.lang in UNKNOWN:
            raise ValueError("Unresolved language label on reference or hypothesis. Resolve labels before scoring; abstention must not hide false switches.")
        tokens.append(token)
    return tokens

def _alignment(ref,hyp):
    """Lexical unit-cost Levenshtein; tie order: diagonal, deletion, insertion.

    Language IDs never influence alignment and cannot be permuted to help a model.
    """
    n,m=len(ref),len(hyp)
    dp=[[0]*(m+1) for _ in range(n+1)]
    for i in range(n+1): dp[i][0]=i
    for j in range(m+1): dp[0][j]=j
    for i in range(1,n+1):
        for j in range(1,m+1):
            dp[i][j]=min(dp[i-1][j-1]+(normalize(ref[i-1].text)!=normalize(hyp[j-1].text)),dp[i-1][j]+1,dp[i][j-1]+1)
    pairs=[];i,j=n,m
    while i or j:
        if i and j and dp[i][j]==dp[i-1][j-1]+(normalize(ref[i-1].text)!=normalize(hyp[j-1].text)):
            pairs.append((i-1,j-1));i-=1;j-=1
        elif i and dp[i][j]==dp[i-1][j]+1:
            pairs.append((i-1,None));i-=1
        else:pairs.append((None,j-1));j-=1
    return list(reversed(pairs))

def _events(tokens,columns):
    events=[];previous=None
    for i,t in enumerate(tokens):
        if t.lang is None:continue
        if t.lang in UNKNOWN:previous=None;continue
        if previous is not None:
            pi,p=previous
            if p.lang!=t.lang:
                events.append(dict(direction=[p.lang,t.lang],position=[columns[pi],columns[i]],
                    token_indices=[pi,i],anchors=[normalize(p.text),normalize(t.text)]))
        previous=(i,t)
    return events

def _prf(tp,fp,fn):
    return dict(tp=tp,fp=fp,fn=fn,precision=tp/(tp+fp) if tp+fp else None,
        recall=tp/(tp+fn) if tp+fn else None,
        f1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None)

def _boundary_matches(reference_events,hypothesis_events,alignment,hypothesis):
    """Match inside each reference boundary's supported alignment interval.

    Both reference endpoints must have aligned hypothesis tokens with the correct
    languages. Count every hypothesis event first, then select at most one event
    of the correct direction inside that interval. Reference boundary intervals
    have disjoint interiors; earliest-event tie-breaking does not optimize text
    alignment or discard false events.
    """
    matches=[];used=set()
    for i,event in enumerate(reference_events):
        left,right=event['position']
        hl,hr=alignment[left][1],alignment[right][1]
        if hl is None or hr is None:continue
        if [hypothesis[hl].lang,hypothesis[hr].lang]!=event['direction']:continue
        for j,predicted in enumerate(hypothesis_events):
            pl,pr=predicted['position']
            if j not in used and left<=pl<pr<=right and predicted['direction']==event['direction']:
                matches.append((i,j));used.add(j);break
    return matches

def score_utterance(reference,hypothesis,*,mode="boundary",utterance_id=""):
    """Score explicit Token objects or {text,lang} dictionaries.

    boundary (primary): correct direction inside a supported aligned boundary gap.
    boundary_exact: same two alignment columns, with substitutions allowed.
    anchored: exact columns and exact normalized lexical anchors.
    """
    if mode not in MODES:raise ValueError(f"mode must be one of {sorted(MODES)}")
    ref,hyp=_tokens(reference,True),_tokens(hypothesis,False)
    alignment=_alignment(ref,hyp)
    rp={ri:c for c,(ri,hi) in enumerate(alignment) if ri is not None}
    hp={hi:c for c,(ri,hi) in enumerate(alignment) if hi is not None}
    re,he=_events(ref,rp),_events(hyp,hp)
    def key(e):
        return (tuple(e['position']),tuple(e['direction']))+((tuple(e['anchors']),) if mode=='anchored' else ())
    if mode=='boundary':
        matches=_boundary_matches(re,he,alignment,hyp)
    else:
        predicted={key(e):j for j,e in enumerate(he)}
        matches=[(i,predicted[key(e)]) for i,e in enumerate(re) if key(e) in predicted]
    tp=len(matches)
    rl={t.lang for t in ref if t.lang is not None and t.lang not in UNKNOWN}
    hl={t.lang for t in hyp if t.lang is not None and t.lang not in UNKNOWN}
    token_counts={lang:dict(tp=0,fp=0,fn=0) for lang in sorted(rl|hl)}
    for ri,hi in alignment:
        gold=ref[ri].lang if ri is not None else None
        predicted_lang=hyp[hi].lang if hi is not None else None
        if gold==predicted_lang and gold is not None:
            token_counts[gold]['tp']+=1
        else:
            if gold is not None:token_counts[gold]['fn']+=1
            if predicted_lang is not None:token_counts[predicted_lang]['fp']+=1
    return dict(id=utterance_id,mode=mode,**_prf(tp,len(he)-tp,len(re)-tp),
        reference_events=len(re),hypothesis_events=len(he),
        reference_no_switch=not bool(re),false_switch_on_no_switch=not re and bool(he),
        language_presence_exact=rl==hl,unknown_hypothesis_tokens=sum(t.lang in UNKNOWN for t in hyp),
        reference_tokens=len(ref),hypothesis_tokens=len(hyp),
        matches_across_insertions=sum(re[i]['position']!=he[j]['position'] for i,j in matches),
        ref_events=re,hyp_events=he,matches=matches,alignment=alignment,token_language_counts=token_counts)

def aggregate(rows):
    """Pool event counts; never average utterance F1 or discard no-switch rows."""
    rows=list(rows)
    modes={r['mode'] for r in rows}
    if len(modes)>1:raise ValueError("Cannot pool different scoring modes")
    tp=sum(r['tp'] for r in rows);fp=sum(r['fp'] for r in rows);fn=sum(r['fn'] for r in rows)
    directions=sorted({tuple(e['direction']) for r in rows for e in r['ref_events']+r['hyp_events']})
    per_direction={}
    for direction in directions:
        nr=sum(tuple(e['direction'])==direction for r in rows for e in r['ref_events'])
        nh=sum(tuple(e['direction'])==direction for r in rows for e in r['hyp_events'])
        nt=sum(tuple(r['ref_events'][i]['direction'])==direction for r in rows for i,j in r['matches'])
        per_direction[' -> '.join(direction)]=_prf(nt,nh-nt,nr-nt)
    no_switch=sum(r['reference_no_switch'] for r in rows)
    false_no_switch=sum(r['false_switch_on_no_switch'] for r in rows)
    languages=sorted({lang for r in rows for lang in r['token_language_counts']})
    token_scores={}
    for lang in languages:
        counts={k:sum(r['token_language_counts'].get(lang,{}).get(k,0) for r in rows) for k in ['tp','fp','fn']}
        token_scores[lang]=_prf(**counts)
    token_micro=_prf(**{k:sum(v[k] for v in token_scores.values()) for k in ['tp','fp','fn']})
    token_macro=sum(v['f1'] for v in token_scores.values())/len(token_scores) if token_scores else None
    return dict(rows=len(rows),mode=next(iter(modes)) if modes else None,**_prf(tp,fp,fn),
        reference_events=tp+fn,hypothesis_events=tp+fp,
        reference_no_switch_rows=no_switch,false_switch_on_no_switch_rows=false_no_switch,
        false_switch_on_no_switch_rate=false_no_switch/no_switch if no_switch else None,
        language_presence_exact_rate=sum(r['language_presence_exact'] for r in rows)/len(rows) if rows else None,
        unknown_hypothesis_tokens=sum(r['unknown_hypothesis_tokens'] for r in rows),by_direction=per_direction,
        matches_across_insertions=sum(r.get('matches_across_insertions',0) for r in rows),
        aligned_token_language=dict(micro=token_micro,macro_f1=token_macro,per_language=token_scores))

def evaluate(records,*,mode="boundary"):
    """Evaluate {id, reference: token list, hypothesis: token list} records."""
    if mode not in MODES:raise ValueError(f"mode must be one of {sorted(MODES)}")
    records=list(records)
    if any(not all(k in r for k in ('id','reference','hypothesis')) for r in records):
        raise ValueError("Each record requires id, reference and hypothesis. Reference/hypothesis must be token lists with explicit text and lang, not plain ASR strings.")
    ids=[str(r['id']) for r in records]
    if len(ids)!=len(set(ids)):raise ValueError("Duplicate utterance IDs")
    rows=[score_utterance(r['reference'],r['hypothesis'],mode=mode,utterance_id=r['id']) for r in records]
    return dict(specification=SPECIFICATIONS[mode],mode=mode,metrics=aggregate(rows),utterances=rows)
