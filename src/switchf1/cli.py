import argparse
import hashlib
import json
from pathlib import Path
from . import __version__,evaluate

def main():
    p=argparse.ArgumentParser(description="Score directed switches in explicitly language-labeled text. No timestamps required.")
    p.add_argument('input',type=Path,help='JSONL with id, reference and hypothesis token arrays')
    p.add_argument('--mode',choices=['anchored','boundary'],default='anchored')
    p.add_argument('--output',type=Path)
    args=p.parse_args()
    raw=args.input.read_bytes()
    result=evaluate([json.loads(line) for line in raw.decode('utf-8').splitlines() if line.strip()],mode=args.mode)
    result.update(package_version=__version__,input_sha256=hashlib.sha256(raw).hexdigest())
    text=json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(text,encoding='utf-8')
    else:print(text,end='')

if __name__=='__main__':main()
