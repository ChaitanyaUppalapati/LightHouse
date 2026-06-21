import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import App from "./App.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Me from "./pages/Me.jsx";
import "./index.css";

// Routing is set up now so later web tasks (S3 /me, S4 /inbox, S5 /bank) just add routes.
ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <Routes>
        <Route path="/" element={<App />}>
          <Route index element={<Dashboard />} />
          <Route path="me" element={<Me />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
