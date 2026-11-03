/* ═════════════════════════════════════════════════════════════════
   TUTOIA · Cliente de la API (FastAPI)
   ═════════════════════════════════════════════════════════════════ */

async function pedir(ruta, opciones = {}) {
  const respuesta = await fetch(ruta, opciones);
  if (!respuesta.ok) {
    let detalle = `Error ${respuesta.status}`;
    try {
      const cuerpo = await respuesta.json();
      detalle = typeof cuerpo.detail === "string" ? cuerpo.detail : detalle;
    } catch { /* sin cuerpo */ }
    throw new Error(detalle);
  }
  return respuesta.json();
}

export const api = {
  crearSesion: (datos) =>
    pedir("/api/sesiones", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(datos),
    }),

  iniciar: (sesionId) => pedir(`/api/sesiones/${sesionId}/iniciar`, { method: "POST" }),

  responder: (sesionId, texto) =>
    pedir(`/api/sesiones/${sesionId}/responder`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texto }),
    }),

  acta: (sesionId) => pedir(`/api/sesiones/${sesionId}/acta`, { method: "POST" }),
};
