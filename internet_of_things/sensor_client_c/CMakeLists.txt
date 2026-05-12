cmake_minimum_required(VERSION 3.20)
project(CloudCProject C)

set(CMAKE_C_STANDARD 11)

# --- 1. SETUP PATHS ---
set(RABBIT_DIR "${CMAKE_CURRENT_SOURCE_DIR}/libs/rabbitmq-c-0.15.0")
set(UNITY_SRC "${CMAKE_CURRENT_SOURCE_DIR}/tests/Unity/src/unity.c")

if(NOT EXISTS ${UNITY_SRC})
    message(FATAL_ERROR "Unity source not found at: ${UNITY_SRC}")
endif()

# --- THE FIX: Tell RabbitMQ headers to ignore Windows-specific DLL logic ---
add_definitions(-DAMQP_STATIC)

include_directories(
        src
        tests/Unity/src
        "${RABBIT_DIR}/include"
)

# --- 2. COLLECT SOURCE FILES ---
file(GLOB_RECURSE ALL_SRC_FILES "${CMAKE_CURRENT_SOURCE_DIR}/src/*.c")
list(REMOVE_ITEM ALL_SRC_FILES "${CMAKE_CURRENT_SOURCE_DIR}/src/main.c")

# --- 3. EXECUTABLES ---

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

# --- 4. LINKING ---
set(RABBIT_LIB_PATH "${RABBIT_DIR}/lib/librabbitmq.4.dll.a")

if(EXISTS "${RABBIT_LIB_PATH}")
    target_link_libraries(test_sensor_reader PRIVATE "${RABBIT_LIB_PATH}")
    target_link_libraries(sensor_client PRIVATE "${RABBIT_LIB_PATH}")
else()
    # On Linux, use the system library installed via apt-get
    target_link_libraries(test_sensor_reader PRIVATE rabbitmq)
    target_link_libraries(sensor_client PRIVATE rabbitmq)
endif()