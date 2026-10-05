if(NOT DEFINED EXECUTABLE)
    message(FATAL_ERROR "EXECUTABLE is required")
endif()

if(NOT DEFINED EXPECTED_EXIT_CODE)
    message(FATAL_ERROR "EXPECTED_EXIT_CODE is required")
endif()

if(NOT DEFINED EXPECTED_OUTPUT)
    message(FATAL_ERROR "EXPECTED_OUTPUT is required")
endif()

if(NOT DEFINED ARGS)
    set(ARGS "")
endif()

execute_process(
    COMMAND "${EXECUTABLE}" ${ARGS}
    RESULT_VARIABLE actual_exit_code
    OUTPUT_VARIABLE stdout
    ERROR_VARIABLE stderr
)

if(NOT actual_exit_code EQUAL EXPECTED_EXIT_CODE)
    message(FATAL_ERROR
        "Expected exit code ${EXPECTED_EXIT_CODE}, got ${actual_exit_code}\n"
        "stdout:\n${stdout}\n"
        "stderr:\n${stderr}"
    )
endif()

string(CONCAT output "${stdout}" "${stderr}")
string(FIND "${output}" "${EXPECTED_OUTPUT}" expected_output_position)
if(expected_output_position EQUAL -1)
    message(FATAL_ERROR
        "Expected output to contain: ${EXPECTED_OUTPUT}\n"
        "stdout:\n${stdout}\n"
        "stderr:\n${stderr}"
    )
endif()
