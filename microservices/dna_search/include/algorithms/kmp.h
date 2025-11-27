#pragma once

#include <string>
#include <vector>

namespace dna {

// KMP con soporte de solapamiento configurado por el caller (control en el loop externo).
class KMPSearch {
public:
    static std::vector<size_t> Find(const std::string& text, const std::string& pattern, bool allow_overlapping);

private:
    static std::vector<int> BuildLps(const std::string& pattern);
};

}  // namespace dna
