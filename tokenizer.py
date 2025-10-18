import regex as re

def get_stats(ids):
    counts = {}
    for pair in zip(ids, ids[1:]): # python way to iterate 2 consecutive elts
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
    

# text = "Hello ^^ I'm a text wééé, et pis qu'il y a de l'utf 8 🤔👀₽Ø⩁τŘ⨊"
# tokens = text.encode("utf-8")
# tokens = list(map(int, tokens))

# print(text)
# print("-----")
# print(len(text))
# print("-----\n-----")
# print(tokens)
# print("-----")
# print(len(tokens))

# stats = get_stats(tokens)
# print(sorted(((v, k) for k,v in stats.items()), reverse=True))

# top_pairs = max(stats, key=stats.get)
# tokens = merge(tokens, top_pairs, 256)
# print(tokens)
# print(len(tokens))

text = """Alexouuuuuuuuuuuuuuuuuuuuuuuuuuu

 — 09/10/2025 11:57
Bah tant mieux alors
Maxime PoutreMaker

 — 09/10/2025 13:16
On demande a reverdy au pire?
R3DWIN

 — 09/10/2025 16:07
Vrais question evan il s'en sort ou pas ?
Alexouuuuuuuuuuuuuuuuuuuuuuuuuuu

 — 09/10/2025 16:08
Eh bah.....
oui.
il est toujours là
R3DWIN

 — 09/10/2025 16:08
Chokbar
Alexouuuuuuuuuuuuuuuuuuuuuuuuuuu

 — 09/10/2025 16:08
y a 4 démissionnaires dans la classe à Kylian
et lui il est toujours là
R3DWIN

 — 09/10/2025 16:09
Ptn il d'accroche gg
Enfin ont sait pas cmb de temps mais ptn chuis choqué
Alexouuuuuuuuuuuuuuuuuuuuuuuuuuu

 — 09/10/2025 16:10
ouais nous aussi
Alexouuuuuuuuuuuuuuuuuuuuuuuuuuu

 — 10/10/2025 07:15
“Je réussis bien mais c’est les profs ils sont nuls, c’est pour ca que j’ai des mauvaises notes”
- Evan.
R3DWIN

 — 10/10/2025 07:16
Très étonnant dit donc
Glupyy Golub — 10/10/2025 07:37
based
Curses

 — 13/10/2025 02:20
bonjour j'espère que vous vous portez
tous*
que vous vous portez tous
Bamboo

 — 13/10/2025 09:17
Nous nous portons
King_of_steak — 13/10/2025 17:36
Je te soulève pour être plus précis
Curses

 — 13/10/2025 17:40
Tu es forr
Car ma masse est celle de 100 briques de lait
King_of_steak — 13/10/2025 17:42
Je pars chercher du lait
Alexouuuuuuuuuuuuuuuuuuuuuuuuuuu

 — 13/10/2025 17:46
Mais nan il est vivant
Curses

 — 13/10/2025 18:06
Oui je vis
Image
Actuellement dans une vidéo Feldup mais tout va bien
Bamboo

 — 13/10/2025 20:49
Bro is NOT making it past 30 🥀🙏
Curses

 — 13/10/2025 21:43
Pls at least 30! (I'm planning to seek females at around 32 to 36)
Bamboo

 — 14/10/2025 00:18
King_of_steak — 14/10/2025 06:35
😆
King_of_steak — 14/10/2025 06:35
T as dormis là?
King_of_steak — 14/10/2025 06:35
💘
King_of_steak — 14/10/2025 06:35
🤤
Curses

 — 14/10/2025 09:12
No
Curses

 — 14/10/2025 09:44
Image
Bamboo

 — 14/10/2025 09:50
meh, I don't think it tastes that good
(both) 
:stuff:
Alexouuuuuuuuuuuuuuuuuuuuuuuuuuu

 — 14/10/2025 09:50
💀
Alexouuuuuuuuuuuuuuuuuuuuuuuuuuu

 — 14/10/2025 09:51
We kinda are the same
Image
Bamboo

 — 14/10/2025 09:51
c'est tellement drôle de me dire que pendant que la prof de géopolitique parle de génocide des éthiopiens je suis en train de lire ça
on aime l'HGSSP :XD:
Bamboo

 — 14/10/2025 09:51
liminal ahh class
Alexouuuuuuuuuuuuuuuuuuuuuuuuuuu

 — 14/10/2025 09:52
bon par contre il fait -672612781°C dans l'amphi
Bamboo

 — 14/10/2025 11:21
mdrr
Curses

 — 14/10/2025 12:49
Whoa
Ily

 — 16/10/2025 21:46
C young Sheldon ouuu"""

merges = tokenize(text)

patterns = re.compile(r"""'(?i:[sdmt]|ll|ve|re)|[^\r\n\p{L}\p{N}]?+\p{L}++|\p{N}{1,3}+| ?[^\s\p{L}\p{N}]++[\r\n]*+|\s++$|\s*[\r\n]|\s+(?!\S)|\s""")

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

print(re.findall(patterns, decode(truc)))