import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import ChessTrack from "./pages/ChessTrack";
import IotDashboard from "./pages/IotDashboard";
import PlayerPreferences from "./pages/PlayerPreferences";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/chesstrack" element={<ChessTrack />} />
        <Route path="/iot" element={<IotDashboard />} />
        <Route path="/preferences" element={<PlayerPreferences />} />
      </Routes>
    </Router>
  );
}

export default App;