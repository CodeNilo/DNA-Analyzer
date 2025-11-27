#include "algorithms/kmp.h"

#include <algorithm>

namespace dna {

std::vector<int> KMPSearch::BuildLps(const std::string& pattern) {
    std::vector<int> lps(pattern.size(), 0);
    int len = 0;
    for (size_t i = 1; i < pattern.size();) {
        if (pattern[i] == pattern[len]) {
            lps[i++] = ++len;
        } else if (len != 0) {
            len = lps[len - 1];
        } else {
            lps[i++] = 0;
        }
    }
    return lps;
}

std::vector<size_t> KMPSearch::Find(const std::string& text, const std::string& pattern, bool allow_overlapping) {
    std::vector<size_t> positions;
    if (pattern.empty() || text.empty() || pattern.size() > text.size()) {
        return positions;
    }

    const auto lps = BuildLps(pattern);
    size_t i = 0;  // text index
    size_t j = 0;  // pattern index
    while (i < text.size()) {
        if (pattern[j] == text[i]) {
            i++;
            j++;
        }

        if (j == pattern.size()) {
            positions.push_back(i - j);
            // Control de solapamiento: avanzar solo 1 o saltar tamaño del patrón
            j = allow_overlapping ? lps[j - 1] : 0;
            if (!allow_overlapping) {
                i = i - j;  // reposicionar si reseteamos j
            }
        } else if (i < text.size() && pattern[j] != text[i]) {
            if (j != 0) {
                j = lps[j - 1];
            } else {
                i++;
            }
        }
    }
    return positions;
}

}  // namespace dna
