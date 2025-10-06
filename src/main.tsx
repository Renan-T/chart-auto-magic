import "./index.css"; // mantém seu estilo global

import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { PrefsProvider } from "./context/PrefsContext";

createRoot(document.getElementById("root")!).render(
  <PrefsProvider>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </PrefsProvider>
);
