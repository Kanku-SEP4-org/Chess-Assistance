#ifndef SENSOR_READER_H
#define SENSOR_READER_H

int read_temperature(float *temperature);
int read_water(int *water);
int read_light(short *light);
int read_pump_status(int *success);
int fill_cup();

#endif