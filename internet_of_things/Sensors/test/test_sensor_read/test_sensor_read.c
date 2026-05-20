//
// Created by ana on 25-April-26.
//
#include <unity.h>
#include <string.h>
#include "services/sensorRead.h"
#include "dht11.h"
#include "services/communication.h"
#include "light.h"
#include "co2.h"

// --- MOCKING AREA ---
// global variables that the "Fake" functions will use
static char mock_transmit_buffer[100];
static uint8_t fake_h_int, fake_h_dec, fake_t_int, fake_t_dec;
static uint16_t fake_co2_value;
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

// Fake Light driver
uint16_t light_measure_raw() {
    return 460;
}

ADC_Error_t light_init() {
    return ADC_OK;
}

// Additional inits for errors
ADC_Error_t light_init_channel() {
    return ADC_ERROR_INVALID_CHANNEL;
}

ADC_Error_t light_init_reference() {
    return ADC_ERROR_INVALID_REFERENCE;
}

// Fake water driver
uint16_t soil_measure_raw(ADC_Channel_t channel) {
    return 460;
}

ADC_Error_t soil_init(ADC_Channel_t channel) {
    return ADC_OK;
}

// Additional inits for errors
ADC_Error_t soil_init_channel(ADC_Channel_t channel) {
    return ADC_ERROR_INVALID_CHANNEL;
}

ADC_Error_t soil_init_reference(ADC_Channel_t channel) {
    return ADC_ERROR_INVALID_REFERENCE;
}

// --- UNITY SETUP ---

void setUp(void) {
    // Reset the buffer and fake data before every test
    memset(mock_transmit_buffer, 0, sizeof(mock_transmit_buffer));
    fake_h_int = 0; fake_h_dec = 0; fake_t_int = 0; fake_t_dec = 0;
    fake_dht_status = DHT11_OK;
    // Force clear internal state of latest_co2_ppm by passing a 0 value
    co2_incoming_data_handler(0);
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

void test_report_humidity_fail(void) {
    // Arrange: Simulate a sensor failure
    fake_dht_status = DHT11_FAIL;

    // Act
    get_and_report_humidity();

    // Assert
    TEST_ASSERT_EQUAL_STRING("ERROR:DHT11_READ_FAIL\n", mock_transmit_buffer);
}

void test_report_light_format(void){
    // set up fake light sensor
    ADC_Error_t light = light_init();

    get_and_report_light(light);

    TEST_ASSERT_EQUAL_STRING("LIG:460", mock_transmit_buffer);
}

void test_report_light_error_channel(void){
    // set up error
    ADC_Error_t light = light_init_channel();

    get_and_report_light(light);

    TEST_ASSERT_EQUAL_STRING("ERROR:ADC_ERROR_INVALID_CHANNEL", mock_transmit_buffer);
}

void test_report_light_error_reference(void){
    // set up error
    ADC_Error_t light = light_init_reference();

    get_and_report_light(light);

    TEST_ASSERT_EQUAL_STRING("ERROR:ADC_ERROR_INVALID_REFERENCE", mock_transmit_buffer);
}

void test_report_water_format(void){
    // set up fake water sensor
    ADC_Error_t water = soil_init(ADC_PK0);

    get_and_report_water(water);

    TEST_ASSERT_EQUAL_STRING("WAT:460", mock_transmit_buffer);
}

void test_report_water_error_channel(void){
    // set up error
    ADC_Error_t water = soil_init_channel(ADC_PK0);

    get_and_report_water(water);

    TEST_ASSERT_EQUAL_STRING("ERROR:ADC_ERROR_INVALID_CHANNEL", mock_transmit_buffer);
}

void test_report_water_error_reference(void){
    // set up error
    ADC_Error_t water = soil_init_reference(ADC_PK0);

    get_and_report_water(water);

    TEST_ASSERT_EQUAL_STRING("ERROR:ADC_ERROR_INVALID_REFERENCE", mock_transmit_buffer);
}

void test_report_co2_no_data_yet(void) {
    // Arrange: Ensure state is 0 (handled by setUp)

    // Act: Request reporting output
    get_and_report_co2();

    // Assert: Check for target error message string
    TEST_ASSERT_EQUAL_STRING("ERROR:CO2_NO_DATA_YET", mock_transmit_buffer);
}

void test_report_co2_valid_value_format(void) {
    // Arrange: Simulate the callback running from a UART packet capture event
    co2_incoming_data_handler(450);

    // Act: Request reporting output
    get_and_report_co2();

    // Assert: Ensure it formats correctly
    TEST_ASSERT_EQUAL_STRING("CO2:450", mock_transmit_buffer);
}

// --- MAIN ---

int main(void) {
    UNITY_BEGIN();
    RUN_TEST(test_report_temperature_normal_format);
    RUN_TEST(test_report_humidity_fail);
    RUN_TEST(test_report_light_format);
    RUN_TEST(test_report_light_error_channel);
    RUN_TEST(test_report_light_error_reference);
    RUN_TEST(test_report_water_format);
    RUN_TEST(test_report_water_error_channel);
    RUN_TEST(test_report_water_error_reference);
    RUN_TEST(test_report_co2_no_data_yet);
    RUN_TEST(test_report_co2_valid_value_format);
    return UNITY_END();
}