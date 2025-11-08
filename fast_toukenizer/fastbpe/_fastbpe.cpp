// fastbpe.cpp
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <unordered_map>
#include <vector>
#include <string>
#include <climits>

namespace py = pybind11;

struct PairHash {
    std::size_t operator()(const std::pair<int,int>& p) const noexcept {
        // simple mix
        return ((std::size_t)p.first) ^ (((std::size_t)p.second) << 32);
    }
};

class FastBPE {
public:
    FastBPE(size_t vocab_size = 8192) : vocab_size(vocab_size) {}

    // get_stats_for_encode: compte les paires dans une séquence d'ids
    std::unordered_map<std::pair<int,int>, int, PairHash>
    get_stats_for_encode(const std::vector<int>& ids) const {
        std::unordered_map<std::pair<int,int>, int, PairHash> counts;
        if (ids.size() < 2) return counts;
        for (size_t i = 0; i + 1 < ids.size(); ++i) {
            counts[{ids[i], ids[i+1]}]++;
        }
        return counts;
    }

    // get_stats sur plusieurs segments (list of list) — utile pour tokenize() training
    std::unordered_map<std::pair<int,int>, int, PairHash>
    get_stats(const std::vector<std::vector<int>>& segments) const {
        std::unordered_map<std::pair<int,int>, int, PairHash> counts;
        for (const auto& seg : segments) {
            if (seg.size() < 2) continue;
            for (size_t i = 0; i + 1 < seg.size(); ++i) {
                counts[{seg[i], seg[i+1]}]++;
            }
        }
        return counts;
    }

    // merge_for_encode: merge une paire dans une séquence d'ids
    std::vector<int> merge_for_encode(const std::vector<int>& ids,
                                      const std::pair<int,int>& pair,
                                      int idx) const {
        std::vector<int> out;
        out.reserve(ids.size());
        size_t i = 0;
        while (i < ids.size()) {
            if (i + 1 < ids.size() && ids[i] == pair.first && ids[i+1] == pair.second) {
                out.push_back(idx);
                i += 2;
            } else {
                out.push_back(ids[i]);
                ++i;
            }
        }
        return out;
    }

    // merge (appliquée sur une liste de segments) : renvoie une nouvelle liste de segments
    std::vector<std::vector<int>>
    merge_segments(const std::vector<std::vector<int>>& segments,
                   const std::pair<int,int>& pair,
                   int idx) const {
        std::vector<std::vector<int>> out;
        out.reserve(segments.size());
        for (const auto& seg : segments) {
            std::vector<int> newseg;
            newseg.reserve(seg.size());
            size_t i = 0;
            while (i < seg.size()) {
                if (i + 1 < seg.size() && seg[i] == pair.first && seg[i+1] == pair.second) {
                    newseg.push_back(idx);
                    i += 2;
                } else {
                    newseg.push_back(seg[i]);
                    ++i;
                }
            }
            out.push_back(std::move(newseg));
        }
        return out;
    }

    // encode: applique les merges (en regardant l'ordre défini par la map merges)
    // merges: map<pair, idx> -> on merge en choisissant la paire ayant le plus petit idx (priorité)
    std::vector<int> encode(const std::vector<int>& tokens,
                             const std::unordered_map<std::pair<int,int>, int, PairHash>& merges) const {
        std::vector<int> current = tokens;
        while (current.size() >= 2) {
            // calcule stats
            auto stats = get_stats_for_encode(current);
            // détermine la paire "applicable" la plus prioritaire (lowest idx)
            std::pair<int,int> best_pair = {-1,-1};
            int best_idx = INT_MAX;
            for (auto &kv : stats) {
                auto it = merges.find(kv.first);
                if (it != merges.end() && it->second < best_idx) {
                    best_idx = it->second;
                    best_pair = kv.first;
                }
            }
            if (best_pair.first == -1) break; // aucun merge applicable
            current = merge_for_encode(current, best_pair, best_idx);
        }
        return current;
    }

    // decode : reconstruit une string concaténée depuis un vocab map<int, string>
    std::string decode(const std::vector<int>& ids,
                       const std::unordered_map<int, std::string>& vocab) const {
        std::string out;
        out.reserve(ids.size() * 2);
        for (int id : ids) {
            auto it = vocab.find(id);
            if (it != vocab.end()) out += it->second;
        }
        return out;
    }

private:
    size_t vocab_size;
};

PYBIND11_MODULE(_fastbpe, m) {
    py::class_<FastBPE>(m, "Tokenizer")
        .def(py::init<size_t>(), py::arg("vocab_size") = 8192)
        .def("get_stats_for_encode", &FastBPE::get_stats_for_encode)
        .def("get_stats", &FastBPE::get_stats)
        .def("merge_for_encode", &FastBPE::merge_for_encode)
        .def("merge_segments", &FastBPE::merge_segments)
        .def("encode", &FastBPE::encode)
        .def("decode", &FastBPE::decode);
}
