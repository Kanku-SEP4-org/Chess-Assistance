# Use Case: View Temperature

| Field             | Description |
|-------------------|-------------|
| **Use Case**      | View Temperature |
| **Summary**       | The system continuously polls and displays the current environmental temperature from the IoT sensor. The frontend auto-refreshes every 10 seconds and shows a comfort status based on the current value. The user may also navigate to the Environment Recommendation page to receive ML-based advice on optimal temperature for chess performance. |
| **Actor**         | Player |
| **Precondition**  | The player is logged in. The IoT service is running and connected to RabbitMQ. The IoT producer is publishing sensor readings to the `sensor.responses` queue. |
| **Postcondition** | The player sees the current temperature and a comfort status (Cool / Comfortable / Warm). Optionally, the player sees an ML recommendation to adjust temperature toward 20°C for improved win probability. |

## Base Sequence

1. Player opens the IoT Dashboard or Home page.
2. The frontend automatically sends `GET /iot/temp?id=1` to the API Gateway.
3. The API Gateway calls the IoT gRPC service (`getTemperature(arduinoId=1)`).
4. The IoT service retrieves the latest temperature value from its in-memory state store (populated continuously from RabbitMQ).
5. The API Gateway returns the value as a REST JSON response.
6. The frontend calculates the comfort status:
   - Below 18°C → **Cool**
   - 18–26°C → **Comfortable**
   - Above 26°C → **Warm**
7. The frontend displays the temperature (e.g., `22.3°C`) and the comfort status.
8. Steps 2–7 repeat automatically every 10 seconds while the player remains on the page.

## Alternate Sequences

**[ALT0]** At any point the player may navigate away, ending the polling loop.

**[ALT1]** Sensor data unavailable (state store empty):
1. The IoT service returns `value=0, success=false`.
2. The frontend displays **N/A** instead of a temperature value.

**[ALT2]** IoT service or API Gateway unreachable:
1. The HTTP request fails.
2. The frontend silently retries on the next 10-second interval.

**[ALT3]** Player navigates to Environment Recommendation page:
1. The current temperature is pre-filled from the latest sensor reading.
2. The player provides sleep and awake duration and submits the form.
3. The ML service calculates the current win probability and tests the effect of adjusting temperature to the optimal 20°C.
4. The frontend displays the recommended temperature and the expected win probability improvement.

## Notes

- Requirement 21
- Comfort status thresholds (Cool / Comfortable / Warm) are evaluated entirely in the frontend — no backend logic involved.
- ML recommendation optimal target is **20°C**, weighted at 30% alongside CO₂ (70%) in the environment score.
- Database recording of sensor values only occurs when the recording flag is active (separate use case).
- The `arduinoId` is currently hardcoded to `1` in the frontend.
