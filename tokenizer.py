import regex as re
import get_data_set as gdt

def split_text(patterns, text):
    return re.findall(patterns, text)

def convert_segments_to_utf8(segments):
    return [list(map(int, segment.encode("utf-8"))) for segment in segments]

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

def tokenize(text):
    tokens = text.encode("utf-8")
    tokens = list(map(int, tokens))

    vocab_size = 256 + 20
    num_merges = vocab_size - 256
    ids = list(tokens)

    merges = {} # (int, int) -> int

    for i in range(num_merges):
        stats = get_stats(ids)
        pair = max(stats, key=stats.get)
        idx = 256 + i
        print("merging {} -> {}".format(pair, idx))
        ids = merge(ids, pair, idx)
        merges[pair] = idx

    print("token length: {}".format(len(tokens)))
    print("ids length: {}".format(len(ids)))
    print("compression ratio: {}x".format(len(tokens) / len(ids)))
    return merges

def tokenize2(text):
    patterns = re.compile(r"""'(?i:[sdmt]|ll|ve|re)|[^\r\n\p{L}\p{N}]?+\p{L}++|\p{N}{1,3}+| ?[^\s\p{L}\p{N}]++[\r\n]*+|\s++$|\s*[\r\n]|\s+(?!\S)|\s""")

    segments = split_text(patterns, text)
    segments = convert_segments_to_utf8(segments)

    vocab_size = 256 + 64
    num_merges = vocab_size - 256

    merges = {}
    for i in range(num_merges):
        
        stats = get_stats2(segments)
        pair = max(stats, key=stats.get)
        idx = 256 + i
        print("merging {} -> {}".format(pair, idx))
        segments = merge2(segments, pair, idx)
        merges[pair] = idx
    
    return merges

if __name__ == '__main__':
    merges = tokenize2("This is under construction don't mind. Yeah it's called developpment not constrcution but you got the point shut it >:()")

    vocab = {idx: bytes([idx]) for idx in range(256)}
    for (p0, p1), idx in merges.items():
        vocab[idx] = vocab[p0] + vocab[p1]

    def decode(ids):
        tokens = b"".join(vocab[idx] for idx in ids)
        text = tokens.decode("utf-8", errors="replace")
        return text

    def encode(text):
        tokens = list(text.encode("utf-8"))
        while(len(tokens) >= 2):
            stats = get_stats(tokens) #only care 'bout the keys
            pair = min(stats, key=lambda p: merges.get(p, float("inf"))) #for any pair inside stats looking into merges in what index it has, get the pair with the lowest index
            if pair not in merges:
                break # nothing else can be merged
            idx = merges[pair]
            tokens = merge(tokens, pair, idx)
        return tokens


    truc = encode("Hello my lil Alexouuuu :)) ^^")
    print(truc)
    print(decode(truc))

    print(gdt.gather_datas())

    # print(re.findall(patterns, decode(truc)))
