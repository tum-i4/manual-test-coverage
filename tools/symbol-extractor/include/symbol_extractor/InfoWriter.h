#pragma once

#include "symbol_extractor/Extractor.h"

#include <filesystem>
#include <vector>

namespace symbol_extractor {

class InfoWriter {
public:
    void write(
        const std::vector<FunctionInfo>& functions,
        const std::filesystem::path& output_dir
    ) const;
};

} // namespace symbol_extractor
