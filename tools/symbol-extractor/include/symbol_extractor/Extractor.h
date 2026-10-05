#pragma once

#include "symbol_extractor/DiagnosticSink.h"

#include <cstdint>
#include <filesystem>
#include <memory>
#include <optional>
#include <string>
#include <vector>

namespace symbol_extractor {

struct FunctionInfo {
    std::string name;
    std::string module_name;
    std::string source_file;
    std::uint64_t address_offset;
};

struct ExtractionResult {
    std::vector<FunctionInfo> functions;
};

struct ExtractionOptions {
    std::filesystem::path module_path;
    std::optional<std::filesystem::path> pdb_path;
};

class ExtractorBackend {
public:
    virtual ~ExtractorBackend() = default;

    [[nodiscard]] virtual std::string name() const = 0;
    [[nodiscard]] virtual bool can_handle(
        const ExtractionOptions& options,
        DiagnosticSink& diagnostics
    ) const = 0;
    [[nodiscard]] virtual ExtractionResult extract(
        const ExtractionOptions& options,
        DiagnosticSink& diagnostics
    ) const = 0;
};

using BackendList = std::vector<std::unique_ptr<ExtractorBackend>>;

class Extractor {
public:
    explicit Extractor(BackendList backends);

    [[nodiscard]] ExtractionResult extract(
        const ExtractionOptions& options,
        DiagnosticSink& diagnostics
    ) const;

private:
    BackendList backends_;
};

BackendList create_default_backends();

} // namespace symbol_extractor
