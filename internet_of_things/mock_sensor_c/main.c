#include "communication.h"
#include <stdio.h>
#include <stddef.h>

void get_and_report_temperature(void) {
    char buffer[50];
    sprintf(buffer,"TEMP:%.1f\n", 23.5); //TEMP:20.5
    transmit_data(buffer);
}

void get_and_report_light(void) {
    char buffer[50];
    sprintf(buffer,"LIG:%d\n", 235);
    transmit_data(buffer);
}

int main(void){
    get_and_report_light();
    //get_and_report_temperature();
    return 0;
}