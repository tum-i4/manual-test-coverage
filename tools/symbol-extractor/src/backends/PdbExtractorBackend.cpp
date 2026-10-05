#include "symbol_extractor/backends/PdbExtractorBackend.h"

#include "llvm/DebugInfo/CodeView/CodeView.h"
#include "llvm/DebugInfo/CodeView/DebugChecksumsSubsection.h"
#include "llvm/DebugInfo/CodeView/DebugLinesSubsection.h"
#include "llvm/DebugInfo/CodeView/GUID.h"
#include "llvm/DebugInfo/CodeView/SymbolDeserializer.h"
#include "llvm/DebugInfo/CodeView/SymbolRecord.h"
#include "llvm/DebugInfo/PDB/IPDBLineNumber.h"
#include "llvm/DebugInfo/PDB/IPDBSession.h"
#include "llvm/DebugInfo/PDB/IPDBSourceFile.h"
#include "llvm/DebugInfo/PDB/Native/DbiModuleList.h"
#include "llvm/DebugInfo/PDB/Native/DbiStream.h"
#include "llvm/DebugInfo/PDB/Native/ModuleDebugStream.h"
#include "llvm/DebugInfo/PDB/Native/NativeSession.h"
#include "llvm/DebugInfo/PDB/Native/PDBFile.h"
#include "llvm/DebugInfo/PDB/Native/PDBStringTable.h"
#include "llvm/DebugInfo/PDB/PDB.h"
#include "llvm/DebugInfo/PDB/PDBSymbolExe.h"
#include "llvm/Object/Binary.h"
#include "llvm/Object/COFF.h"
#include "llvm/Object/CVDebugRecord.h"
#include "llvm/Support/BinaryStreamReader.h"
#include "llvm/Support/Error.h"

#include <algorithm>
#include <cstring>
#include <filesystem>
#include <map>
#include <memory>
#include <optional>
#include <set>
#include <string>
#include <utility>
#include <vector>

namespace symbol_extractor {
namespace {

struct PdbReference {
    std::filesystem::path embedded_path;
    std::uint32_t age = 0;
    std::optional<llvm::codeview::GUID> guid;
};

struct LoadedCoffObject {
    std::unique_ptr<llvm::object::Binary> binary;
    std::unique_ptr<llvm::MemoryBuffer> memory_buffer;
    llvm::object::COFFObjectFile* coff = nullptr;
};

struct SourceLineRange {
    std::uint16_t segment = 0;
    std::uint32_t start_offset = 0;
    std::uint32_t end_offset = 0;
    std::string source_file;
};

class SourceLineIndex {
public:
    static SourceLineIndex build(
        llvm::pdb::NativeSession& session,
        const llvm::pdb::ModuleDebugStreamRef& module_stream,
        DiagnosticSink& diagnostics
    );

    [[nodiscard]] std::optional<std::string> find_source_file(
        const llvm::codeview::ProcSym& function
    ) const;

private:
    void add_range(SourceLineRange range);

