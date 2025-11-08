import regex as re
import json
import os
from typing import List, Tuple, Dict
from fastbpe._fastbpe import Tokenizer as CoreTokenizer  # <-- backend C++ compilé


# ===============================
#   RÉGEX ET CONSTANTES GLOBALES
# ===============================
PATTERN = re.compile(
    r"(?i)"
    r"<\|(?:who_i_am|end_who_i_am|bos|eos|pad)\|>|"       # tokens spéciaux
    r".?(?:[cdjlmnst]|qu)'|'(?:[sdmt]|ll|ve|re)|"         # contractions
    r"[^\r\n\p{L}\p{N}]?+\p{L}++|"                        # mots (lettres)
    r"\p{N}{1,3}+|"                                       # nombres
    r" ?[^\s\p{L}\p{N}<>]++[\r\n]*+|"                     # ponctuation
    r"\s++$|\s*[\r\n]|\s+(?!\S)|\s"                       # espaces
)

SPECIAL_TOKENS = ["<|who_i_am|>", "<|end_who_i_am|>", "<|bos|>", "<|eos|>", "<|pad|>"]
BASE_BYTES = 256


# ===============================
#   FONCTIONS UTILITAIRES JSON
# ===============================
def save_vocab(vocab: Dict[int, bytes], path: str):
    vocab_serializable = {str(k): v.decode('latin-1') for k, v in vocab.items()}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(vocab_serializable, f, ensure_ascii=False, indent=2)


def save_merges(merges: Dict[Tuple[int, int], int], path: str):
    merges_serializable = [(a, b, new_id) for (a, b), new_id in merges.items()]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(merges_serializable, f, ensure_ascii=False, indent=2)


def load_vocab(path: str) -> Dict[int, bytes]:
    with open(path, "r", encoding="utf-8") as f:
        return {int(k): v.encode('latin-1') for k, v in json.load(f).items()}


def load_merges(path: str) -> Dict[Tuple[int, int], int]:
    with open(path, "r", encoding="utf-8") as f:
        merges_list = json.load(f)
        return {(a, b): new_id for a, b, new_id in merges_list}


# ===============================
#   CLASSE TOKENIZER PYTHON
# ===============================
class Tokenizer:
    """
    Tokenizer Python qui encapsule le backend C++ (_fastbpe).
    Utilise le regex Python, les sauvegardes JSON, et délègue
    les opérations lourdes (get_stats, merge, encode, decode) à C++.
    """

    def __init__(self, vocab_size: int = 8192):
        self.patterns = PATTERN
        self.special_tokens_map = {token: BASE_BYTES + i for i, token in enumerate(SPECIAL_TOKENS)}
        self.reserved_after_special_tokens = BASE_BYTES + len(SPECIAL_TOKENS)
        self.vocab_size = vocab_size
        self.num_merges = vocab_size - self.reserved_after_special_tokens

        # Vocab: id -> bytes
        self.vocab: Dict[int, bytes] = {idx: bytes([idx]) for idx in range(256)}
        self.merges: Dict[Tuple[int, int], int] = {}

        # Core C++ tokenizer
        self.core = CoreTokenizer(vocab_size)

        # Charger merges/vocab si existants
        if os.path.exists("merges.json"):
            self.merges = load_merges("merges.json")
        if os.path.exists("vocab.json"):
            self.vocab = load_vocab("vocab.json")

    # --------------------------
    #    MÉTHODES DE SPLIT
    # --------------------------
    def split_text(self, text: str) -> List[str]:
        return re.findall(self.patterns, text)

    def convert_segments_to_utf8(self, segments: List[str]) -> List[List[int]]:
        """
        Convertit les segments texte en liste d'octets UTF-8 (list[list[int]]).
        """
        out = []
        for segment in segments:
            if segment in self.special_tokens_map:
                out.append([self.special_tokens_map[segment]])
            else:
                out.append(list(segment.encode("utf-8")))
        return out

    # --------------------------
    #    ENTRAÎNEMENT (TOKENIZE)
    # --------------------------
    def tokenize(self, text: str):
        """
        Entraîne un vocabulaire BPE sur le texte fourni :
        - calcule les statistiques de paires
        - fusionne les plus fréquentes
        - enregistre vocab.json et merges.json
        """
        segments_str = self.split_text(text)
        segments = self.convert_segments_to_utf8(segments_str)

        for i in range(self.num_merges):
            stats = self.core.get_stats(segments)
            if not stats:
                break

            # Trouve la paire la plus fréquente
            best_pair = max(stats.items(), key=lambda kv: kv[1])[0]
            idx = self.reserved_after_special_tokens + i
            self.merges[best_pair] = idx

            # Appliquer la fusion via C++
            segments = self.core.merge_segments(segments, best_pair, idx)

            # Mettre à jour le vocab
            a, b = best_pair
            part_a = self.vocab.get(a, None)
            part_b = self.vocab.get(b, None)
            if part_a is not None and part_b is not None:
                self.vocab[idx] = part_a + part_b
            else:
                self.vocab[idx] = bytes([idx])

            # Log progress
            try:
                pair_repr = (
                    self.vocab.get(best_pair[0], b"?").decode("latin-1", errors="replace"),
                    self.vocab.get(best_pair[1], b"?").decode("latin-1", errors="replace")
                )
                print(f"merging {best_pair} -> {idx} ({pair_repr})")
            except Exception:
                print(f"merging {best_pair} -> {idx}")

        # Sauvegarde finale
        save_merges(self.merges, "merges.json")
        save_vocab(self.vocab, "vocab.json")

    # --------------------------
    #    ENCODAGE / DÉCODAGE
    # --------------------------
    def encode(self, text: str) -> List[int]:
        """
        Encode une chaîne de caractères en liste d'IDs.
        Utilise le backend C++ pour appliquer les merges.
        """
        segments = re.findall(self.patterns, text)
        tokens: List[int] = []
        for seg in segments:
            if seg in self.special_tokens_map:
                tokens.append(self.special_tokens_map[seg])
            else:
                tokens.extend(list(seg.encode("utf-8")))

        if len(tokens) < 2:
            return tokens

        encoded = self.core.encode(tokens, self.merges)
        return encoded

    def decode(self, ids: List[int]) -> str:
        """
        Décode une liste d'IDs en texte.
        """
        vocab_str_map = {k: v.decode("latin-1") for k, v in self.vocab.items()}
        s = self.core.decode(ids, vocab_str_map)
        b = s.encode("latin-1")
        return b.decode("utf-8", errors="replace")
