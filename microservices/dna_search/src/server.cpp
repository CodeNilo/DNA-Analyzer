#include "server.h"

#include <chrono>
#include <string>
#include <vector>

#include "algorithms/kmp.h"

namespace dna {

grpc::Status DnaSearchServiceImpl::Search(grpc::ServerContext* /*context*/,
                                          const SearchRequest* request,
                                          SearchResponse* response) {
    if (!request || !response) {
        return grpc::Status(grpc::StatusCode::INVALID_ARGUMENT, "Invalid request");
    }

    const std::string sequence = request->sequence();
    const std::string pattern = request->pattern();
    const bool allow_overlapping = request->allow_overlapping();

    if (pattern.empty() || sequence.empty()) {
        return grpc::Status(grpc::StatusCode::INVALID_ARGUMENT, "Sequence and pattern cannot be empty");
    }

    const auto start = std::chrono::steady_clock::now();
    FillMatches(sequence, pattern, allow_overlapping, response);
    const auto end = std::chrono::steady_clock::now();
    const auto elapsed_ms = std::chrono::duration_cast<std::chrono::microseconds>(end - start).count() / 1000.0;

    response->set_total_matches(response->matches_size());
    response->set_search_time_ms(elapsed_ms);
    response->set_algorithm_used("KMP");

    return grpc::Status::OK;
}

void DnaSearchServiceImpl::FillMatches(const std::string& sequence,
                                       const std::string& pattern,
                                       bool allow_overlapping,
                                       SearchResponse* response) {
    const auto positions = KMPSearch::Find(sequence, pattern, allow_overlapping);
    const int context_window = 10;

    for (const auto pos : positions) {
        auto* match = response->add_matches();
        match->set_position(static_cast<int64_t>(pos));

        const auto start_ctx = (pos > static_cast<size_t>(context_window))
                                   ? pos - context_window
                                   : 0;
        const auto end_ctx = std::min(sequence.size(), pos + pattern.size() + context_window);

        const auto before = sequence.substr(start_ctx, pos - start_ctx);
        const auto after = sequence.substr(pos + pattern.size(), end_ctx - (pos + pattern.size()));

        match->set_context_before(before);
        match->set_context_after(after);
    }
}

}  // namespace dna
