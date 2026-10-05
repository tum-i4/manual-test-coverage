#include "symbol_extractor/InfoWriter.h"

#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

std::string read_file(const std::filesystem::path& path)
{
    std::ifstream stream(path);
    if (!stream) {
        throw std::runtime_error("Unable to read file: " + path.string());
    }

    std::ostringstream buffer;
    buffer << stream.rdbuf();
    return buffer.str();
}

void assert_equal(const std::string& actual, const std::string& expected)
{
    if (actual == expected) {
        return;
    }

    std::cerr
        << "Unexpected file content.\n"
        << "Expected:\n"
        << expected
        << "Actual:\n"
        << actual;
    throw std::runtime_error("File content mismatch");
}

void assert_throws_for_invalid_function(const std::filesystem::path& output_dir)
{
    const symbol_extractor::InfoWriter writer;
    const std::vector<symbol_extractor::FunctionInfo> invalid_function_name = {
        {"invalid\tname", "demo.exe", "src/demo.cpp", 16},
    };
    const std::vector<symbol_extractor::FunctionInfo> invalid_module_name = {
        {"func", "../demo.exe", "src/demo.cpp", 16},
    };

    try {
        writer.write(invalid_function_name, output_dir);
    } catch (const std::runtime_error&) {
        try {
            writer.write(invalid_module_name, output_dir);
        } catch (const std::runtime_error&) {
            return;
        }

        throw std::runtime_error("Expected writer to reject invalid module names");
    }

    throw std::runtime_error("Expected writer to reject invalid function fields");
}

} // namespace

int main(int argc, char** argv)
{
    if (argc != 2) {
        std::cerr << "Usage: symbol-extractor-writer-test <output-dir>\n";
        return 2;
    }

    const std::filesystem::path output_dir(argv[1]);
    std::filesystem::remove_all(output_dir);

    try {
        const symbol_extractor::InfoWriter writer;
        const std::vector<symbol_extractor::FunctionInfo> functions = {
            {"func_a", "demo.exe", "src/demo.cpp", 16},
            {"func_b", "demo.exe", "src/demo.cpp", 32},
            {"lib_func", "helper.dll", "src/helper.cpp", 48},
        };

        writer.write(functions, output_dir);

        assert_equal(
            read_file(output_dir / "demo.exe.info"),
            "func_a\tdemo.exe\tsrc/demo.cpp\t16\n"
            "func_b\tdemo.exe\tsrc/demo.cpp\t32\n"
        );
        assert_equal(
            read_file(output_dir / "helper.dll.info"),
            "lib_func\thelper.dll\tsrc/helper.cpp\t48\n"
        );

        assert_throws_for_invalid_function(output_dir / "invalid-output");
    } catch (const std::exception& ex) {
        std::cerr << "error: " << ex.what() << "\n";
        return 1;
    }

    return 0;
}
