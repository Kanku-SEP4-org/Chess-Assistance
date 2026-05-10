cmake_minimum_required(VERSION 3.20)
project(CloudCProject C)

set(CMAKE_C_STANDARD 11)

# --- 1. SETUP RABBITMQ PATHS (Relative to project) ---
set(RABBIT_DIR "${CMAKE_CURRENT_SOURCE_DIR}/libs/rabbitmq-c-0.15.0")

include_directories(
        src
        tests/unity/src
        "${RABBIT_DIR}/include"
)


# --- 2. COLLECT SOURCE FILES ---
file(GLOB_RECURSE ALL_SRC_FILES "src/*.c")
list(REMOVE_ITEM ALL_SRC_FILES "${CMAKE_CURRENT_SOURCE_DIR}/src/main.c")

set(UNITY_SRC tests/unity/src/unity.c)

# --- 3. EXECUTABLES ---

# Test: Message Builder
add_executable(test_message_builder
        tests/test_message_builder.c
        ${UNITY_SRC}
        src/message_builder.c
        src/sensor_reader.c #it calls for read_temperature
)

# Test: Sensor Reader
add_executable(
        test_sensor_reader
        tests/test_sensor_reader.c
        ${UNITY_SRC}
        ${ALL_SRC_FILES}
)


# Main App
add_executable(sensor_client
        src/main.c
        ${ALL_SRC_FILES}
)

# 1. Point to the folder containing librabbitmq.4.dll.a
link_directories("${CMAKE_CURRENT_SOURCE_DIR}/libs/rabbitmq-c-0.15.0/lib")

# 2. Link the library
# Define exactly where that .dll.a file is
set(RABBIT_LIB_PATH "${CMAKE_CURRENT_SOURCE_DIR}/libs/rabbitmq-c-0.15.0/lib/librabbitmq.4.dll.a")

# Link using the FULL PATH instead of just the name
#target_link_libraries(test_message_builder PRIVATE "${RABBIT_LIB_PATH}")
#line above only needed if using ALL_SRC_FILES in the add executable,
# or if the tested file uses RabbitMQ, of course
target_link_libraries(test_sensor_reader PRIVATE "${RABBIT_LIB_PATH}")
target_link_libraries(sensor_client PRIVATE "${RABBIT_LIB_PATH}")