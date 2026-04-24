/*****************************************************************************
 * interactive.c
 *  Interactive application file for the IoT hardware drivers demo.
 *  This file implements an interactive demo that allows you to test each
 *  driver.
 *  The demo presents a menu where you can select which driver to
 *  test.
 *  Connect a terminal (e.g. yat) to the board on uart0 and follow the
 *  instructions for each driver.
 * 
 *  Author:  Erland Larsen
 *  Date:    2026-03-17
 *  Project: SPE4_API
 *****************************************************************************/
#include <avr/io.h>
#include <util/delay.h>
#include <stdio.h>
#include <string.h>
#include <avr/interrupt.h>
#include "uart_stdio.h"
#include "led.h"
#include "pir.h"
#include "display.h"
#include "timer.h"
#include "wifi.h"
#include "button.h"
#include "buzzer.h"
#include "dht11.h"
#include "proximity.h"
#include "servo.h"
#include "adc.h"
#include "light.h"
#include "soil.h"
#include "tone.h"
//#include "adxl345.h"

#define MAX_STRING_LENGTH 100
#define MAX_MENU_OPTIONS 14

static int x = 0;
static char _q_buff[5] = {0};
static char _tmp_buff1[MAX_STRING_LENGTH] = {0};
static char _tmp_buff2[MAX_STRING_LENGTH] = {0};
static bool _tcp_string_received = false;
static bool _pir_active = false;

char welcome_text[] = "Welcome from SEP4 IoT hardware!\n";

uint8_t menu(void)
{
    int choice = 0;
    printf("\t----------------- M E N U ------------------\n");
    printf("\t 1. Button and LED\n");
    printf("\t 2. PIR Sensor (HC-SR501)\n");
    printf("\t 3. Display\n");
    printf("\t 4. WiFi (ESP8266)\n");
    printf("\t 5. stdio\n");
    printf("\t 6. Timer\n");
    printf("\t 7. Buzzer\n");
    printf("\t 8. Temperature and humiduty sensor (DHT11)\n");
    printf("\t 9. Proximity sensor (HC-SR04)\n");
    printf("\t10. Servo motor (SG90)\n");
    printf("\t11. Light sensor (KY-018)\n");
    printf("\t12. Soil Moisture Sensor ( capacitive )\n");
    printf("\t13. Play Star Wars theme on the speaker\n");
    printf("\t14. Show Accelerometer values (ADXL345)\n");

    printf("Choose a driver to test (1-%d): ", MAX_MENU_OPTIONS);
    do
    {
        scanf("%d", &choice);
        printf("%d\n", choice);
        if(choice < 1 || choice > MAX_MENU_OPTIONS)
        {
            // Invalid input, clear the input buffer
            while (getchar() != '\n')
                ;
            printf("Invalid input. Please enter a number between 1 and %d: ", MAX_MENU_OPTIONS);
        }
    } while (choice < 1 || choice > MAX_MENU_OPTIONS);
    return (uint8_t)choice;
}

static bool _quit()
{
    return (gets_nonblocking(_q_buff, sizeof(_q_buff)) > 0 && _q_buff[0] == 'q');
}

void pir_callback(void)
{
    if (_pir_active)
    {
        if (pir_get_state() == PIR_NO_MOTION)
        {
            led_off(1);
        }
        else
        {
            led_on(1);
        }
    }
}

void led2_callback(uint8_t id)
{
    static int8_t led_no = 2;
    led_toggle(led_no);
}

void start_stop_timer(uint8_t id)
{
    if (timer_get_state(id)) // Check if LED2 timer is active
        timer_pause(id);     // Pause the LED2 timer
    else
        timer_resume(id); // Resume the LED2 timer
}

void wifi_line_callback(const char *line)
{
    uint8_t _index;
    _index = strlen(_tmp_buff1);
    _tmp_buff1[_index] = '\r';
    _tmp_buff1[_index + 1] = '\n';
    _tmp_buff1[_index + 2] = '\0';
    _tcp_string_received = true;
}

