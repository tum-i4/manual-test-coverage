#pragma once

#include <iosfwd>
#include <string>
#include <vector>

namespace symbol_extractor {

enum class DiagnosticLevel {
    Warning,
    Error,
};

struct Diagnostic {
    DiagnosticLevel level;
    std::string message;
};

class DiagnosticSink {
public:
    void warning(std::string message);
    void error(std::string message);

    [[nodiscard]] bool has_errors() const;
    [[nodiscard]] const std::vector<Diagnostic>& diagnostics() const;

    void print_to(std::ostream& stream) const;

private:
    std::vector<Diagnostic> diagnostics_;
};

} // namespace symbol_extractor
