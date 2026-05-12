cmake_minimum_required(VERSION 3.20)
project(CloudCProject C)

set(CMAKE_C_STANDARD 11)

# --- 1. DEFINE PATHS FIRST ---
set(RABBIT_DIR "${CMAKE_CURRENT_SOURCE_DIR}/libs/rabbitmq-c-0.15.0")
set(UNITY_SRC "${CMAKE_CURRENT_SOURCE_DIR}/tests/Unity/src/unity.c")

# Fail-fast check for Unity
if(NOT EXISTS "${UNITY_SRC}")
    message(FATAL_ERROR "Unity source not found at: ${UNITY_SRC}")
endif()

# --- 2. OS-SPECIFIC CONFIGURATION ---
if(WIN32)
    # Windows: Use the local headers and the specific .dll.a file
    include_directories("${RABBIT_DIR}/include")
    include_directories("${RABBIT_DIR}/include/rabbitmq-c")
    set(RABBIT_LIB "${RABBIT_DIR}/lib/librabbitmq.4.dll.a")

    # Add Windows-specific definitions to help headers behave
    add_definitions(-D_WIN32_WINNT=0x0600)
else()
    # Linux (GitHub Actions): Use system headers and the library from apt-get
    # We DO NOT include_directories("${RABBIT_DIR}/include") here to avoid __declspec errors
    set(RABBIT_LIB "rabbitmq")
endif()

# Global Fix: Treat RabbitMQ as static to avoid DLL export issues
add_definitions(-DAMQP_STATIC)

# Common Includes
include_directories(
        src
        tests/Unity/src
)

# --- 3. COLLECT SOURCE FILES ---
file(GLOB_RECURSE ALL_SRC_FILES "${CMAKE_CURRENT_SOURCE_DIR}/src/*.c")
list(REMOVE_ITEM ALL_SRC_FILES "${CMAKE_CURRENT_SOURCE_DIR}/src/main.c")

# --- 4. EXECUTABLES ---
add_executable(test_message_builder
        "${CMAKE_CURRENT_SOURCE_DIR}/tests/test_message_builder.c"
        "${UNITY_SRC}"
        "${CMAKE_CURRENT_SOURCE_DIR}/src/message_builder.c"
        "${CMAKE_CURRENT_SOURCE_DIR}/src/sensor_reader.c"
)

add_executable(test_sensor_reader
        "${CMAKE_CURRENT_SOURCE_DIR}/tests/test_sensor_reader.c"
        "${UNITY_SRC}"
        ${ALL_SRC_FILES}
)

add_executable(sensor_client
        "${CMAKE_CURRENT_SOURCE_DIR}/src/main.c"
        ${ALL_SRC_FILES}
)

# --- 5. LINKING ---
# We use the ${RABBIT_LIB} variable we set in the IF/ELSE block above
target_link_libraries(test_sensor_reader PRIVATE ${RABBIT_LIB})
target_link_libraries(sensor_client PRIVATE ${RABBIT_LIB})