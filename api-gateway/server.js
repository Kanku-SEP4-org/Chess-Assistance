const express = require("express");
const cors = require("cors");
const jwt = require("jsonwebtoken");
const cookieParser = require("cookie-parser");
const grpc = require("@grpc/grpc-js");
const protoLoader = require("@grpc/proto-loader");
const path = require("path");
const { evaluateReadiness } = require("./services/readinessService");

const JWT_SECRET = process.env.JWT_SECRET || "dev-secret-change-in-production";
const COOKIE_NAME = "chess_session";
const tokenStore = new Map();

const app = express();
app.use(cookieParser());
app.use(cors({
  origin: process.env.FRONTEND_URL || "http://localhost:5173",
  credentials: true,
}));
app.use(express.json());
app.use(express.text({ type: "text/plain" }));

function requireAuth(req, res, next) {
  const token = req.cookies[COOKIE_NAME];
  if (!token) return res.status(401).json({ error: "Not authenticated" });

  try {
    req.player = jwt.verify(token, JWT_SECRET);
    next();
  } catch {
    res.clearCookie(COOKIE_NAME);
    return res.status(401).json({ error: "Session expired" });
  }
}

const LOAD_OPTS = {
  keepCase: true,
  longs: String,
  enums: String,
  defaults: true,
  oneofs: true,
};

// ===================== LOAD SHARED PROTOS =====================
const iotDef = protoLoader.loadSync(
  path.join(__dirname, "../shared/IoT.proto"),
  LOAD_OPTS
);
const iotObject = grpc.loadPackageDefinition(iotDef);
// package 'iotService' contains service 'iotService'
const IotServiceClient = iotObject.iotService.iotService;

const lichessDef = protoLoader.loadSync(
  path.join(__dirname, "../shared/LichessApi.proto"),
  LOAD_OPTS
);
const lichessObject = grpc.loadPackageDefinition(lichessDef);
const lichessPackage = lichessObject.lichess_api;

// ===================== CLIENTS =====================
const iotGrpcHost = process.env.IOT_GRPC_HOST || "localhost";
const iotGrpcPort = process.env.IOT_GRPC_PORT || "8080";

const lichessGrpcHost = process.env.LICHESS_GRPC_HOST || "localhost";
const lichessGrpcPort = process.env.LICHESS_GRPC_PORT || "8082";

const lichessClient = new lichessPackage.LichessService(
  `${lichessGrpcHost}:${lichessGrpcPort}`,
  grpc.credentials.createInsecure()
);

