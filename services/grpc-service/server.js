const grpc = require("@grpc/grpc-js");
const protoLoader = require("@grpc/proto-loader");
const path = require("path");

const LOAD_OPTS = {
  keepCase: true,
  longs: String,
  enums: String,
  defaults: true,
  oneofs: true,
};

// ===================== LOAD SHARED PROTOS =====================
const malDef = protoLoader.loadSync(
  path.join(__dirname, "../../shared/MAL.proto"),
  LOAD_OPTS
);
const malObject = grpc.loadPackageDefinition(malDef);
const malPackage = malObject.machine_learning;

const iotDef = protoLoader.loadSync(
  path.join(__dirname, "../../shared/IoT.proto"),
  LOAD_OPTS
);
const iotObject = grpc.loadPackageDefinition(iotDef);
// package 'iotService' contains service 'iotService'
const IotServiceClient = iotObject.iotService.iotService;

// ===================== IoT CLIENT (→ C# IoT gRPC service) =====================
const iotHost = process.env.IOT_HOST || "localhost";
const iotPort = process.env.IOT_PORT || "5143";
const iotClient = new IotServiceClient(
  `${iotHost}:${iotPort}`,
  grpc.credentials.createInsecure()
);

// ===================== WinrateService.Predict =====================
async function Predict(call, callback) {
  const { minutes_slept, minutes_awake, temperature_celsius, co2, light } =
    call.request;

  try {
    const mlApiHost = process.env.ML_API_HOST || "localhost";
    const response = await fetch(`http://${mlApiHost}:8000/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        minutes_slept,
        minutes_awake,
        temperature_celsius,
        co2,
        light,
      }),
    });

    if (!response.ok) throw new Error(`ML API error: ${response.status}`);

    const data = await response.json();
    callback(null, { prediction: data.prediction });
  } catch (error) {
    console.error("Predict error:", error);
    callback({ code: grpc.status.UNAVAILABLE, details: error.message });
  }
}

async function PredictMock(call, callback) {
  callback(null, { prediction: 0.5 });
}

// ===================== iotService.getTemperature =====================
function getTemperature(call, callback) {
  iotClient.getTemperature(
    { arduinoId: call.request.arduinoId },
    (err, response) => {
      if (err) {
        console.error("IoT gRPC error:", err.message);
        callback(null, {
          reading: { value: 0, type: "temp", timestamp: 0 },
          status: { success: false, message: err.message },
        });
      } else {
        callback(null, response);
      }
    }
  );
}

// ===================== SERVER =====================
const server = new grpc.Server();

server.addService(malPackage.WinrateService.service, { Predict, PredictMock });
server.addService(IotServiceClient.service, { getTemperature });

server.bindAsync(
  "0.0.0.0:50051",
  grpc.ServerCredentials.createInsecure(),
  () => {
    console.log("gRPC server running on port 50051");
  }
);
