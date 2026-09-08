"""SwitchF1: directed aligned boundaries in explicitly language-labeled text."""
from .metric import evaluate, score_utterance, aggregate, Token, SPECIFICATIONS

__version__ = "0.3.0"
__all__ = ["evaluate", "score_utterance", "aggregate", "Token", "SPECIFICATIONS"]
