import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import ChessTrack from "./pages/ChessTrack";
import IotDashboard from "./pages/IotDashboard";
import Login from "./pages/Login.jsx";
import Callback from "./pages/Callback";
import PlayerPreference from "./pages/PlayerPreference";
import AngrinessPredictor from "./pages/AngrinessPredictor";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/chesstrack" element={<ChessTrack />} />
        <Route path="/angriness" element={<AngrinessPredictor />} />
        <Route path="/iot-dashboard" element={<IotDashboard />} />
        <Route path="/login" element={<Login />} />
        <Route path="/callback" element={<Callback />} />
         <Route path="/preferences" element={<PlayerPreference />} />
      </Routes>
    </Router>
  );
}

export default App;