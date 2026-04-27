function PredForm({
  sleepMinutes,
  setSleepMinutes,
  awakeMinutes,
  setAwakeMinutes,
  arduinoId,
  setArduinoId,
  mockMode,
  setMockMode,
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

      <div className="form-check mb-3">
        <input
          className="form-check-input"
          type="checkbox"
          id="mockMode"
          checked={mockMode}
          onChange={(e) => setMockMode(e.target.checked)}
        />
        <label className="form-check-label text-muted" htmlFor="mockMode">
          Use mock data (API not ready)
        </label>
      </div>

      <button type="submit" className="btn btn-primary w-100" disabled={loading}>
        {loading ? 'Loading...' : 'Get Prediction'}
      </button>
    </form>
  );
}

export default PredForm;