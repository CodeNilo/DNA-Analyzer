/**
 * Pruebas unitarias para el algoritmo KMP
 *
 * Usa Google Test framework
 *
 * Para compilar y ejecutar:
 *   mkdir build && cd build
 *   cmake ..
 *   make
 *   ./test_kmp
 */

#include <gtest/gtest.h>
#include <vector>
#include <string>
#include "../include/algorithms/kmp.h"

// Clase base para tests de KMP
class KMPTest : public ::testing::Test {
protected:
    void SetUp() override {
        // Setup común si es necesario
    }

    void TearDown() override {
        // Cleanup común si es necesario
    }
};

// ============================================================================
// PRUEBAS DE LA TABLA LPS (Longest Proper Prefix Suffix)
// ============================================================================

TEST_F(KMPTest, ComputeLPSSimplePattern) {
    std::string pattern = "AAAA";
    std::vector<int> lps = computeLPS(pattern);

    ASSERT_EQ(lps.size(), 4);
    EXPECT_EQ(lps[0], 0);  // A -> 0
    EXPECT_EQ(lps[1], 1);  // AA -> 1
    EXPECT_EQ(lps[2], 2);  // AAA -> 2
    EXPECT_EQ(lps[3], 3);  // AAAA -> 3
}

TEST_F(KMPTest, ComputeLPSNoRepeating) {
    std::string pattern = "ABCD";
    std::vector<int> lps = computeLPS(pattern);

    ASSERT_EQ(lps.size(), 4);
    EXPECT_EQ(lps[0], 0);
    EXPECT_EQ(lps[1], 0);
    EXPECT_EQ(lps[2], 0);
    EXPECT_EQ(lps[3], 0);
}

TEST_F(KMPTest, ComputeLPSMixedPattern) {
    std::string pattern = "ABABC";
    std::vector<int> lps = computeLPS(pattern);

    ASSERT_EQ(lps.size(), 5);
    EXPECT_EQ(lps[0], 0);  // A
    EXPECT_EQ(lps[1], 0);  // AB
    EXPECT_EQ(lps[2], 1);  // ABA
    EXPECT_EQ(lps[3], 2);  // ABAB
    EXPECT_EQ(lps[4], 0);  // ABABC
}

TEST_F(KMPTest, ComputeLPSSingleCharacter) {
    std::string pattern = "A";
    std::vector<int> lps = computeLPS(pattern);

    ASSERT_EQ(lps.size(), 1);
    EXPECT_EQ(lps[0], 0);
}

TEST_F(KMPTest, ComputeLPSEmptyPattern) {
    std::string pattern = "";
    std::vector<int> lps = computeLPS(pattern);

    EXPECT_EQ(lps.size(), 0);
}

// ============================================================================
// PRUEBAS DE BÚSQUEDA BÁSICA
// ============================================================================

TEST_F(KMPTest, SearchSimpleMatch) {
    std::string text = "ATCGATCG";
    std::string pattern = "TCG";

    std::vector<int> matches = kmpSearch(text, pattern, false);

    ASSERT_EQ(matches.size(), 2);
    EXPECT_EQ(matches[0], 1);
    EXPECT_EQ(matches[1], 5);
}

TEST_F(KMPTest, SearchNoMatches) {
    std::string text = "AAAA";
    std::string pattern = "TTT";

    std::vector<int> matches = kmpSearch(text, pattern, false);

    EXPECT_EQ(matches.size(), 0);
}

TEST_F(KMPTest, SearchSingleMatch) {
    std::string text = "ATCGATCG";
    std::string pattern = "ATCGATCG";

    std::vector<int> matches = kmpSearch(text, pattern, false);

    ASSERT_EQ(matches.size(), 1);
    EXPECT_EQ(matches[0], 0);
}

TEST_F(KMPTest, SearchPatternAtStart) {
    std::string text = "ATCGATCG";
    std::string pattern = "ATC";

    std::vector<int> matches = kmpSearch(text, pattern, false);

    ASSERT_GE(matches.size(), 1);
    EXPECT_EQ(matches[0], 0);
}

TEST_F(KMPTest, SearchPatternAtEnd) {
    std::string text = "ATCGATCG";
    std::string pattern = "TCG";

    std::vector<int> matches = kmpSearch(text, pattern, false);

    // Debe encontrar TCG en posición 5 (al final)
    EXPECT_TRUE(std::find(matches.begin(), matches.end(), 5) != matches.end());
}

TEST_F(KMPTest, SearchPatternLongerThanText) {
    std::string text = "AT";
    std::string pattern = "ATCGATCG";

    std::vector<int> matches = kmpSearch(text, pattern, false);

    EXPECT_EQ(matches.size(), 0);
}

// ============================================================================
// PRUEBAS DE BÚSQUEDA CON SOLAPAMIENTO
// ============================================================================

TEST_F(KMPTest, SearchOverlappingMatches) {
    std::string text = "AAAA";
    std::string pattern = "AA";

    std::vector<int> matches = kmpSearch(text, pattern, true);  // Overlapping

    ASSERT_EQ(matches.size(), 3);
    EXPECT_EQ(matches[0], 0);
    EXPECT_EQ(matches[1], 1);
    EXPECT_EQ(matches[2], 2);
}

TEST_F(KMPTest, SearchNonOverlappingMatches) {
    std::string text = "AAAA";
    std::string pattern = "AA";

    std::vector<int> matches = kmpSearch(text, pattern, false);  // Non-overlapping

    ASSERT_EQ(matches.size(), 2);
    EXPECT_EQ(matches[0], 0);
    EXPECT_EQ(matches[1], 2);
}

