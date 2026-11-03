import { useEffect, useState } from "react";
import Landing from "./components/Landing";
import Sala from "./components/Sala";
import ZonaAvisos from "./components/ZonaAvisos";

/* Navegación por hash (#/sala?s=<id>): sin servidor de rutas ni SPA-fallback. */
export function vistaActual() {
  const hash = window.location.hash || "";
  if (hash.startsWith("#/sala")) {
    const query = hash.split("?")[1] || "";
    const sid = new URLSearchParams(query).get("s");
    if (sid) return { vista: "sala", sesionId: sid };
  }
  return { vista: "landing" };
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

  return (
    <>
      {ruta.vista === "sala"
        ? <Sala key={ruta.sesionId} sesionId={ruta.sesionId} />
        : <Landing />}
      <ZonaAvisos />
    </>
  );
}