    std::map<std::uint16_t, std::vector<SourceLineRange>> ranges_by_segment_;
};

std::string llvm_error_to_string(llvm::Error error)
{
    return llvm::toString(std::move(error));
}

std::optional<LoadedCoffObject> load_coff_object(
    const std::filesystem::path& module_path,
    DiagnosticSink* diagnostics
)
{
    auto binary = llvm::object::createBinary(module_path.string());
    if (!binary) {
        if (diagnostics != nullptr) {
            diagnostics->error("Unable to read module: " + llvm_error_to_string(binary.takeError()));
        } else {
            llvm::consumeError(binary.takeError());
        }
        return std::nullopt;
    }

    auto [owned_binary, memory_buffer] = binary->takeBinary();
    auto* coff = llvm::dyn_cast<llvm::object::COFFObjectFile>(owned_binary.get());
    if (coff == nullptr) {
        return std::nullopt;
    }

    return LoadedCoffObject{
        std::move(owned_binary),
        std::move(memory_buffer),
        coff,
    };
}

std::optional<PdbReference> read_pdb_reference(
    const llvm::object::COFFObjectFile& coff,
    DiagnosticSink& diagnostics
)
{
    const llvm::codeview::DebugInfo* debug_info = nullptr;
    llvm::StringRef pdb_file_name;

    if (auto error = coff.getDebugPDBInfo(debug_info, pdb_file_name)) {
        diagnostics.error("Unable to read PE CodeView debug information: " + llvm_error_to_string(std::move(error)));
        return std::nullopt;
    }

    if (debug_info == nullptr) {
        return std::nullopt;
    }

    const auto signature = static_cast<std::uint32_t>(debug_info->Signature.CVSignature);
    if (signature != llvm::OMF::Signature::PDB70) {
        diagnostics.warning("Only RSDS/PDB70 CodeView records can be validated");
        PdbReference reference;
        reference.embedded_path = pdb_file_name.str();
        return reference;
    }

    PdbReference reference;
    reference.embedded_path = pdb_file_name.str();
    reference.age = debug_info->PDB70.Age;

    llvm::codeview::GUID guid;
    std::memcpy(guid.Guid, debug_info->PDB70.Signature, sizeof(guid.Guid));
    reference.guid = guid;

    return reference;
}

std::optional<std::filesystem::path> resolve_pdb_path(
    const ExtractionOptions& options,
    const std::optional<PdbReference>& reference,
    DiagnosticSink& diagnostics
)
{
    if (options.pdb_path.has_value()) {
        return std::filesystem::absolute(*options.pdb_path);
    }

    if (!reference.has_value() || reference->embedded_path.empty()) {
        diagnostics.error("No PDB path is embedded in the module; pass --pdb explicitly");
        return std::nullopt;
    }

    const auto module_dir = options.module_path.parent_path();
    const auto& embedded_path = reference->embedded_path;

    if (embedded_path.is_absolute() && std::filesystem::exists(embedded_path)) {
        return embedded_path;
    }

    if (std::filesystem::exists(embedded_path)) {
        return std::filesystem::absolute(embedded_path);
    }

    const auto next_to_module = module_dir / embedded_path.filename();
    if (std::filesystem::exists(next_to_module)) {
        return std::filesystem::absolute(next_to_module);
    }

    const auto relative_to_module = module_dir / embedded_path;
    if (std::filesystem::exists(relative_to_module)) {
        return std::filesystem::absolute(relative_to_module);
    }

    diagnostics.error("Unable to resolve PDB path: " + embedded_path.string());
    return std::nullopt;
}

std::unique_ptr<llvm::pdb::IPDBSession> load_pdb_session(
    const std::filesystem::path& pdb_path,
    DiagnosticSink& diagnostics
)
{
    std::unique_ptr<llvm::pdb::IPDBSession> session;
    if (auto error = llvm::pdb::loadDataForPDB(
            llvm::pdb::PDB_ReaderType::Native,
            pdb_path.string(),
            session)) {
        diagnostics.error("Unable to read PDB: " + llvm_error_to_string(std::move(error)));
        return nullptr;
    }

    return session;
}

bool validate_identity(
    llvm::pdb::IPDBSession& session,
    const std::optional<PdbReference>& reference,
    DiagnosticSink& diagnostics
)
{
    if (!reference.has_value()) {
        diagnostics.warning("PDB identity could not be validated because the module has no CodeView PDB reference");
        return true;
    }

    auto global_scope = session.getGlobalScope();
    if (!global_scope) {
        diagnostics.error("PDB does not expose a global scope");
        return false;
    }

    if (reference->age != 0 && global_scope->getAge() != reference->age) {
        diagnostics.error("PDB age does not match the module CodeView record");
        return false;
    }

    if (reference->guid.has_value() && global_scope->getGuid() != *reference->guid) {
        diagnostics.error("PDB GUID does not match the module CodeView record");
        return false;
    }

    return true;
}

bool is_function_symbol(llvm::codeview::SymbolKind kind)
{
    switch (kind) {
    case llvm::codeview::SymbolKind::S_GPROC32:
    case llvm::codeview::SymbolKind::S_LPROC32:
    case llvm::codeview::SymbolKind::S_GPROC32_ID:
    case llvm::codeview::SymbolKind::S_LPROC32_ID:
    case llvm::codeview::SymbolKind::S_LPROC32_DPC:
    case llvm::codeview::SymbolKind::S_LPROC32_DPC_ID:
        return true;
    default:
        return false;
    }
}

std::string source_file_for_proc_sym(
    llvm::pdb::NativeSession& session,
    const llvm::codeview::ProcSym& function,
    std::uint32_t rva
)
{
    auto line_numbers = session.findLineNumbersByRVA(rva, function.CodeSize);
    if (!line_numbers) {
        return {};
    }

    std::unique_ptr<llvm::pdb::IPDBLineNumber> line_number;
    while ((line_number = line_numbers->getNext())) {
        if (!line_number->isStatement()) {
            continue;
        }

        auto source_file = session.getSourceFileById(line_number->getSourceFileId());
        if (source_file) {
            return source_file->getFileName();
        }
    }

    line_numbers->reset();
    line_number = line_numbers->getNext();
    if (!line_number) {
        return {};
    }

    auto source_file = session.getSourceFileById(line_number->getSourceFileId());
    if (!source_file) {
        return {};
    }

    return source_file->getFileName();
}

bool offset_in_range(std::uint32_t offset, std::uint32_t start, std::uint32_t size)
{
    return offset >= start && offset < start + size;
}

std::map<std::uint32_t, std::string> build_checksum_source_map(
    const llvm::pdb::PDBStringTable& string_table,
    const llvm::codeview::DebugChecksumsSubsectionRef& checksums
)
{
    std::map<std::uint32_t, std::string> source_files_by_checksum_offset;
    for (auto iterator = checksums.begin(); iterator != checksums.end(); ++iterator) {
        auto source_file = string_table.getStringTable().getString((*iterator).FileNameOffset);
        if (!source_file) {
            llvm::consumeError(source_file.takeError());
            continue;
        }

        source_files_by_checksum_offset[iterator.offset()] = source_file->str();
    }

    return source_files_by_checksum_offset;
}

std::optional<std::string> source_file_for_checksum_offset(
    const std::map<std::uint32_t, std::string>& source_files_by_checksum_offset,
    std::uint32_t checksum_offset
)
{
    const auto source_file = source_files_by_checksum_offset.find(checksum_offset);
    if (source_file == source_files_by_checksum_offset.end()) {
        return std::nullopt;
    }

    return source_file->second;
}

void SourceLineIndex::add_range(SourceLineRange range)
{
    if (range.source_file.empty() || range.start_offset >= range.end_offset) {
        return;
    }

    ranges_by_segment_[range.segment].push_back(std::move(range));
}

SourceLineIndex SourceLineIndex::build(
    llvm::pdb::NativeSession& session,
    const llvm::pdb::ModuleDebugStreamRef& module_stream,
    DiagnosticSink& diagnostics
)
{
    SourceLineIndex index;

    auto string_table = session.getPDBFile().getStringTable();
    if (!string_table) {
        llvm::consumeError(string_table.takeError());
        return index;
    }

    auto checksums = module_stream.findChecksumsSubsection();
    if (!checksums) {
        llvm::consumeError(checksums.takeError());
        return index;
    }

    const auto source_files_by_checksum_offset = build_checksum_source_map(
        *string_table,
        *checksums);

    for (const auto& subsection : module_stream.subsections()) {
        if (subsection.kind() != llvm::codeview::DebugSubsectionKind::Lines) {
            continue;
        }

        llvm::codeview::DebugLinesSubsectionRef lines;
        llvm::BinaryStreamReader reader(subsection.getRecordData());
        if (auto error = lines.initialize(reader)) {
            diagnostics.warning("Unable to read a line subsection: " + llvm_error_to_string(std::move(error)));
            continue;
        }

        const auto* header = lines.header();
        if (header == nullptr) {
            continue;
        }

        for (const auto& block : lines) {
            auto source_file = source_file_for_checksum_offset(
                source_files_by_checksum_offset,
                block.NameIndex);
            if (!source_file.has_value()) {
                continue;
            }

            for (const auto& line : block.LineNumbers) {
                const auto line_info = llvm::codeview::LineInfo(line.Flags);
                if (!line_info.isStatement()) {
                    continue;
                }

                const auto raw_offset = static_cast<std::uint32_t>(line.Offset);
                const auto rebased_offset = static_cast<std::uint32_t>(
                    header->RelocOffset + line.Offset);
                index.add_range({
                    header->RelocSegment,
                    raw_offset,
                    raw_offset + 1,
                    *source_file,
                });
                index.add_range({
                    header->RelocSegment,
                    rebased_offset,
                    rebased_offset + 1,
                    *source_file,
                });
            }
        }
    }

    for (auto& [_, ranges] : index.ranges_by_segment_) {
        std::sort(
            ranges.begin(),
            ranges.end(),
            [](const SourceLineRange& lhs, const SourceLineRange& rhs) {
                if (lhs.start_offset != rhs.start_offset) {
                    return lhs.start_offset < rhs.start_offset;
                }
                return lhs.end_offset < rhs.end_offset;
            });
    }

    return index;
}

std::optional<std::string> SourceLineIndex::find_source_file(
    const llvm::codeview::ProcSym& function
) const
{
    const auto ranges = ranges_by_segment_.find(function.Segment);
    if (ranges == ranges_by_segment_.end()) {
        return std::nullopt;
    }

    const auto function_start = function.CodeOffset;
    const auto function_end = function.CodeOffset + function.CodeSize;
    const auto& segment_ranges = ranges->second;
    const auto first_line_in_function = std::lower_bound(
        segment_ranges.begin(),
        segment_ranges.end(),
        function_start,
        [](const SourceLineRange& range, std::uint32_t offset) {
            return range.start_offset < offset;
        });

    if (first_line_in_function != segment_ranges.end()
        && first_line_in_function->start_offset < function_end) {
        return first_line_in_function->source_file;
    }

    if (first_line_in_function != segment_ranges.begin()) {
        const auto previous_line = std::prev(first_line_in_function);
        if (offset_in_range(function_start, previous_line->start_offset, previous_line->end_offset)) {
            return previous_line->source_file;
        }
    }

    return std::nullopt;
}

void extract_module_functions(
    llvm::pdb::NativeSession& session,
    const std::string& module_name,
    std::uint32_t module_index,
    ExtractionResult& result,
    std::set<std::pair<std::uint32_t, std::string>>& seen_functions,
    std::uint32_t& skipped_without_source,
    DiagnosticSink& diagnostics
)
{
    auto module_stream = session.getModuleDebugStream(module_index);
    if (!module_stream) {
        llvm::consumeError(module_stream.takeError());
        return;
    }

    bool had_symbol_error = false;
    const auto source_line_index = SourceLineIndex::build(
        session,
        *module_stream,
        diagnostics);

    for (const auto& symbol : module_stream->symbols(&had_symbol_error)) {
        if (!is_function_symbol(symbol.kind())) {
            continue;
        }

        auto proc = llvm::codeview::SymbolDeserializer::deserializeAs<llvm::codeview::ProcSym>(symbol);
        if (!proc) {
            diagnostics.warning(
                "Unable to deserialize a procedure symbol: "
                + llvm_error_to_string(proc.takeError()));
            continue;
        }

        if (proc->Segment == 0 || proc->CodeOffset == 0 || proc->CodeSize == 0 || proc->Name.empty()) {
            continue;
        }

        const auto rva = session.getRVAFromSectOffset(proc->Segment, proc->CodeOffset);
        if (rva == 0) {
            continue;
        }

        auto source_file = source_line_index.find_source_file(*proc);
        if (!source_file.has_value()) {
            source_file = source_file_for_proc_sym(session, *proc, rva);
        }

        if (!source_file.has_value() || source_file->empty()) {
            ++skipped_without_source;
            continue;
        }

        auto name = proc->Name.str();
        if (!seen_functions.insert({rva, name}).second) {
            continue;
        }

        result.functions.push_back({
            std::move(name),
            module_name,
            std::move(*source_file),
            rva,
        });
    }

    if (had_symbol_error) {
        diagnostics.warning("A module debug stream contained malformed symbol records");
    }
}

ExtractionResult extract_functions_from_native_session(
    llvm::pdb::NativeSession& session,
    const std::string& module_name,
    DiagnosticSink& diagnostics
)
{
    auto dbi = session.getPDBFile().getPDBDbiStream();
    if (!dbi) {
        diagnostics.error("PDB does not expose a DBI stream: " + llvm_error_to_string(dbi.takeError()));
        return {};
    }

    ExtractionResult result;
    std::set<std::pair<std::uint32_t, std::string>> seen_functions;
    std::uint32_t skipped_without_source = 0;

    const auto module_count = dbi->modules().getModuleCount();
    for (std::uint32_t module_index = 0; module_index < module_count; ++module_index) {
        extract_module_functions(
            session,
            module_name,
            module_index,
            result,
            seen_functions,
            skipped_without_source,
            diagnostics);
    }

    if (skipped_without_source > 0) {
        diagnostics.warning(
            "Skipped " + std::to_string(skipped_without_source)
            + " function symbols without source-file information");
    }

    return result;
}

class PdbExtractorBackend final : public ExtractorBackend {
public:
    [[nodiscard]] std::string name() const override
    {
        return "pdb";
    }

