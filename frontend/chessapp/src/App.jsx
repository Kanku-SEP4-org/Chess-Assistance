import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import ChessTrack from "./pages/ChessTrack";
import IotDashboard from "./pages/IotDashboard";
import Login from "./pages/Login.jsx";
import Callback from "./pages/Callback";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/chesstrack" element={<ChessTrack />} />
        <Route path="/iot-dashboard" element={<IotDashboard />} />
        <Route path="/login" element={<Login />} />
        <Route path="/callback" element={<Callback />} />
      </Routes>
    </Router>
  );
}

export default App;