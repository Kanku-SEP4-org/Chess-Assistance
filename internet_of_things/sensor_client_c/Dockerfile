# Use a lightweight Ubuntu image with compilation tools
FROM ubuntu:22.04

# Avoid interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install gcc compiler, CMake, make, and the RabbitMQ development library
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    librabbitmq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Copy the entire C project into the container
COPY . .

# Create build directory, run CMake, and compile the binary
RUN mkdir -p build && \
    cd build && \
    cmake .. && \
    cmake --build .

# Inform Docker that the container listens on network port 2323 at runtime
EXPOSE 2323

# Run the compiled binary, and use '&& tail -f /dev/null' to force the container to stay alive forever
CMD ["sh", "-c", "./build/sensor_client && tail -f /dev/null"]