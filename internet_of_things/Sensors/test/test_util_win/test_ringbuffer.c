#include "unity.h"
#include "ringbuffer.h"

#define TEST_CAPACITY 4
#define TEST_ELEM_SIZE sizeof(int)

static ringbuffer_t *rb;

void setUp(void) {
    rb = ringbuffer_create(TEST_CAPACITY, TEST_ELEM_SIZE);
    TEST_ASSERT_NOT_NULL(rb);
}

void tearDown(void) {
    if (rb) {
        ringbuffer_destroy(rb);
        rb = NULL;
    }
}

void test_ringbuffer_push_pop(void) {
    int value;

    // Push elements into the ring buffer
    for (int i = 0; i < TEST_CAPACITY; i++) {
        TEST_ASSERT_TRUE(ringbuffer_push(rb, &i));
    }

    // Pop elements from the ring buffer and verify
    for (int i = 0; i < TEST_CAPACITY; i++) {
        TEST_ASSERT_TRUE(ringbuffer_pop(rb, &value));
        TEST_ASSERT_EQUAL_INT(i, value);
    }

    // Verify that the ring buffer is empty
    TEST_ASSERT_FALSE(ringbuffer_pop(rb, &value));
}

void test_ringbuffer_overwrite(void) {
    int value;

    // Push elements into the ring buffer
    for (int i = 0; i < TEST_CAPACITY; i++) {
        TEST_ASSERT_TRUE(ringbuffer_push(rb, &i));
    }

    // Push another element to overwrite the oldest one
    int new_value = 99;
    TEST_ASSERT_TRUE(ringbuffer_push(rb, &new_value));

    // Pop elements and verify the overwritten value
    TEST_ASSERT_TRUE(ringbuffer_pop(rb, &value));
    TEST_ASSERT_EQUAL_INT(1, value); // The first element (0) should be overwritten

    for (int i = 2; i < TEST_CAPACITY; i++) {
        TEST_ASSERT_TRUE(ringbuffer_pop(rb, &value));
        TEST_ASSERT_EQUAL_INT(i, value);
    }

    // Verify that the new value is present
    TEST_ASSERT_TRUE(ringbuffer_pop(rb, &value));
    TEST_ASSERT_EQUAL_INT(new_value, value);
}

void test_ringbuffer_empty_full(void) {
    // Verify that the ring buffer is initially empty
    TEST_ASSERT_TRUE(ringbuffer_is_empty(rb));

    // Push elements until the ring buffer is full
    for (int i = 0; i < TEST_CAPACITY; i++) {
        TEST_ASSERT_TRUE(ringbuffer_push(rb, &i));
    }

    // Verify that the ring buffer is full
    TEST_ASSERT_TRUE(ringbuffer_is_full(rb));
}

int main(void) {
    UNITY_BEGIN();
    RUN_TEST(test_ringbuffer_push_pop);
    RUN_TEST(test_ringbuffer_overwrite);
    RUN_TEST(test_ringbuffer_empty_full);
    return UNITY_END();
}