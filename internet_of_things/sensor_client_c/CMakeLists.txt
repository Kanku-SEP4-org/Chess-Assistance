cmake_minimum_required(VERSION 3.20)
project(CloudCProject C)

set(CMAKE_C_STANDARD 11)

# --- 1. SETUP PATHS (Relative to project) ---
set(RABBIT_DIR "${CMAKE_CURRENT_SOURCE_DIR}/libs/rabbitmq-c-0.15.0")
set(UNITY_SRC "${CMAKE_CURRENT_SOURCE_DIR}/tests/unity/src/unity.c")

# Check if the file actually exists before proceeding
if(NOT EXISTS ${UNITY_SRC})
    message(FATAL_ERROR "Unity source not found at: ${UNITY_SRC}")
endif()


# --- 2. COLLECT SOURCE FILES ---
file(GLOB_RECURSE ALL_SRC_FILES "src/*.c")
list(REMOVE_ITEM ALL_SRC_FILES "${CMAKE_CURRENT_SOURCE_DIR}/src/main.c")



include_directories(
        src
        tests/unity/src
        "${RABBIT_DIR}/include"
)


# --- 3. EXECUTABLES ---

# Test: Message Builder
add_executable(test_message_builder
        "${CMAKE_CURRENT_SOURCE_DIR}/tests/test_message_builder.c"
        "${UNITY_SRC}"
        "${CMAKE_CURRENT_SOURCE_DIR}/src/message_builder.c"
        "${CMAKE_CURRENT_SOURCE_DIR}/src/sensor_reader.c"
)

# Test: Sensor Reader
add_executable(
        "${CMAKE_CURRENT_SOURCE_DIR}/tests/test_sensor_reader.c"
        "${UNITY_SRC}"
        ${ALL_SRC_FILES}
)


# Main App
add_executable(sensor_client
        "${CMAKE_CURRENT_SOURCE_DIR}/src/main.c"
        ${ALL_SRC_FILES}
)

# 1. Point to the folder containing librabbitmq.4.dll.a
link_directories("${RABBIT_DIR}/lib")

# 2. Link the library
# Define exactly where that .dll.a file is
set(RABBIT_LIB_PATH "${RABBIT_DIR}/lib/librabbitmq.4.dll.a")


# Link targets
if(EXISTS "${RABBIT_LIB_PATH}")
    target_link_libraries(test_sensor_reader PRIVATE "${RABBIT_LIB_PATH}")
    target_link_libraries(sensor_client PRIVATE "${RABBIT_LIB_PATH}")
else()
    # On Linux/GitHub Actions, use the library installed via apt-get
    target_link_libraries(test_sensor_reader PRIVATE rabbitmq)
    target_link_libraries(sensor_client PRIVATE rabbitmq)
endif()