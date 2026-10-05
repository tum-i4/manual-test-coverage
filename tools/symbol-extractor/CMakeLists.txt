cmake_minimum_required(VERSION 3.20)

project(symbol_extractor
    VERSION 0.1.0
    DESCRIPTION "Native symbol extractor for manual-test-coverage"
    LANGUAGES C CXX
)

option(
    SYMBOL_EXTRACTOR_ENABLE_LLVM_PDB
    "Build the LLVM-backed Windows PDB extractor backend"
    ON
)

if(SYMBOL_EXTRACTOR_ENABLE_LLVM_PDB)
    find_package(LLVM REQUIRED CONFIG)
    message(STATUS "Found LLVM ${LLVM_PACKAGE_VERSION}: ${LLVM_DIR}")
    llvm_map_components_to_libnames(
        SYMBOL_EXTRACTOR_LLVM_LIBS
        object
        debuginfopdb
        debuginfocodeview
        support
    )
endif()

add_library(symbol-extractor-core
    src/Extractor.cpp
    src/InfoWriter.cpp
)

if(SYMBOL_EXTRACTOR_ENABLE_LLVM_PDB)
    target_sources(symbol-extractor-core
        PRIVATE
            src/backends/PdbExtractorBackend.cpp
    )
endif()

target_include_directories(symbol-extractor-core
    PUBLIC
        include
)

if(SYMBOL_EXTRACTOR_ENABLE_LLVM_PDB)
    target_include_directories(symbol-extractor-core
        SYSTEM PRIVATE
            ${LLVM_INCLUDE_DIRS}
    )
    target_compile_definitions(symbol-extractor-core
        PRIVATE
            ${LLVM_DEFINITIONS}
    )
    target_link_libraries(symbol-extractor-core
        PRIVATE
            ${SYMBOL_EXTRACTOR_LLVM_LIBS}
    )
endif()

target_compile_definitions(symbol-extractor-core
    PRIVATE
        SYMBOL_EXTRACTOR_HAS_LLVM_PDB=$<BOOL:${SYMBOL_EXTRACTOR_ENABLE_LLVM_PDB}>
)

target_compile_features(symbol-extractor-core PUBLIC cxx_std_17)

add_executable(symbol-extractor
    src/main.cpp
)

target_link_libraries(symbol-extractor
    PRIVATE
        symbol-extractor-core
)

target_compile_features(symbol-extractor PRIVATE cxx_std_17)

function(configure_symbol_extractor_target target_name)
    if(MSVC)
        target_compile_options(${target_name} PRIVATE /W4 /permissive-)
    else()
        target_compile_options(${target_name} PRIVATE -Wall -Wextra -Wpedantic)
    endif()
endfunction()

configure_symbol_extractor_target(symbol-extractor-core)
configure_symbol_extractor_target(symbol-extractor)

install(
    TARGETS symbol-extractor
    RUNTIME DESTINATION tools/symbol-extractor
)

enable_testing()

add_test(
    NAME symbol_extractor_prints_version
    COMMAND $<TARGET_FILE:symbol-extractor> --version
)

add_test(
    NAME symbol_extractor_requires_arguments
    COMMAND ${CMAKE_COMMAND}
        -DEXECUTABLE=$<TARGET_FILE:symbol-extractor>
        -DEXPECTED_EXIT_CODE=2
        "-DEXPECTED_OUTPUT=Both --module and --output-dir are required"
        -P ${CMAKE_CURRENT_SOURCE_DIR}/tests/ExpectCommand.cmake
)

add_test(
    NAME symbol_extractor_reports_missing_backend
    COMMAND ${CMAKE_COMMAND}
        -DEXECUTABLE=$<TARGET_FILE:symbol-extractor>
        "-DARGS=--module;${CMAKE_CURRENT_SOURCE_DIR}/CMakeLists.txt;--output-dir;${CMAKE_CURRENT_BINARY_DIR}/function-info"
        -DEXPECTED_EXIT_CODE=1
        "-DEXPECTED_OUTPUT=No symbol backend can read"
        -P ${CMAKE_CURRENT_SOURCE_DIR}/tests/ExpectCommand.cmake
)

add_test(
    NAME symbol_extractor_validates_explicit_pdb_path
    COMMAND ${CMAKE_COMMAND}
        -DEXECUTABLE=$<TARGET_FILE:symbol-extractor>
        "-DARGS=--module;${CMAKE_CURRENT_SOURCE_DIR}/CMakeLists.txt;--pdb;${CMAKE_CURRENT_BINARY_DIR}/missing.pdb;--output-dir;${CMAKE_CURRENT_BINARY_DIR}/function-info"
        -DEXPECTED_EXIT_CODE=2
        "-DEXPECTED_OUTPUT=PDB does not exist"
        -P ${CMAKE_CURRENT_SOURCE_DIR}/tests/ExpectCommand.cmake
)

add_executable(symbol-extractor-writer-test
    tests/InfoWriterTest.cpp
)
target_link_libraries(symbol-extractor-writer-test
    PRIVATE
        symbol-extractor-core
)
configure_symbol_extractor_target(symbol-extractor-writer-test)

add_test(
    NAME symbol_extractor_writes_info_files
    COMMAND $<TARGET_FILE:symbol-extractor-writer-test>
        ${CMAKE_CURRENT_BINARY_DIR}/writer-test-output
)
