#ifndef SENSOR_READER_H
#define SENSOR_READER_H

int read_temperature(float *temperature);
int read_water(int *water);
int read_light(short *light);
int fill_cup(int *success);

#endif