/* ═════════════════════════════════════════════════════════════════
   TUTOIA · <FolioConversa />
   Acta de lo sucedido: preguntas de AURA, respuestas del sustentante
   y tarjetas de evaluación automática — con autoscroll.
   ═════════════════════════════════════════════════════════════════ */
import { useEffect, useRef } from "react";

const escapar = (texto) =>
  String(texto).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );

function Literal({ item }) {
  if (item.clase === "pregunta") {
    return (
      <div className="cabos pregunta">
        <span className="quien">AURA pregunta</span>
        <div className="burbuja-texto">{item.texto}</div>
        <span className="tag-eje">
          {item.eje_etiqueta}{item.tipo === "seguimiento" ? " · refuerzo" : ""}
        </span>
      </div>
    );
  }

  if (item.clase === "respuesta") {
    return (
      <div className="cabos respuesta">
        <span className="quien">{item.quien} responde</span>
        <div className="burbuja-texto">{item.texto}</div>
      </div>
    );
  }

  const criterios = Object.values(item.evaluacion?.criterios || {});
  const necesitaRefuerzo = criterios.some((c) => c.puntaje < 2.5);
  const fortalezas = (item.evaluacion?.fortalezas || []).slice(0, 2);
  const oportunidades = (item.evaluacion?.oportunidades || []).slice(0, 2);

  return (
    <div className="tarjeta-evaluacion">
      <div className="linea-arriba">
        <b>Módulo analítico de PLN</b>
        <span className="chip-nota">{(item.evaluacion.nota_global ?? 0).toFixed(1)}</span>
      </div>
      <ul>
        {fortalezas.map((x, i) => <li key={`f${i}`} className="fortaleza">✓ {x}</li>)}
        {oportunidades.map((x, i) => <li key={`o${i}`} className="oportunidad">▲ {x}</li>)}
        {fortalezas.length === 0 && oportunidades.length === 0 && (
          <li className="fortaleza">✓ Sin alertas: continúa con este nivel.</li>
        )}
      </ul>
      {necesitaRefuerzo && <div className="refuerzo">AURA profundizará este eje antes de avanzar.</div>}
    </div>
  );
}

export default function FolioConversa({ transcripcion, contador }) {
  const flujoRef = useRef(null);

  useEffect(() => {
    if (flujoRef.current) flujoRef.current.scrollTop = flujoRef.current.scrollHeight;
  }, [transcripcion.length]);

  return (
    <div className="folio-transcripcion">
      <div className="cabecera-folio">
        📜 Acta de lo sucedido
        <span className="turno-co">Turno {contador}</span>
      </div>
      <div className="flujo-conversa" ref={flujoRef}>
        {transcripcion.length === 0 && (
          <p style={{ color: "var(--texto-tenue)", fontSize: 13 }}>
            La transcripción de la sustentación aparecerá aquí.
          </p>
        )}
        {transcripcion.map((item, i) => <Literal key={i} item={item} />)}
      </div>
    </div>
  );
}
