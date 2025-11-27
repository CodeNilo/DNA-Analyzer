cmake_minimum_required(VERSION 3.15)
project(dna_search_service CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Protobuf REQUIRED)
find_package(PkgConfig REQUIRED)
pkg_check_modules(GRPC REQUIRED grpc++)
find_program(GRPC_CPP_PLUGIN grpc_cpp_plugin)
if(NOT GRPC_CPP_PLUGIN)
    message(FATAL_ERROR "grpc_cpp_plugin not found")
endif()

set(PROTO_SRC ${CMAKE_CURRENT_SOURCE_DIR}/proto/dna_search.proto)
set(GENERATED_DIR ${CMAKE_CURRENT_BINARY_DIR}/generated)

file(MAKE_DIRECTORY ${GENERATED_DIR})

add_custom_command(
    OUTPUT ${GENERATED_DIR}/dna_search.pb.cc ${GENERATED_DIR}/dna_search.pb.h
           ${GENERATED_DIR}/dna_search.grpc.pb.cc ${GENERATED_DIR}/dna_search.grpc.pb.h
    COMMAND ${PROTOBUF_PROTOC_EXECUTABLE}
    ARGS --grpc_out=${GENERATED_DIR}
         --cpp_out=${GENERATED_DIR}
         --plugin=protoc-gen-grpc=${GRPC_CPP_PLUGIN}
         -I ${CMAKE_CURRENT_SOURCE_DIR}/proto
         ${PROTO_SRC}
    DEPENDS ${PROTO_SRC}
    VERBATIM)

add_library(dna_search_proto
    ${GENERATED_DIR}/dna_search.pb.cc
    ${GENERATED_DIR}/dna_search.grpc.pb.cc)

target_include_directories(dna_search_proto
    PUBLIC ${GENERATED_DIR} ${Protobuf_INCLUDE_DIRS} ${GRPC_INCLUDE_DIRS})

target_link_libraries(dna_search_proto
    PUBLIC ${Protobuf_LIBRARIES} ${GRPC_LIBRARIES})

add_library(dna_search_algos
    src/algorithms/kmp.cpp)

target_include_directories(dna_search_algos
    PUBLIC src ${GENERATED_DIR} ${CMAKE_CURRENT_SOURCE_DIR}/include ${Protobuf_INCLUDE_DIRS} ${GRPC_INCLUDE_DIRS})

add_executable(dna_search_server
    src/main.cpp
    src/server.cpp)

target_include_directories(dna_search_server
    PRIVATE src ${GENERATED_DIR} ${CMAKE_CURRENT_SOURCE_DIR}/include ${Protobuf_INCLUDE_DIRS} ${GRPC_INCLUDE_DIRS})

target_link_libraries(dna_search_server
    PRIVATE dna_search_proto
            dna_search_algos
            ${Protobuf_LIBRARIES}
            ${GRPC_LIBRARIES})
