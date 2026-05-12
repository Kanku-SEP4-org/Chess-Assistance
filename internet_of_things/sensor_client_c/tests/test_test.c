//demonstrtation file

#include "unity.h"

//Run before every test
void setUp(void){}

//Runs after every test
void tearDown(void){}

void test_Should_Pass_Standard_Logic(void) {
    // normally a real function from the src/ directory
    int result = 1 + 1; 
    TEST_ASSERT_EQUAL_INT(2, result);
}

int main(void) {
    UNITY_BEGIN();
    RUN_TEST(test_Should_Pass_Standard_Logic);
    return UNITY_END();
}