#pragma once

#include <grpcpp/grpcpp.h>

#include "dna_search.grpc.pb.h"

namespace dna {

class DnaSearchServiceImpl final : public DnaSearch::Service {
public:
    grpc::Status Search(grpc::ServerContext* context,
                        const SearchRequest* request,
                        SearchResponse* response) override;

private:
    void FillMatches(const std::string& sequence,
                     const std::string& pattern,
                     bool allow_overlapping,
                     SearchResponse* response);
};

}  // namespace dna
