import regex as re
import get_data_set as gdt
import json, os

def split_text(patterns, text):
    return re.findall(patterns, text)

def convert_segments_to_utf8(segments, specials_map={}):
    # return [list(map(int, segment.encode("utf-8"))) for segment in segments]
    """
    segments: list[str] (tokens produits par split_text)
    specials_map: dict[token_str] -> reserved_id (int)
    retourne: list[list[int]] where each inner list is either:
      - [reserved_id] for a special token
      - list(byte values) for normal tokens
    """
    out = []
    for segment in segments:
        if segment in specials_map:
            out.append([specials_map[segment]])
        else:
            # ordinary token: bytes -> list of ints
            out.append(list(segment.encode("utf-8")))
    return out

def get_stats(ids):
    counts = {}
    for pair in zip(ids, ids[1:]): # python way to iterate 2 consecutive elts
        counts[pair] = counts.get(pair, 0) + 1
    return counts

def get_stats2(segments):
    counts = {}
    for segment in segments:

        for pair in zip(segment, segment[1:]): # python way to iterate 2 consecutive elts
            counts[pair] = counts.get(pair, 0) + 1
    return counts

def merge(ids, pair, idx):
    newids = []
    i = 0
    while i < len(ids):
        if i < len(ids) -1 and ids[i] == pair[0] and ids[i+1] == pair[1]:
            newids.append(idx)
            i += 2
        else:
            newids.append(ids[i])
            i += 1
    return newids

def merge2(segments, pair, idx):
    newsegments = []
    for segment in segments:
        newsegment = []

        i = 0
        while i < len(segment):
            if i < len(segment) -1 and segment[i] == pair[0] and segment[i+1] == pair[1]:
                newsegment.append(idx)
                i += 2
            else:
                newsegment.append(segment[i])
                i += 1
        newsegments.append(newsegment)
    return newsegments

# def tokenize(text):
#     tokens = text.encode("utf-8")
#     tokens = list(map(int, tokens))

#     vocab_size = 256 + 20
#     num_merges = vocab_size - 256
#     ids = list(tokens)

#     merges = {} # (int, int) -> int

#     for i in range(num_merges):
#         stats = get_stats(ids)
#         pair = max(stats, key=stats.get)
#         idx = 256 + i
#         print("merging {} -> {}".format(pair, idx))
#         ids = merge(ids, pair, idx)
#         merges[pair] = idx

#     print("token length: {}".format(len(tokens)))
#     print("ids length: {}".format(len(ids)))
#     print("compression ratio: {}x".format(len(tokens) / len(ids)))
#     return merges

def insert_special_tokens(segments, special_tokens_map):
    newsegments = []
    for segment in segments:
        if segment in special_tokens_map.values():
            newsegments.append(special_tokens_map[special_tokens_map.index(segment)])
        else:
            newsegments.append(segment)
    return newsegments

def tokenize2(text):
    """
    Should have been called train but dw
    """
    
    patterns = re.compile(
    r"(?i)"
    r"<\|(?:who_i_am|end_who_i_am|bos|eos)\|>|"                       # tokens spéciaux
    r".?(?:[cdjlmnst]|qu)'|'(?:[sdmt]|ll|ve|re)|"                     # contractions
    r"[^\r\n\p{L}\p{N}]?+\p{L}++|"                                    # mots (lettres)
    r"\p{N}{1,3}+|"                                                   # nombres
    r" ?[^\s\p{L}\p{N}<>]++[\r\n]*+|"                                 # ponctuation **sans < et >**
    r"\s++$|\s*[\r\n]|\s+(?!\S)|\s"
    )

    base_bytes = 256
    special_tokens = ["<|who_i_am|>", "<end_who_i_am|>", "<|bos|>", "<|eos|>"]
    special_tokens_map = {token: base_bytes + i for i, token in enumerate(special_tokens)}
    reserved_after_special_tokens = base_bytes + len(special_tokens)

    vocab_size = reserved_after_special_tokens + 500
    num_merges = vocab_size - reserved_after_special_tokens
    

    segments = split_text(patterns, text)
    segments = convert_segments_to_utf8(segments)

    merges = {}
    for i in range(num_merges):
        
        stats = get_stats2(segments)
        pair = max(stats, key=stats.get)
        idx = reserved_after_special_tokens + i

        vocab = {idx: bytes([idx]) for idx in range(256)}
        for tok ,id_ in special_tokens_map.items():
            vocab[id_] = tok.encode("utf-8")
        for (p0, p1), idx2 in merges.items():
            vocab[idx2] = vocab[p0] + vocab[p1]
        print("merging {} -> {} ({})".format(pair, idx, decode(vocab, pair)))

        segments = merge2(segments, pair, idx)
        merges[pair] = idx
    
    return merges
def decode(vocab, ids):
        
        tokens = b"".join(vocab[idx] for idx in ids)
        text = tokens.decode("utf-8", errors="replace")
        return text

