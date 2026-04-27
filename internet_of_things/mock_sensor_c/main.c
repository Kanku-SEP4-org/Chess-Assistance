#include "communication.h"
#include <stdio.h>
#include <stddef.h>

void get_and_report_temperature(void) {
    uint8_t h_int, h_dec, t_int, t_dec;

    // Call the temperature and humidity driver
  
    // Clear, consistent output for the C# app
    char buffer[50];
    sprintf(buffer,"TEMP:%d.%f\n", 23, 20.5); //TEMP:20.5
    transmit_data(buffer);
}

int main(void){
    get_and_report_temperature();
    return 0;
}