#include "symbol_extractor/Extractor.h"
#include "symbol_extractor/InfoWriter.h"

#include <exception>
#include <filesystem>
#include <iostream>
#include <string>
#include <vector>

namespace {

constexpr const char* kVersion = "0.1.0";

enum class ExitCode {
    Success = 0,
    ExtractionFailed = 1,
    UsageError = 2,
};

struct Options {
    bool help = false;
    bool version = false;
    std::filesystem::path module_path;
    std::filesystem::path pdb_path;
    std::filesystem::path output_dir;
};

void print_usage(std::ostream& stream)
{
    stream
        << "symbol-extractor " << kVersion << "\n"
        << "\n"
        << "Usage:\n"
        << "  symbol-extractor --module <path> --output-dir <dir>\n"
        << "  symbol-extractor --module <path> --pdb <file.pdb> --output-dir <dir>\n"
        << "  symbol-extractor --help\n"
        << "  symbol-extractor --version\n"
        << "\n"
        << "Writes .info files using this schema:\n"
        << "  function_name<TAB>module_name<TAB>source_file<TAB>address_offset\n";
}

bool requires_value(const std::vector<std::string>& args, std::size_t index, const char* option)
{
    if (index + 1 < args.size()) {
        return true;
    }

    std::cerr << "Missing value for " << option << "\n";
    return false;
}

bool parse_args(int argc, char** argv, Options& options)
{
    const std::vector<std::string> args(argv + 1, argv + argc);

    for (std::size_t i = 0; i < args.size(); ++i) {
        const auto& arg = args[i];

        if (arg == "--help" || arg == "-h") {
            options.help = true;
        } else if (arg == "--version") {
            options.version = true;
        } else if (arg == "--module") {
            if (!requires_value(args, i, "--module")) {
                return false;
            }
            options.module_path = args[++i];
        } else if (arg == "--pdb") {
            if (!requires_value(args, i, "--pdb")) {
                return false;
            }
            options.pdb_path = args[++i];
        } else if (arg == "--output-dir") {
            if (!requires_value(args, i, "--output-dir")) {
                return false;
            }
            options.output_dir = args[++i];
        } else {
            std::cerr << "Unknown argument: " << arg << "\n";
            return false;
        }
    }

    return true;
}

bool validate_required_options(const Options& options)
{
    if (options.module_path.empty() || options.output_dir.empty()) {
        std::cerr << "Both --module and --output-dir are required.\n";
        return false;
    }

    if (!std::filesystem::exists(options.module_path)) {
        std::cerr << "Module does not exist: " << options.module_path << "\n";
        return false;
    }

    if (!std::filesystem::is_regular_file(options.module_path)) {
        std::cerr << "Module is not a regular file: " << options.module_path << "\n";
        return false;
    }

    if (!options.pdb_path.empty()) {
        if (!std::filesystem::exists(options.pdb_path)) {
            std::cerr << "PDB does not exist: " << options.pdb_path << "\n";
            return false;
        }

        if (!std::filesystem::is_regular_file(options.pdb_path)) {
            std::cerr << "PDB is not a regular file: " << options.pdb_path << "\n";
            return false;
        }
    }

    return true;
}

} // namespace

int main(int argc, char** argv)
{
    Options options;
    if (!parse_args(argc, argv, options)) {
        print_usage(std::cerr);
        return static_cast<int>(ExitCode::UsageError);
    }

    if (options.help) {
        print_usage(std::cout);
        return static_cast<int>(ExitCode::Success);
    }

    if (options.version) {
        std::cout << "symbol-extractor " << kVersion << "\n";
        return static_cast<int>(ExitCode::Success);
    }

    if (!validate_required_options(options)) {
        print_usage(std::cerr);
        return static_cast<int>(ExitCode::UsageError);
    }

    try {
        symbol_extractor::DiagnosticSink diagnostics;
        const symbol_extractor::Extractor extractor(symbol_extractor::create_default_backends());
        symbol_extractor::ExtractionOptions extraction_options;
        extraction_options.module_path = options.module_path;
        if (!options.pdb_path.empty()) {
            extraction_options.pdb_path = options.pdb_path;
        }

        const auto result = extractor.extract(extraction_options, diagnostics);

        diagnostics.print_to(std::cerr);
        if (diagnostics.has_errors()) {
            return static_cast<int>(ExitCode::ExtractionFailed);
        }

        symbol_extractor::InfoWriter writer;
        writer.write(result.functions, options.output_dir);
    } catch (const std::exception& ex) {
        std::cerr << "error: " << ex.what() << "\n";
        return static_cast<int>(ExitCode::ExtractionFailed);
    }

    return static_cast<int>(ExitCode::Success);
}
