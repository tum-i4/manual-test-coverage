#include "symbol_extractor/InfoWriter.h"

#include <fstream>
#include <map>
#include <stdexcept>
#include <string>

namespace symbol_extractor {
namespace {

constexpr char kSeparator = '\t';
constexpr const char* kInfoExtension = ".info";

bool contains_invalid_info_character(const std::string& value)
{
    return value.find('\t') != std::string::npos
        || value.find('\n') != std::string::npos
        || value.find('\r') != std::string::npos;
}

void validate_field(const std::string& field_name, const std::string& value)
{
    if (value.empty()) {
        throw std::runtime_error(field_name + " must not be empty");
    }

    if (contains_invalid_info_character(value)) {
        throw std::runtime_error(field_name + " contains a character unsupported by .info files");
    }
}

void validate_function_info(const FunctionInfo& function)
{
    validate_field("Function name", function.name);
    validate_field("Module name", function.module_name);
    if (function.module_name.find('/') != std::string::npos
        || function.module_name.find('\\') != std::string::npos) {
        throw std::runtime_error("Module name must be a file name, not a path");
    }
    validate_field("Source file", function.source_file);
}

} // namespace

void InfoWriter::write(
    const std::vector<FunctionInfo>& functions,
    const std::filesystem::path& output_dir
) const
{
    std::map<std::string, std::vector<FunctionInfo>> functions_by_module;
    for (const auto& function : functions) {
        validate_function_info(function);
        functions_by_module[function.module_name].push_back(function);
    }

    std::filesystem::create_directories(output_dir);

    for (const auto& [module_name, module_functions] : functions_by_module) {
        const auto output_file = output_dir / (module_name + kInfoExtension);
        std::ofstream stream(output_file, std::ios::out | std::ios::trunc);
        if (!stream) {
            throw std::runtime_error("Unable to open output file: " + output_file.string());
        }

        for (const auto& function : module_functions) {
            stream
                << function.name << kSeparator
                << function.module_name << kSeparator
                << function.source_file << kSeparator
                << function.address_offset << "\n";
        }
    }
}

} // namespace symbol_extractor