int interactive_demo(void)
{
    static int led2_timer_id = 0;

    while (1)
    {
        switch (menu())
        {
        case 1:
            printf("Button and LED driver. Type 'q' to exit.\n");
            printf("LED 4 vill blink. Push a button to light one of the other LEDs.\n");
            led_blink(4, 500); // Blink LED4 with 500ms period
            do
            {
                (button_get(1)) ? led_on(1) : led_off(1);
                (button_get(2)) ? led_on(2) : led_off(2);
                (button_get(3)) ? led_on(3) : led_off(3);
                _delay_ms(200);
            } while (!_quit());
            led_off(4);
            break;
        case 2:
            _pir_active = true;
            printf("PIR sensor driver. Type 'q' to exit.\n");
            printf("LED 1 should turn on when motion is detected.\n");
            do
            {
                _delay_ms(200);
            } while (!_quit());
            _pir_active = false;
            break;
        case 3:
            printf("Display driver. Type 'q' to exit.\n");
            printf("Type a number between -999 and 9999\n");
            while (scanf("%d", &x) == 1)
            {
                display_setDecimals(1); // Set comma before least significant digit for demonstration
                display_int(x);
                printf("Du skrev: %d\n", x);
            }
            scanf("%*s"); // Clear invalid input from buffer
            break;
        case 4:
            printf("WiFi driver demo. Press Reset to exit.\n");
            printf("Enter WIFI SSID (max. 27 characters): ");
            while(getchar() != '\n') // Clear newline left in buffer from previous input
                ;
            gets(_tmp_buff1); puts(_tmp_buff1);            
            printf("Enter WIFI password (max. 27 characters): ");
            gets(_tmp_buff2); puts(_tmp_buff2);
            if(wifi_command_join_AP(_tmp_buff1, _tmp_buff2) != WIFI_OK)
            {
                printf("Failed to join WiFi network.\n");
                break;
            }
            else
            {
                printf("Successfully joined WiFi network.\n");
            }
            printf("Enter IP address of TCP server to connect to: ");
            gets(_tmp_buff1); puts(_tmp_buff1); // Reusing _tmp_buff1 to store the IP address

            WIFI_ERROR_MESSAGE_t message = wifi_command_create_TCP_connection(_tmp_buff1, 23, wifi_line_callback, _tmp_buff1);
            if( message != WIFI_OK)
            {
                printf("Failed to create TCP connection. %d\n", message);
                break;
            }
            else
            {
                printf("Successfully created TCP connection.\n");
            }
            wifi_command_TCP_transmit((uint8_t *)welcome_text, strlen(welcome_text));

            while (1)
            {
                if (_tcp_string_received)
                {
                    printf("TCP received: %s\n", _tmp_buff1);
                    _tmp_buff1[0] = '\0';
                    _tcp_string_received = false;
                }
                if (gets_nonblocking(_tmp_buff2, MAX_STRING_LENGTH) > 0)
                {
                    printf("You wrote: %s\n", _tmp_buff2);
                    wifi_command_TCP_transmit((uint8_t *)_tmp_buff2, strlen(_tmp_buff2));
                }
                _delay_ms(200);
            }
            break;
        case 5:
        {
            int ch;
            printf("stdio driver. Type a text to echo to the terminal.\n");
            while(getchar() != '\n') // Clear newline left in buffer from previous input
                ;
            do
            {
                ch = getchar();
                putchar(ch);
            } while (ch != '\n' && ch != EOF);
            break;
        }
        case 6:
            printf("Timer driver demo. Type 'q' to exit.\n");
            printf("LED 2 will toggle every 100ms. Pressing button 2 will pause/resume the blinking.\n");
            if ((led2_timer_id = timer_create_sw(led2_callback, 100)) < 0)
            {
                printf("Timer create failed\n");
                _delay_ms(2000);
                break;
            }
            do
            {
                if(button_get(2)) 
                {
                    start_stop_timer(led2_timer_id); // Call the start/stop callback to toggle the timer
                    _delay_ms(300); // Debounce delay
                }
            } while (!_quit());
            led_off(2);
            timer_delete(led2_timer_id);
            break;
        case 7:
            printf("Buzzer driver demo. Press button 2 to hear a beep. Type 'q' to exit.\n");
            do
            {
                if (button_get(2))
                {
                    buzzer_beep();  // Call the buzzer beep function
                    _delay_ms(200); // Debounce delay
                }
            } while (!_quit());
            break;
        case 8:
            printf("DHT11 driver demo. Type 'q' to exit.\n");
            printf("Temperature and humidity will be printed every 2 seconds.\n");
            do
            {
                uint8_t humidity_integer, humidity_decimal, temperature_integer, temperature_decimal;
                DHT11_ERROR_MESSAGE_t error = dht11_get(&humidity_integer, &humidity_decimal, &temperature_integer, &temperature_decimal);
                if (error == DHT11_OK)
                {
                    printf("Temperature: %d.%d°C, Humidity: %d.%d%%\n", temperature_integer, temperature_decimal, humidity_integer, humidity_decimal);
                }
                else
                {
                    printf("Failed to read DHT11 sensor data\n");
                }
                _delay_ms(2000); // Wait 2 seconds before next reading
            } while (!_quit());
            break;
        case 9:
            printf("Proximity sensor driver demo. Type 'q' to exit.\n");
            printf("Distance in mm will be printed every 2 seconds.\n");
            do
            {
                uint16_t distance = proximity_measure();
                if (distance == UINT16_MAX)
                {
                    printf("Proximity sensor timeout. No object detected within range.\n");
                }
                else
                {
                    printf("Distance: %d mm\n", distance);
                }
                _delay_ms(2000); // Wait 2 seconds before next reading
            } while (!_quit());
            break;
        case 10:
        {
            int angle;
            printf("Servo motor driver demo. Type 'q' to exit.\n");
            servo_start();
            printf("Enter angle (-90 to 90): ");
            while (scanf("%d", &angle) == 1)
            {
                if (angle < -90 || angle > 90)
                {
                    printf("Invalid angle. Please enter a value between -90 and 90.\n");
                }
                else
                {
                    servo_setAngle(PWM_A, (int8_t)angle);
                    servo_setAngle(PWM_B, (int8_t)angle);
                    printf("Servo set to %d degrees.\n", angle);
                }
            }
            servo_stop();
            scanf("%*s"); // Clear invalid input from buffer
            break;
        }
        case 11:
            printf("Light sensor driver demo. Type 'q' to exit.\n");
            printf("Light level will be printed every 2 seconds.\n");
            do
            {
                uint16_t light_level = light_measure_raw();
                if (light_level == UINT16_MAX)
                {
                    printf("Failed to read from light sensor. Make sure it is initialized correctly.\n");
                }
                else
                {
                    printf("Light level: %d (0-1023)\n", light_level);
                }
                _delay_ms(2000); // Wait 2 seconds before next reading
            } while (!_quit());
            break;
        case 12:
            printf("Soil moisture sensor driver demo. Type 'q' to exit.\n");
            printf("Soil moisture level will be measured on PK0 every 2 seconds.\n");
            do
            {
                uint16_t soil_moisture = soil_measure_raw(ADC_PK0);
                if (soil_moisture == UINT16_MAX)
                {
                    printf("Failed to read from soil moisture sensor. Make sure it is connected and initialized correctly.\n");
                }
                else
                {
                    printf("Soil moisture level: %d (0-1023)\n", soil_moisture);
                }
                _delay_ms(2000); // Wait 2 seconds before next reading
            } while (!_quit());
            break;
        case 13:
            printf("Playing Star Wars theme on the speaker. Press Reset to exit.\n");
            tone_play_starwars();
            break;
        case 14:
        {
            // int16_t x, y, z;
            // printf("ADXL345 Accelerometer demo. Type 'q' to exit.\n");
            // printf("X, Y, Z acceleration values will be printed every 2 seconds.\n");
            // do
            // {
            //     adxl345_read_xyz(&x, &y, &z);
            //     printf("Acceleration - X: %d, Y: %d, Z: %d\n", x, y, z);
            //     _delay_ms(2000); // Wait 2 seconds before next reading
            // } while (!_quit());
            break;
        }
        default:
            printf("Error: Invalid selection.\n");
            break;
        }
    }
    return 0;
}
