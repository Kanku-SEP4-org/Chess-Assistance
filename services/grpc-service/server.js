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

// Current dummy: const score = Math.min(100, Math.floor(minutes_slept / 6));
// Replace with: call your Python ML API: const mlRes = await fetch('http://localhost:5000/predict', { ... });
function PredictWinrate(call, callback) {
  const { minutes_slept, minutes_awake } = call.request.condition;

  const score = Math.min(100, Math.floor(minutes_slept / 6));

  callback(null, {
    predictionWinrate: score,
    isActive: score > 50,
    message: score > 50 ? "Good condition" : "Poor condition",
  });
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