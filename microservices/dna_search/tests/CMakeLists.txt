cmake_minimum_required(VERSION 3.15)
project(dna_search_tests)

# C++ Standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find Google Test
find_package(GTest REQUIRED)
include_directories(${GTEST_INCLUDE_DIRS})

# Include directories
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../include)

# Test executable
add_executable(test_kmp
    test_kmp.cpp
    ../src/algorithms/kmp.cpp
)

# Link Google Test
target_link_libraries(test_kmp
    ${GTEST_LIBRARIES}
    pthread
)

# Enable testing
enable_testing()

# Add test
add_test(NAME KMPTests COMMAND test_kmp)

# Optional: Add verbose output
add_custom_target(check
    COMMAND ${CMAKE_CTEST_COMMAND} --verbose
    DEPENDS test_kmp
)
