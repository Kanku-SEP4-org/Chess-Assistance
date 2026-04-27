const grpc = require("@grpc/grpc-js");
const protoLoader = require("@grpc/proto-loader");
const path = require("path");

// ===================== LOAD SENSOR PROTO =====================
const sensorDef = protoLoader.loadSync(
  path.join(__dirname, "../../frontend/proto/sensor.proto"),
  {
    keepCase: true,
    longs: String,
    enums: String,
    defaults: true,
    oneofs: true,
  }
);

const sensorObject = grpc.loadPackageDefinition(sensorDef);
const sensorPackage = sensorObject.iot;

// ===================== LOAD MODEL PROTO =====================
const packageDef = protoLoader.loadSync(
  path.join(__dirname, "../../frontend/proto/model.proto"),
  {
    keepCase: true,
    longs: String,
    enums: String,
    defaults: true,
    oneofs: true,
  }
);

const grpcObject = grpc.loadPackageDefinition(packageDef);
const modelPackage = grpcObject.model || grpcObject;

// ===================== FUNCTIONS =====================

// Call Python ML API to get prediction
async function PredictWinrate(call, callback) {
  const { minutes_slept, minutes_awake } = call.request.condition;

  try {
    const response = await fetch("http://localhost:8000/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        minutes_slept,
        minutes_awake,
        temperature_celsius: 20, // Default value
        co2: 400, // Default value (ideal conditions)
        light: 500, // Default value
      }),
    });

    if (!response.ok) {
      throw new Error(`ML API error: ${response.status}`);
    }

    const mlResult = await response.json();
    const score = Math.round(mlResult.prediction * 100); // Convert to percentage

    callback(null, {
      predictionWinrate: score,
      isActive: score > 50,
      message: score > 50 ? "Good condition" : "Poor condition",
    });
  } catch (error) {
    console.error("Error calling ML API:", error);
    callback(error, null);
  }
}

// Current dummy: value: 25.5 + id
// Replace with: read from Arduino/MQTT/serial
function GetTemperature(call, callback) {
  const id = call.request.id;

  callback(null, {
    value: 25.5 + id,
    type: 1,
  });
}

// ===================== SERVER =====================
const server = new grpc.Server();

// Register existing service
server.addService(modelPackage.WinrateService.service, {
  PredictWinrate,
});

// 🔥 REGISTER NEW SERVICE
server.addService(sensorPackage.SensorService.service, {
  GetTemperature,
});

// Start server
server.bindAsync(
  "127.0.0.1:50051",
  grpc.ServerCredentials.createInsecure(),
  () => {
    console.log("gRPC server running on port 50051");
  }
);