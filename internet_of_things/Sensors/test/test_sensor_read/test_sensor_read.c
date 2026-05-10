//
// Created by ana on 25-April-26.
//
#include <unity.h>
#include <string.h>
#include "sensorRead.h"
#include "dht11.h"
#include "communication.h"

// --- MOCKING AREA ---
// global variables that the "Fake" functions will use
static char mock_transmit_buffer[100];
static uint8_t fake_h_int, fake_h_dec, fake_t_int, fake_t_dec;
static DHT11_ERROR_MESSAGE_t fake_dht_status;

// "Fake" the communication driver
void transmit_data(char* str) {
    strcpy(mock_transmit_buffer, str); // Capture the output
}

// "Fake" the DHT11 driver
DHT11_ERROR_MESSAGE_t dht11_get(uint8_t* h_i, uint8_t* h_d, uint8_t* t_i, uint8_t* t_d) {
    if (h_i) *h_i = fake_h_int;
    if (h_d) *h_d = fake_h_dec;
    if (t_i) *t_i = fake_t_int;
    if (t_d) *t_d = fake_t_dec;
    return fake_dht_status;
}

// --- UNITY SETUP ---

void setUp(void) {
    // Reset the buffer and fake data before every test
    memset(mock_transmit_buffer, 0, sizeof(mock_transmit_buffer));
    fake_h_int = 0; fake_h_dec = 0; fake_t_int = 0; fake_t_dec = 0;
    fake_dht_status = DHT11_OK;
}

void tearDown(void) {}

// --- TESTS ---

void test_report_temperature_normal_format(void) {
    // Arrange: Set the fake sensor to 25.5 degrees
    fake_t_int = 25;
    fake_t_dec = 5;

    // Act: Run the function
    get_and_report_temperature();

    // Assert: Did it format the string correctly?
    TEST_ASSERT_EQUAL_STRING("TEMP:25.5\n", mock_transmit_buffer);
}

void test_report_temperature_json_format(void) {
    // Arrange: Set sensor to 22.3 degrees
    fake_t_int = 22;
    fake_t_dec = 3;

    // Act
    get_and_report_temp_json();

    // Assert
    TEST_ASSERT_EQUAL_STRING("{\"temperature\": 22.3}", mock_transmit_buffer);
}

void test_report_humidity_fail(void) {
    // Arrange: Simulate a sensor failure
    fake_dht_status = DHT11_FAIL;

    // Act
    get_and_report_humidity();

    // Assert
    TEST_ASSERT_EQUAL_STRING("ERROR:DHT11_READ_FAIL\n", mock_transmit_buffer);
}

void test_report_humidity_json(void) {
    // Arrange
    fake_h_int = 45;
    fake_h_dec = 0;

    // Act
    get_and_report_hum_json();

    // Assert
    TEST_ASSERT_EQUAL_STRING("{\"humidity\": 45.0}\n", mock_transmit_buffer);
}

// --- MAIN ---

int main(void) {
    UNITY_BEGIN();
    RUN_TEST(test_report_temperature_normal_format);
    RUN_TEST(test_report_temperature_json_format);
    RUN_TEST(test_report_humidity_fail);
    RUN_TEST(test_report_humidity_json);
    return UNITY_END();
}