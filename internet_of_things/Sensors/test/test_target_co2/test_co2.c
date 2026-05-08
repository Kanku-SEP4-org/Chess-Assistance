#include "unity.h"
#include "co2.h"

void co2_uart_rx_callback(uint8_t byte);

static uint16_t _test_co2_ppm = 0;

void setUp(void) 
{
    // This is run before EACH test
    _test_co2_ppm = 0; // Reset test CO2 ppm value before each test
}

void tearDown(void) 
{
    // This is run after EACH test
}

void test_co2_init_valid_callback(void) 
{
    co2_status_t status = co2_init((void (*)(uint16_t))1); // Pass a non-NULL callback
    TEST_ASSERT_EQUAL(CO2_OK, status); // Initialization should succeed
}

void test_co2_init_null_callback(void) 
{
    co2_status_t status = co2_init(NULL); // Pass a NULL callback
    TEST_ASSERT_EQUAL(CO2_ERROR, status); // Initialization should fail
}

void test_co2_start_measure(void) 
{
    // First, initialize with a valid callback
    co2_status_t status = co2_init((void (*)(uint16_t))1);
    TEST_ASSERT_EQUAL(CO2_OK, status); // Initialization should succeed

    // Now start measurement
    status = co2_start_measure();
    TEST_ASSERT_EQUAL(CO2_OK, status); // Starting measurement should succeed
}

void co2_test_callback(uint16_t co2_ppm)
{
    // This is a test callback function that can be used to verify that the callback mechanism works
    // For example, we could set a global variable here to check if the callback was called with the correct value
    _test_co2_ppm = co2_ppm;
}

void test_co2_callback_mechanism_correct_checksum(void) 
{
    // Initialize with our test callback
    co2_status_t status = co2_init(co2_test_callback);
    TEST_ASSERT_EQUAL(CO2_OK, status); // Initialization should succeed

    // Simulate receiving a CO2 measurement by directly calling the UART RX callback
    uint8_t simulated_response[] = {0xFF, 0x86, 0x01, 0xF4, 0x00, 0x00, 0x00, 0x00, 0x85}; // Example response for 500 ppm
    for (size_t i = 0; i < sizeof(simulated_response); i++)    
    {
        co2_uart_rx_callback(simulated_response[i]);
    }

    // Check if the callback was called with the correct CO2 ppm value (500 ppm in this case)
    TEST_ASSERT_EQUAL(500, _test_co2_ppm);
}

void test_co2_callback_mechanism_incorrect_checksum(void) 
{
    // Initialize with our test callback
    co2_status_t status = co2_init(co2_test_callback);
    TEST_ASSERT_EQUAL(CO2_OK, status); // Initialization should succeed

    // Simulate receiving a CO2 measurement by directly calling the UART RX callback
    uint8_t simulated_response[] = {0xFF, 0x86, 0x01, 0xF4, 0x00, 0x00, 0x00, 0x00, 0xAA}; // Example response for 500 ppm with incorrect checksum
    for (size_t i = 0; i < sizeof(simulated_response); i++)    
    {
        co2_uart_rx_callback(simulated_response[i]);
    }

    // Check if the callback was called with the correct CO2 ppm value (500 ppm in this case)
    TEST_ASSERT_EQUAL(0, _test_co2_ppm);
}

int main(void) 
{
    UNITY_BEGIN();
    RUN_TEST(test_co2_init_valid_callback);
    RUN_TEST(test_co2_init_null_callback);
    RUN_TEST(test_co2_start_measure);
    RUN_TEST(test_co2_callback_mechanism_correct_checksum);
    RUN_TEST(test_co2_callback_mechanism_incorrect_checksum);
    return UNITY_END();
}

