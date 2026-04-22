const express = require("express");
const grpc = require("@grpc/grpc-js");
const protoLoader = require("@grpc/proto-loader");
const path = require("path");

const app = express();
app.use(express.json());

// ===================== LOAD MODEL PROTO =====================
const packageDef = protoLoader.loadSync(
  path.join(__dirname, "../proto/model.proto"),
  {
    keepCase: true,
    longs: String,
    enums: String,
    defaults: true,
    oneofs: true,
  }
);

const grpcObject = grpc.loadPackageDefinition(packageDef);
const modelPackage = grpcObject.model;

// ===================== LOAD SENSOR PROTO =====================
const sensorDef = protoLoader.loadSync(
  path.join(__dirname, "../proto/sensor.proto"),
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

// ===================== CLIENTS =====================

// Winrate client
const client = new modelPackage.WinrateService(
  "localhost:50051",
  grpc.credentials.createInsecure()
);

// Sensor client
const sensorClient = new sensorPackage.SensorService(
  "localhost:50051",
  grpc.credentials.createInsecure()
);

// ===================== ENDPOINTS =====================

// Existing endpoint
app.post("/model/winrate/predict", (req, res) => {
  client.PredictWinrate(req.body, (err, response) => {
    if (err) {
      console.error(err);
      return res.status(500).send("gRPC error");
    }

    res.json(response);
  });
});

// 🔥 NEW IoT endpoint
app.get("/iot/temp", (req, res) => {
  const id = parseInt(req.query.id);

  sensorClient.GetTemperature({ id }, (err, response) => {
    if (err) {
      console.error(err);
      return res.status(500).send("gRPC error");
    }

    res.json(response);
  });
});

// ===================== START SERVER =====================
app.listen(3000, () => {
  console.log("API Gateway running on port 3000");
});