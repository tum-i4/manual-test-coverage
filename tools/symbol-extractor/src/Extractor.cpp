#include "symbol_extractor/Extractor.h"

#if SYMBOL_EXTRACTOR_HAS_LLVM_PDB
#include "symbol_extractor/backends/PdbExtractorBackend.h"
#endif

#include <ostream>
#include <utility>

namespace symbol_extractor {

void DiagnosticSink::warning(std::string message)
{
    diagnostics_.push_back({DiagnosticLevel::Warning, std::move(message)});
}

void DiagnosticSink::error(std::string message)
{
    diagnostics_.push_back({DiagnosticLevel::Error, std::move(message)});
}

bool DiagnosticSink::has_errors() const
{
    for (const auto& diagnostic : diagnostics_) {
        if (diagnostic.level == DiagnosticLevel::Error) {
            return true;
        }
    }
    return false;
}

const std::vector<Diagnostic>& DiagnosticSink::diagnostics() const
{
    return diagnostics_;
}

void DiagnosticSink::print_to(std::ostream& stream) const
{
    for (const auto& diagnostic : diagnostics_) {
        stream
            << (diagnostic.level == DiagnosticLevel::Error ? "error" : "warning")
            << ": "
            << diagnostic.message
            << "\n";
    }
}

Extractor::Extractor(BackendList backends)
    : backends_(std::move(backends))
{
}

ExtractionResult Extractor::extract(
    const ExtractionOptions& options,
    DiagnosticSink& diagnostics
) const
{
    for (const auto& backend : backends_) {
        if (!backend->can_handle(options, diagnostics)) {
            continue;
        }

        return backend->extract(options, diagnostics);
    }

    diagnostics.error("No symbol backend can read: " + options.module_path.string());
    return {};
}

BackendList create_default_backends()
{
    BackendList backends;
#if SYMBOL_EXTRACTOR_HAS_LLVM_PDB
    backends.push_back(create_pdb_extractor_backend());
#endif
    return backends;
}

} // namespace symbol_extractor