def encode(merges, text):
    specials_map = {
            "<|who_i_am|>": 256,
            "<|end_who_i_am|>": 257,
            "<|bos|>": 258,
            "<|eos|>": 259
        }

    pattern = re.compile(
        r"(?i)"
        r"<\|(?:who_i_am|end_who_i_am|bos|eos)\|>|"
        r".?(?:[cdjlmnst]|qu)'|'(?:[sdmt]|ll|ve|re)|"
        r"[^\r\n\p{L}\p{N}]?+\p{L}++|"
        r"\p{N}{1,3}+|"
        r" ?[^\s\p{L}\p{N}<>]++[\r\n]*+|"
        r"\s++$|\s*[\r\n]|\s+(?!\S)|\s"
    )

    # Étape 1: découpage identique à l'entraînement
    segments = re.findall(pattern, text)

    # Étape 2: conversion en entiers (gérer specials)
    tokens = []
    for seg in segments:
        if seg in specials_map:
            tokens.append(specials_map[seg])
        else:
            tokens.extend(list(seg.encode("utf-8")))

    while(len(tokens) >= 2):
        stats = get_stats(tokens) #only care 'bout the keys
        pair = min(stats, key=lambda p: merges.get(p, float("inf"))) #for any pair inside stats looking into merges in what index it has, get the pair with the lowest index
        if pair not in merges:
            break # nothing else can be merged
        idx = merges[pair]
        tokens = merge(tokens, pair, idx)
    return tokens

def train(merges):
    """
    The name doesn't match but dw
    """


    print("vocab size: {}".format(len(merges) + 256))

    vocab = {idx: bytes([idx]) for idx in range(256)}

    special_tokens = ["<|who_i_am|>", "<end_who_i_am|>", "<|bos|>", "<|eos|>"]
    base_bytes = 256
    special_tokens_map = {token: base_bytes + i for i, token in enumerate(special_tokens)}

    for tok ,id_ in special_tokens_map.items():
        vocab[id_] = tok.encode("utf-8")
    
    for (p0, p1), idx in merges.items():
        vocab[idx] = vocab[p0] + vocab[p1]

    save_vocab(vocab, "vocab.json")
    return vocab

def save_vocab(vocab, path):
    vocab_serializable = {str(k): v.decode('latin-1') for k, v in vocab.items()}

    with open(path, "w", encoding="utf-8") as f:
        json.dump(vocab_serializable, f, ensure_ascii=False, indent=2)

def save_merges(merges, path):
    merges_serializable = [(a, b, new_id) for (a, b), new_id in merges.items()]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(merges_serializable, f, ensure_ascii=False, indent=2)

def load_vocab(path):
    with open(path, "r", encoding="utf-8") as f:
        vocab_loaded = {int(k): v.encode('latin-1') for k, v in json.load(f).items()}
        return vocab_loaded

def load_merges(path):
    with open(path, "r", encoding="utf-8") as f:
        merges_list = json.load(f)
        merges_loaded = {(a, b): new_id for a, b, new_id in merges_list}
        return merges_loaded

if __name__ == '__main__':
    

    if(os.path.exists("merges.json")):
        merges = load_merges("merges.json")
    else:
        merges = tokenize2(gdt.gather_datas())
        save_merges(merges, "merges.json")

    if os.path.exists("vocab.json"):
        with open ("vocab.json", "r", encoding="utf-8") as f:
            vocab = load_vocab("vocab.json")
    else:
        vocab = train(merges)

        
    # special_tokens = ["<|who_i_am|>", "<end_who_i_am|>", "<|bos|>", "<|eos|>"]
    # for i in range(len(special_tokens)):
    #     vocab[len(vocab)+i] = special_tokens[i].encode("utf-8")


    truc = encode(merges, "L'importation de librairie c'est super ! mais qu'est-ce que tu m'dis ??? Do you'd live if I'm knew how to speak english ._. 🚵‍♂️🚵‍♀️🌡⛱")
    truc = encode(merges, "hello <|eos|>")
    print(truc)
    print(decode(vocab, truc))

    # pattern = re.compile(
    # r"(?i)"
    # r"<\|(?:who_i_am|end_who_i_am|bos|eos)\|>|"                       # tokens spéciaux
    # r".?(?:[cdjlmnst]|qu)'|'(?:[sdmt]|ll|ve|re)|"                     # contractions
    # r"[^\r\n\p{L}\p{N}]?+\p{L}++|"                                    # mots (lettres)
    # r"\p{N}{1,3}+|"                                                   # nombres
    # r" ?[^\s\p{L}\p{N}<>]++[\r\n]*+|"                                 # ponctuation **sans < et >**
    # r"\s++$|\s*[\r\n]|\s+(?!\S)|\s"
    # )

    # text = "Hello <|eos|> world"
    # tokens = [m.group(0) for m in pattern.finditer(text)]
    # print(tokens)   # => ['Hello', ' ', '<|eos|>', ' world']

