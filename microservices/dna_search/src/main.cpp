#include <grpcpp/grpcpp.h>

#include <cstdlib>
#include <iostream>
#include <memory>
#include <string>

#include "server.h"

int main(int argc, char** argv) {
    const char* env_port = std::getenv("GRPC_PORT");
    const std::string port = env_port ? env_port : "50051";
    const std::string address = "0.0.0.0:" + port;

    grpc::ServerBuilder builder;
    builder.AddListeningPort(address, grpc::InsecureServerCredentials());
    builder.SetMaxReceiveMessageSize(200 * 1024 * 1024);  // 200MB
    builder.SetMaxSendMessageSize(200 * 1024 * 1024);     // 200MB

    dna::DnaSearchServiceImpl service;
    builder.RegisterService(&service);

    std::unique_ptr<grpc::Server> server(builder.BuildAndStart());
    if (!server) {
        std::cerr << "Failed to start gRPC server on " << address << std::endl;
        return 1;
    }

    std::cout << "DNA Search gRPC server listening on " << address << std::endl;
    server->Wait();
    return 0;
}
