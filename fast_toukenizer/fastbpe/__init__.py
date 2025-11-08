# fastbpe/__init__.py
from ._fastbpe import Tokenizer as FastTokenizer      # backend C++
from .tokenizer_wrapper import Tokenizer as Tokenizer # wrapper Python

__all__ = ["Tokenizer", "FastTokenizer"]
__version__ = "0.2.1"