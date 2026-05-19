#ifndef SENSOR_READER_H
#define SENSOR_READER_H

int read_temperature(float *temperature);
int read_light(short *light);
int read_pump_status(int *success);

#endif
