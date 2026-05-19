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
          light: 1500,
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

// POST /auth/lichess/callback
// Body: { code, code_verifier }
// Exchanges the Lichess authorization code for an access token,
// then fetches the authenticated Lichess account.
app.post("/auth/lichess/callback", async (req, res) => {
  const { code, code_verifier } = req.body;

  const clientId = process.env.LICHESS_CLIENT_ID || "chess-assistance";
  const redirectUri =
    process.env.LICHESS_REDIRECT_URI || "http://localhost:5173/callback";

  if (!code || !code_verifier) {
    return res.status(400).json({
      error: "Missing code or code_verifier",
    });
  }

  try {
    const tokenResponse = await fetch("https://lichess.org/api/token", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({
        grant_type: "authorization_code",
        code,
        redirect_uri: redirectUri,
        client_id: clientId,
        code_verifier,
      }),
    });

    if (!tokenResponse.ok) {
      const errorText = await tokenResponse.text();
      console.error("Lichess token exchange failed:", errorText);

      return res.status(500).json({
        error: "Lichess token exchange failed",
        details: errorText,
      });
    }

    const tokenData = await tokenResponse.json();
    const accessToken = tokenData.access_token;

    const accountResponse = await fetch("https://lichess.org/api/account", {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });

    if (!accountResponse.ok) {
      const errorText = await accountResponse.text();
      console.error("Lichess account fetch failed:", errorText);

      return res.status(500).json({
        error: "Lichess account fetch failed",
        details: errorText,
      });
    }

    const accountData = await accountResponse.json();

    res.json({
      player_username: accountData.username,
      player_id: accountData.id,
      lichess_token: accessToken,
    });
  } catch (err) {
    console.error("Lichess OAuth callback error:", err);

    res.status(500).json({
      error: "Lichess OAuth callback failed",
      details: err.message,
    });
  }
});

// ===================== START =====================
app.listen(3001, () => {
  console.log("API Gateway running on port 3001");
});
