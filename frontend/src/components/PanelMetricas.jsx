/* ═════════════════════════════════════════════════════════════════
   TUTOIA · <PanelMetricas />
   Cuadro de mando en vivo: nota acumulada, barras por criterio y
   sucesión de ejes temáticos.
   ═════════════════════════════════════════════════════════════════ */
const CRITERIOS = [
  { os: "pertinencia", nombre: "Pertinencia" },
  { os: "coherencia", nombre: "Coherencia" },
  { os: "fundamentacion", nombre: "Fundamentación" },
  { os: "metodologia", nombre: "Metodología" },
];

const COD_EJES = ["contexto", "problema", "teoria", "metodo", "resultados", "aporte"];

function media(valores) {
  return valores.length ? valores.reduce((a, b) => a + b, 0) / valores.length : null;
}

export default function PanelMetricas({ registro, totalPreguntas }) {
  const conNota = registro.filter((r) => r.nota_global != null);
  const notaAcumulada = media(conNota.map((r) => r.nota_global));
  const ejesCompletados = new Set(
    registro.filter((r) => r.tipo === "principal").map((r) => r.eje)
  );
  const total = totalPreguntas || 6;

  return (
    <div className="tarjeta panel-metricas">
      <div className="cabecera-metricas">
        <h3>Análisis en tiempo real</h3>
        <div className="marcador-nota">
          <span className="valor">{notaAcumulada == null ? "–" : notaAcumulada.toFixed(1)}</span>
          <span className="tope">/ 5.0</span>
        </div>
      </div>

      <div className="barras-criterios">
        {CRITERIOS.map(({ os, nombre }) => {
          const puntajes = registro
            .map((r) => r.criterios?.[os]?.puntaje)
            .filter((v) => v != null);
          const mediaC = media(puntajes);
          return (
            <div className="criterio" key={os}>
              <span className="nombre">{nombre}</span>
              <div className="via">
                <div className="relleno"
                     style={{ width: `${mediaC == null ? 0 : (mediaC / 5) * 100}%` }} />
              </div>
              <span className="puntaje">{mediaC == null ? "–" : mediaC.toFixed(1)}</span>
            </div>
          );
        })}
      </div>

      <div className="sucesion-ejes">
        {Array.from({ length: total }, (_, i) => (
          <span key={i}
                className={
                  "eje" +
                  (i <= ejesCompletados.size - 1 ? " hecho" : "") +
                  (i === Math.min(ejesCompletados.size, total - 1) ? " actual" : "")
                } />
        ))}
      </div>
    </div>
  );
}