const iotClient = new IotServiceClient(
  `${iotGrpcHost}:${iotGrpcPort}`,
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

// GET /iot/light?id={arduinoId}
app.get("/iot/light", (req, res) => {
  const arduinoId = parseInt(req.query.id) || 1;

  iotClient.getLight({ arduinoId }, (err, response) => {
    if (err) {
      console.error("IoT light error:", err);
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

// ===================== ENDPOINTS =====================

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

// GET /iot/co2?id={arduinoId}
app.get("/iot/co2", (req, res) => {
  const arduinoId = parseInt(req.query.id) || 1;

  iotClient.getCO2({ arduinoId }, (err, response) => {
    if (err) {
      console.error("IoT CO2 error:", err);
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

    const registerResult = await new Promise((resolve, reject) => {
      lichessClient.RegisterPlayer(
        { lichess_id: accountData.id, username: accountData.username },
        (err, response) => {
          if (err) reject(err);
          else resolve(response);
        }
      );
    });

    const playerId = registerResult.player_id;

    tokenStore.set(playerId, {
      lichess_token: accessToken,
      player_username: accountData.username,
    });

    const jwtToken = jwt.sign(
      { player_id: playerId, player_username: accountData.username },
      JWT_SECRET,
      { expiresIn: "24h" }
    );

    res.cookie(COOKIE_NAME, jwtToken, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: 24 * 60 * 60 * 1000,
    });

    res.json({
      player_username: accountData.username,
      player_id: playerId,
    });
  } catch (err) {
    console.error("Lichess OAuth callback error:", err);

    res.status(500).json({
      error: "Lichess OAuth callback failed",
      details: err.message,
    });
  }
});

// GET /auth/me
app.get("/auth/me", requireAuth, (req, res) => {
  res.json({
    player_id: req.player.player_id,
    player_username: req.player.player_username,
  });
});

// POST /auth/lichess/logout
app.post("/auth/lichess/logout", requireAuth, async (req, res) => {
  const stored = tokenStore.get(req.player.player_id);

  if (stored) {
    try {
      await fetch("https://lichess.org/api/token", {
        method: "DELETE",
        headers: { Authorization: `Bearer ${stored.lichess_token}` },
      });
    } catch {}
    tokenStore.delete(req.player.player_id);
  }

  res.clearCookie(COOKIE_NAME);
  res.json({ success: true });
});

// POST /session/evaluate
app.post("/session/evaluate", (req, res) => {
  const { sleep_time, awaken_time, water_intake_ml } = req.body;

  if (!sleep_time || !awaken_time) {
    return res.status(400).json({ error: "Missing sleep_time or awaken_time" });
  }

  const result = evaluateReadiness({ sleep_time, awaken_time, water_intake_ml });
  res.json(result);
});

// POST /session/start
app.post("/session/start", requireAuth, async (req, res) => {
  const { sleep_time, awaken_time, confirmed_at, water_intake_initial_ml } = req.body;
  const { player_id, player_username } = req.player;

  const stored = tokenStore.get(player_id);
  if (!stored) {
    res.clearCookie(COOKIE_NAME);
    return res.status(401).json({ error: "Session expired — please log in again" });
  }

  try {
    const grpcRequest = {
      player_id: Number(player_id),
      player_username,
      lichess_token: stored.lichess_token,
      water_intake_initial_ml: Number(water_intake_initial_ml) || 0,
    };

    if (sleep_time)
      grpcRequest.sleep_time = {
        seconds: Math.floor(new Date(sleep_time).getTime() / 1000),
        nanos: 0,
      };
    if (awaken_time)
      grpcRequest.awaken_time = {
        seconds: Math.floor(new Date(awaken_time).getTime() / 1000),
        nanos: 0,
      };
    if (confirmed_at)
      grpcRequest.confirmed_at = {
        seconds: Math.floor(new Date(confirmed_at).getTime() / 1000),
        nanos: 0,
      };

    const result = await new Promise((resolve, reject) => {
      lichessClient.StartSession(grpcRequest, (err, response) => {
        if (err) reject(err);
        else resolve(response);
      });
    });

    if (!result.success) {
      return res.status(400).json({ success: false, message: result.message });
    }

    res.json({
      session_id: result.session_id,
      success: true,
      message: result.message,
    });
  } catch (err) {
    console.error("StartSession error:", err);
    res.status(500).json({ error: "StartSession failed", details: err.message });
  }
});

// POST /session/end
app.post("/session/end", async (req, res) => {
  let body = req.body;
  if (typeof body === "string") {
    try { body = JSON.parse(body); } catch { return res.status(400).json({ error: "Invalid body" }); }
  }
  const { session_id, water_drunk_during_session_ml } = body;

  if (!session_id) {
    return res.status(400).json({ error: "Missing session_id" });
  }

  try {
    const result = await new Promise((resolve, reject) => {
      lichessClient.EndSession(
        {
          session_id: Number(session_id),
          water_drunk_during_session_ml:
            Number(water_drunk_during_session_ml) || 0,
        },
        (err, response) => {
          if (err) reject(err);
          else resolve(response);
        }
      );
    });

    if (!result.success) {
      return res.status(400).json({ success: false, message: result.message });
    }

    res.json({ success: true, message: result.message });
  } catch (err) {
    console.error("EndSession error:", err);
    res.status(500).json({ error: "EndSession failed", details: err.message });
  }
});

// ===================== START =====================
app.listen(3001, () => {
  console.log("API Gateway running on port 3001");
});
