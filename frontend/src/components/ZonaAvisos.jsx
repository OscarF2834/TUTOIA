/* ═════════════════════════════════════════════════════════════════
   TUTOIA · avisos flotantes (mini-bus de eventos global)
   ═════════════════════════════════════════════════════════════════ */
import { useEffect, useState } from "react";

const SUSCRITOS = new Set();

export function avisar(mensaje, ok = false) {
  const aviso = { id: Date.now() + Math.random(), mensaje, ok };
  SUSCRITOS.forEach((cb) => cb(aviso));
}

export default function ZonaAvisos() {
  const [avisos, setAvisos] = useState([]);

  useEffect(() => {
    const alta = (aviso) => {
      setAvisos((previos) => [...previos, aviso]);
      setTimeout(() => setAvisos((previos) => previos.filter((a) => a.id !== aviso.id)), 4500);
    };
    SUSCRITOS.add(alta);
    return () => SUSCRITOS.delete(alta);
  }, []);

  return (
    <>
      {avisos.map((a) => (
        <div key={a.id} className={`aviso-flotante${a.ok ? " correcto" : ""}`}>
          {a.ok ? "✓ " : "⚠ "}{a.mensaje}
        </div>
      ))}
    </>
  );
}
