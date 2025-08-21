import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import App from "./App";

const root = ReactDOM.createRoot(document.getElementById("root"));
import { Toaster } from "./components/ui/toaster";
root.render(
  <React.StrictMode>
    <Toaster />
    <App />
  </React.StrictMode>,
);
