import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import ChessTrack from "./pages/ChessTrack";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/chesstrack" element={<ChessTrack />} />
      </Routes>
    </Router>
  );
}

export default App;