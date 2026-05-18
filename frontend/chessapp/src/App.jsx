import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import ChessTrack from "./pages/ChessTrack";
import IotDashboard from "./pages/IotDashboard";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/chesstrack" element={<ChessTrack />} />
        <Route path="/iot-dashboard" element={<IotDashboard />} />
      </Routes>
    </Router>
  );
}

export default App;