    [[nodiscard]] bool can_handle(
        const ExtractionOptions& options,
        DiagnosticSink& diagnostics
    ) const override
    {
        auto coff = load_coff_object(options.module_path, nullptr);
        if (!coff) {
            return false;
        }

        if (options.pdb_path.has_value()) {
            return true;
        }

        return read_pdb_reference(*coff->coff, diagnostics).has_value();
    }

    [[nodiscard]] ExtractionResult extract(
        const ExtractionOptions& options,
        DiagnosticSink& diagnostics
    ) const override
    {
        auto coff = load_coff_object(options.module_path, &diagnostics);
        if (!coff) {
            return {};
        }

        const auto reference = read_pdb_reference(*coff->coff, diagnostics);
        auto pdb_path = resolve_pdb_path(options, reference, diagnostics);
        if (!pdb_path.has_value()) {
            return {};
        }

        auto session = load_pdb_session(*pdb_path, diagnostics);
        if (!session) {
            return {};
        }

        if (!validate_identity(*session, reference, diagnostics)) {
            return {};
        }

        auto* native_session = static_cast<llvm::pdb::NativeSession*>(session.get());
        const auto module_name = options.module_path.filename().string();
        auto result = extract_functions_from_native_session(
            *native_session,
            module_name,
            diagnostics);

        std::sort(
            result.functions.begin(),
            result.functions.end(),
            [](const FunctionInfo& lhs, const FunctionInfo& rhs) {
                if (lhs.module_name != rhs.module_name) {
                    return lhs.module_name < rhs.module_name;
                }
                if (lhs.address_offset != rhs.address_offset) {
                    return lhs.address_offset < rhs.address_offset;
                }
                return lhs.name < rhs.name;
            });

        if (result.functions.empty() && !diagnostics.has_errors()) {
            diagnostics.warning("PDB did not produce any source-backed function symbols");
        }

        return result;
    }
};

} // namespace

std::unique_ptr<ExtractorBackend> create_pdb_extractor_backend()
{
    return std::make_unique<PdbExtractorBackend>();
}

} // namespace symbol_extractor
