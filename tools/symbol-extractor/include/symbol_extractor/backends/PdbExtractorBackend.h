#pragma once

#include "symbol_extractor/Extractor.h"

#include <memory>

namespace symbol_extractor {

std::unique_ptr<ExtractorBackend> create_pdb_extractor_backend();

} // namespace symbol_extractor
