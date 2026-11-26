import { useEffect, useState } from "react";
import Landing from "./components/Landing";
import Sala from "./components/Sala";
import ZonaAvisos from "./components/ZonaAvisos";
import { Button } from "@/presentation/components/ui";
import FdcIngestionPage from "@/presentation/pages/FdcIngestionPage";

/* Navegación por hash (#/fdc, #/legacy, #/sala?s=<id>). */
export function vistaActual() {
  const hash = window.location.hash || "";
  if (hash.startsWith("#/sala")) {
    const query = hash.split("?")[1] || "";
    const sid = new URLSearchParams(query).get("s");
    if (sid) return { vista: "sala", sesionId: sid };
  }
  if (hash.startsWith("#/legacy")) {
    return { vista: "legacy" };
  }
  return { vista: "fdc" };
}

export function navegar(hash) {
  window.location.hash = hash;
}

export default function App() {
  const [ruta, setRuta] = useState(vistaActual);

  useEffect(() => {
    const alCambiar = () => setRuta(vistaActual());
    window.addEventListener("hashchange", alCambiar);
    return () => window.removeEventListener("hashchange", alCambiar);
  }, []);

  const isLegacy = ruta.vista === "legacy" || ruta.vista === "sala";

  return (
    <>
      <nav
        aria-label="Selector de entorno TutoIA"
        className="border-b border-slate-200 bg-white/95 px-4 py-2 text-xs text-slate-600"
      >
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-3">
          <span className="font-medium text-slate-500">
            TutoIA · Entorno de transición
          </span>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant={!isLegacy ? "primary" : "ghost"}
              onClick={() => navegar("#/fdc")}
            >
              Módulo 1 · Análisis FDC
            </Button>
            <Button
              size="sm"
              variant={isLegacy ? "secondary" : "ghost"}
              onClick={() => navegar("#/legacy")}
            >
              Prototipo Legacy (Sustentación)
            </Button>
          </div>
        </div>
      </nav>

      {ruta.vista === "sala" ? (
        <Sala key={ruta.sesionId} sesionId={ruta.sesionId} />
      ) : ruta.vista === "legacy" ? (
        <Landing />
      ) : (
        <FdcIngestionPage />
      )}
      <ZonaAvisos />
    </>
  );
}
