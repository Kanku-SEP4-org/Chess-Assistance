function evaluateReadiness({ sleep_time, awaken_time, water_intake_ml }) {
  const now = new Date();
  const sleep = new Date(sleep_time);
  const wake = new Date(awaken_time);

  const sleepMinutes = Math.round((wake - sleep) / 60000);
  const sleepHours = sleepMinutes / 60;
  const awakeDurationHrs = (now - wake) / 3600000;
  const water = Number(water_intake_ml) || 0;

  const alerts = [];

  if (sleepHours < 5) {
    alerts.push({
      level: "red",
      message: `You only slept ${fmt(sleepMinutes)}. Consider resting first.`,
    });
  } else if (sleepHours < 7) {
    alerts.push({
      level: "yellow",
      message: `You slept ${fmt(sleepMinutes)} — not ideal but playable.`,
    });
  }

  if (awakeDurationHrs > 16) {
    alerts.push({
      level: "red",
      message: `You've been awake for ${Math.round(awakeDurationHrs)}h. Consider sleeping first.`,
    });
  } else if (awakeDurationHrs < 0.5) {
    alerts.push({
      level: "yellow",
      message: "You just woke up — give yourself time to fully wake up.",
    });
  }

  const expectedWater = Math.min(
    Math.floor(awakeDurationHrs / 2) * 250,
    2000
  );
  if (expectedWater > 0 && water < expectedWater) {
    alerts.push({
      level: "yellow",
      message: `You've had ${water}ml but have been awake ${Math.round(awakeDurationHrs)}h — consider drinking more (${expectedWater}ml recommended).`,
    });
  }

  return {
    alerts,
    sleep_duration: fmt(sleepMinutes),
    awake_duration: fmtHrs(awakeDurationHrs),
  };
}

function fmt(totalMinutes) {
  return `${Math.floor(totalMinutes / 60)}h ${totalMinutes % 60}m`;
}

function fmtHrs(hrs) {
  const h = Math.floor(hrs);
  const m = Math.round((hrs - h) * 60);
  return `${h}h ${m}m`;
}

module.exports = { evaluateReadiness };
