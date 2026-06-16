#!/bin/bash
set -e
clear

# Navigate to the C code directory cleanly from root
cd internet_of_things/sensor_client_c

echo "========================================================"
echo "🔧 Configuring & Compiling C Sensor Client..."
echo "========================================================"

# Safely manage build directory state
mkdir -p linuxbuild
cd linuxbuild

# 1. Generate the compiler blueprints
cmake ..

# 2. CRITICAL FIX: Actually compile the binary executable layers!
cmake --build .

echo -e "\n========================================================"
echo "🛰️ Starting Native C Server on Port 2323..."
echo "========================================================"

# 3. Execute the resulting compiled native binary
./sensor_client

#remember to run `chmod +x launchSensorClientC.sh` in the terminal to make it executable.
#afterwards,in (!!!!) WSL terminal (!!!!), run the script with `./launchSensorClientC.sh`