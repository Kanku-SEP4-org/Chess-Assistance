const express = require("express");
const cors = require("cors");
const grpc = require("@grpc/grpc-js");
const protoLoader = require("@grpc/proto-loader");
const path = require("path");

const app = express();
app.use(cors());
app.use(express.json());

const LOAD_OPTS = {
  keepCase: true,
  longs: String,
  enums: String,
  defaults: true,
  oneofs: true,
};

// ===================== LOAD SHARED PROTOS =====================
const malDef = protoLoader.loadSync(
  path.join(__dirname, "../shared/MAL.proto"),
  LOAD_OPTS
);
const malObject = grpc.loadPackageDefinition(malDef);
const malPackage = malObject.machine_learning;

const iotDef = protoLoader.loadSync(
  path.join(__dirname, "../shared/IoT.proto"),
  LOAD_OPTS
);
const iotObject = grpc.loadPackageDefinition(iotDef);
// package 'iotService' contains service 'iotService'
const IotServiceClient = iotObject.iotService.iotService;

// ===================== CLIENTS (→ grpc-service at :50051) =====================
const grpcHost = process.env.GRPC_HOST || "localhost";

const mlClient = new malPackage.WinrateService(
  `${grpcHost}:50051`,
  grpc.credentials.createInsecure()
);

const iotClient = new IotServiceClient(
  `${grpcHost}:50051`,
  grpc.credentials.createInsecure()
);

// ===================== HELPERS =====================

function getTemperature(arduinoId) {
  return new Promise((resolve) => {
    iotClient.getTemperature({ arduinoId }, (err, response) => {
      if (err || !response?.status?.success) {
        resolve(20); // fallback: 20°C
      } else {
        resolve(response.reading.value);
      }
    });
  });
}

// ===================== ENDPOINTS =====================

// POST /model/winrate/predict
// Body: { minutes_slept, minutes_awake, arduino_id }
// Orchestrates: fetches IoT temp, then calls ML Predict, returns dashboard-ready response
app.post("/model/winrate/predict", async (req, res) => {
  const { minutes_slept, minutes_awake, arduino_id } = req.body;

  try {
    const temperature = await getTemperature(Number(arduino_id) || 1);

    const prediction = await new Promise((resolve, reject) => {
      mlClient.Predict(
        {
          minutes_slept: Number(minutes_slept),
          minutes_awake: Number(minutes_awake),
          temperature_celsius: temperature,
          co2: 400,
          light: 0.5,
        },
        (err, response) => {
          if (err) reject(err);
          else resolve(response);
        }
      );
    });

    const winrate = Math.round(
      Math.max(0, Math.min(100, prediction.prediction * 100))
    );

    res.json({
      predictionWinrate: winrate,
      isActive: winrate > 50,
      message:
        winrate > 50 ? "Good condition for chess" : "Poor condition for chess",
    });
  } catch (err) {
    console.error("Predict error:", err);
    res.status(500).json({ error: "Prediction failed", details: err.message });
  }
});

// GET /iot/temp?id={arduinoId}
app.get("/iot/temp", (req, res) => {
  const arduinoId = parseInt(req.query.id) || 1;

  iotClient.getTemperature({ arduinoId }, (err, response) => {
    if (err) {
      console.error("IoT error:", err);
      return res.status(500).json({ error: "IoT request failed" });
    }

    res.json({
      value: response.reading?.value ?? 0,
      type: response.reading?.type ?? 0,
      timestamp: response.reading?.timestamp ?? 0,
      success: response.status?.success ?? false,
      message: response.status?.message ?? "",
    });
  });
});

// ===================== START =====================
app.listen(3001, () => {
  console.log("API Gateway running on port 3001");
});