TEST_F(KMPTest, SearchOverlappingComplex) {
    std::string text = "ABABABAB";
    std::string pattern = "ABAB";

    std::vector<int> matches = kmpSearch(text, pattern, true);

    // Debe encontrar en 0, 2, 4
    ASSERT_EQ(matches.size(), 3);
    EXPECT_EQ(matches[0], 0);
    EXPECT_EQ(matches[1], 2);
    EXPECT_EQ(matches[2], 4);
}

TEST_F(KMPTest, SearchNonOverlappingComplex) {
    std::string text = "ABABABAB";
    std::string pattern = "ABAB";

    std::vector<int> matches = kmpSearch(text, pattern, false);

    // Debe encontrar en 0, 4 (sin solapamiento)
    ASSERT_EQ(matches.size(), 2);
    EXPECT_EQ(matches[0], 0);
    EXPECT_EQ(matches[1], 4);
}

// ============================================================================
// PRUEBAS CON SECUENCIAS DE ADN
// ============================================================================

TEST_F(KMPTest, SearchDNAStartCodon) {
    std::string sequence = "ATGATGATGATG";
    std::string codon = "ATG";

    std::vector<int> matches = kmpSearch(sequence, codon, true);

    ASSERT_EQ(matches.size(), 4);
    EXPECT_EQ(matches[0], 0);
    EXPECT_EQ(matches[1], 3);
    EXPECT_EQ(matches[2], 6);
    EXPECT_EQ(matches[3], 9);
}

TEST_F(KMPTest, SearchDNAStopCodon) {
    std::string sequence = "ATGTAATGATAG";
    std::string stop_codon = "TAA";

    std::vector<int> matches = kmpSearch(sequence, stop_codon, false);

    ASSERT_EQ(matches.size(), 1);
    EXPECT_EQ(matches[0], 3);
}

TEST_F(KMPTest, SearchDNAWithN) {
    std::string sequence = "ATCGNATCG";
    std::string pattern = "CGN";

    std::vector<int> matches = kmpSearch(sequence, pattern, false);

    ASSERT_EQ(matches.size(), 1);
    EXPECT_EQ(matches[0], 3);
}

// ============================================================================
// PRUEBAS DE RENDIMIENTO Y CASOS EXTREMOS
// ============================================================================

TEST_F(KMPTest, SearchLargeSequence) {
    // Secuencia de 10,000 bp
    std::string sequence(10000, 'A');
    sequence[5000] = 'T';
    sequence[5001] = 'C';
    sequence[5002] = 'G';

    std::string pattern = "TCG";

    std::vector<int> matches = kmpSearch(sequence, pattern, false);

    ASSERT_EQ(matches.size(), 1);
    EXPECT_EQ(matches[0], 5000);
}

TEST_F(KMPTest, SearchRepeatingPattern) {
    std::string text = "AAAAAAAAAA";  // 10 As
    std::string pattern = "A";

    std::vector<int> matches = kmpSearch(text, pattern, false);

    EXPECT_EQ(matches.size(), 10);
}

TEST_F(KMPTest, SearchEmptyText) {
    std::string text = "";
    std::string pattern = "ATG";

    std::vector<int> matches = kmpSearch(text, pattern, false);

    EXPECT_EQ(matches.size(), 0);
}

TEST_F(KMPTest, SearchEmptyPattern) {
    std::string text = "ATCG";
    std::string pattern = "";

    std::vector<int> matches = kmpSearch(text, pattern, false);

    EXPECT_EQ(matches.size(), 0);
}

TEST_F(KMPTest, SearchSingleCharacterText) {
    std::string text = "A";
    std::string pattern = "A";

    std::vector<int> matches = kmpSearch(text, pattern, false);

    ASSERT_EQ(matches.size(), 1);
    EXPECT_EQ(matches[0], 0);
}

TEST_F(KMPTest, SearchVeryLongPattern) {
    std::string pattern = std::string(1000, 'A');
    std::string text = std::string(2000, 'A');

    std::vector<int> matches = kmpSearch(text, pattern, false);

    // Debe encontrar el patrón una vez (sin solapamiento)
    ASSERT_GE(matches.size(), 1);
    EXPECT_EQ(matches[0], 0);
}

// ============================================================================
// PRUEBAS DE CORRECCIÓN DEL ALGORITMO
// ============================================================================

TEST_F(KMPTest, VerifyKMPMatchesNaiveSearch) {
    std::string text = "ATCGATCGATCG";
    std::string pattern = "TCG";

    // Búsqueda KMP
    std::vector<int> kmp_matches = kmpSearch(text, pattern, true);

    // Búsqueda naive (para verificar)
    std::vector<int> naive_matches;
    for (size_t i = 0; i <= text.length() - pattern.length(); ++i) {
        if (text.substr(i, pattern.length()) == pattern) {
            naive_matches.push_back(i);
        }
    }

    EXPECT_EQ(kmp_matches, naive_matches);
}

TEST_F(KMPTest, VerifyKMPWithMultiplePatterns) {
    std::string text = "ATCGATCGATCGATCG";
    std::vector<std::string> patterns = {"AT", "CG", "ATG", "GATC"};

    for (const auto& pattern : patterns) {
        std::vector<int> kmp_matches = kmpSearch(text, pattern, true);

        // Verificar con búsqueda naive
        std::vector<int> naive_matches;
        for (size_t i = 0; i <= text.length() - pattern.length(); ++i) {
            if (text.substr(i, pattern.length()) == pattern) {
                naive_matches.push_back(i);
            }
        }

        EXPECT_EQ(kmp_matches, naive_matches)
            << "Failed for pattern: " << pattern;
    }
}

// ============================================================================
// MAIN
// ============================================================================

int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
