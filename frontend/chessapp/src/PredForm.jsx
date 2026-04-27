function PredForm({
  sleepMinutes,
  setSleepMinutes,
  awakeMinutes,
  setAwakeMinutes,
  arduinoId,
  setArduinoId,
  handleSubmit,
  loading,
}) {
  return (
    <form onSubmit={handleSubmit}>
      <div className="mb-3">
        <label className="form-label">Sleep Duration (minutes)</label>
        <input
          type="number"
          className="form-control"
          value={sleepMinutes}
          onChange={(e) => setSleepMinutes(e.target.value)}
          min="0"
          required
        />
      </div>

      <div className="mb-3">
        <label className="form-label">Time Awake (minutes)</label>
        <input
          type="number"
          className="form-control"
          value={awakeMinutes}
          onChange={(e) => setAwakeMinutes(e.target.value)}
          min="0"
          required
        />
      </div>

      <div className="mb-3">
        <label className="form-label">Arduino ID</label>
        <input
          type="number"
          className="form-control"
          value={arduinoId}
          onChange={(e) => setArduinoId(e.target.value)}
          min="0"
          required
        />
      </div>

      <button type="submit" className="btn btn-primary w-100" disabled={loading}>
        {loading ? 'Loading...' : 'Get Prediction'}
      </button>
    </form>
  );
}

export default PredForm;