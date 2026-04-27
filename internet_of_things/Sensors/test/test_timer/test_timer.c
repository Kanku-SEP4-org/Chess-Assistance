#include "unity.h"
#include "timer.h"


void setUp(void) {
    // This is run before EACH test
    for (int8_t i = 0; i < TIMER_MAX_TIMERS; i++) 
    {
        timer_delete(i + 1); // Clean up any existing timers
    }
}

void tearDown(void) {
    // This is run after EACH test
}

void test_timer_create_valid(void) {
    int8_t timer_id = timer_create_sw(NULL, 1000);
    TEST_ASSERT_EQUAL(TIMER_ERROR_NO_RESOURCES, timer_id); // Callback is NULL

    timer_id = timer_create_sw((void (*)(uint8_t))1, 0);
    TEST_ASSERT_EQUAL(TIMER_ERROR_INVALID_INTERVAL, timer_id); // Invalid interval

    timer_id = timer_create_sw((void (*)(uint8_t))1, 1000);
    TEST_ASSERT(timer_id > 0); // Valid creation
}

void test_timer_create_invalid_interval(void) {
    int8_t timer_id = timer_create_sw((void (*)(uint8_t))1, 0);
    TEST_ASSERT_EQUAL(TIMER_ERROR_INVALID_INTERVAL, timer_id); // Invalid interval

    timer_id = timer_create_sw((void (*)(uint8_t))1, TIMER_MAX_INTERVAL_MS + 1);
    TEST_ASSERT_EQUAL(TIMER_ERROR_INVALID_INTERVAL, timer_id); // Invalid interval
}

void test_timer_create_no_resources(void) {
    // Create maximum number of timers
    for (int i = 0; i < TIMER_MAX_TIMERS; i++) {
        int8_t timer_id = timer_create_sw((void (*)(uint8_t))1, 1000);
        TEST_ASSERT(timer_id > 0); // Valid creation
    }
    // Attempt to create one more timer, which should fail
    int8_t timer_id = timer_create_sw((void (*)(uint8_t))1, 1000);
    TEST_ASSERT_EQUAL(TIMER_ERROR_NO_RESOURCES, timer_id); // No resources available
}

void test_timer_state(void) {
    int8_t timer_id = timer_create_sw((void (*)(uint8_t))1, 1000);
    TEST_ASSERT(timer_id > 0); // Valid creation

    int8_t state = timer_get_state(timer_id);
    TEST_ASSERT_EQUAL(1, state); // Timer should be active

    timer_pause(timer_id);
    state = timer_get_state(timer_id);
    TEST_ASSERT_EQUAL(0, state); // Timer should be paused

    timer_resume(timer_id);
    state = timer_get_state(timer_id);
    TEST_ASSERT_EQUAL(1, state); // Timer should be active again
}

int main(void) {
    UNITY_BEGIN();
    // Add test cases here, e.g.:
    RUN_TEST(test_timer_create_valid);
    RUN_TEST(test_timer_create_invalid_interval);
    RUN_TEST(test_timer_create_no_resources);
    RUN_TEST(test_timer_state);
    return UNITY_END();
}   
