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

// Calls Python ML API to get prediction
async function PredictWinrate(call, callback) {
  const { minutes_slept, minutes_awake } = call.request.condition;

  try {
    const mlApiHost = process.env.ML_API_HOST || 'localhost';
    const response = await fetch(`http://${mlApiHost}:8000/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        minutes_slept: minutes_slept,
        minutes_awake: minutes_awake,
        temperature_celsius: 20, // Default values for env factors
        co2: 400,
        light: 0.5
      })
    });

    if (!response.ok) {
      throw new Error(`ML API error: ${response.status}`);
    }

    const data = await response.json();
    const winrate = Math.max(0, Math.min(100, data.predictionWinrate));

    callback(null, {
      predictionWinrate: winrate,
      isActive: winrate > 50,
      message: winrate > 50 ? "Good condition for chess" : "Poor condition for chess",
    });
  } catch (error) {
    console.error('Prediction error:', error);
    callback({
      code: 14, // UNAVAILABLE
      details: `Failed to get prediction: ${error.message}`
    });
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
  "0.0.0.0:50051",
  grpc.ServerCredentials.createInsecure(),
  () => {
    console.log("gRPC server running on port 50051");
  }
);