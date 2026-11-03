/* ═════════════════════════════════════════════════════════════════
   TUTOIA · <Sala />
   Máquina de estados de la sustentación en vivo:
   conectar → bienvenida → [pregunta → (dicta/escribe) → análisis]* → acta
   ═════════════════════════════════════════════════════════════════ */
import { useEffect, useRef, useState } from "react";
import { navegar } from "../App";
import { api } from "../lib/api";
import { avisar } from "./ZonaAvisos";
import AvatarAURA from "./AvatarAURA";
import PanelMetricas from "./PanelMetricas";
import FolioConversa from "./FolioConversa";
import { hablar, detenerVoz, conmutarSilencio, escuchar, detenerEscucha, SoporteSTT, saltarVoz } from "../lib/vozAula";

const TEXTO_ESTADO = {
  idle: "Atenta", escuchando: "Escuchando 👂",
  pensando: "Analizando ⚡", hablando: "Presentando 🗣️", saludo: "Bienvenida 🎓",
};

const REFLEXIONES = ["Analizando tu argumento…", "Contrastando con la rúbrica…", "Ponderando la evidencia…"];

const esperar = (ms) => new Promise((r) => setTimeout(r, ms));

export default function Sala({ sesionId }) {
  /* — datos del backend — */
  const [sesion, setSesion] = useState(null);
  const [registro, setRegistro] = useState([]);           // evaluaciones recibidas
  const [transcripcion, setTranscripcion] = useState([]); // folio visual
  const [acta, setActa] = useState(null);
  const [estadoAvatar, setEstadoAvatar] = useState("idle");
  const [textoEstado, setTextoEstado] = useState("Iniciando");
  const [hablandoBoca, setHablandoBoca] = useState(false);
  const [escrito, setEscrito] = useState(true);

  const [burbujaTexto, setBurbujaTexto] = useState("Estableciendo enlace con la plataforma…");
  const [campoRespuesta, setCampoRespuesta] = useState("");
  const [finalizada, setFinalizada] = useState(false);

  const [microactivo, setMicroactivo] = useState(false);
  const [mudo, setMudo] = useState(false);
  const ocupado = useRef(true);
  const [ocupadoUI, setOcupadoUI] = useState(true);

  function marcarOcupado(valor) {
    ocupado.current = valor;
    setOcupadoUI(valor);
  }

  /* ═══ arranque: una sola vez por sesión ═══ */
  const arranqueHecho = useRef(false);
  useEffect(() => {
    if (arranqueHecho.current) return;
    arranqueHecho.current = true;
    arrancar();
    return () => detenerVoz();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function arrancar() {
    try {
      const datos = await api.iniciar(sesionId);
      setSesion({
        id: sesionId, tema: datos.tema, estudiante: datos.estudiante,
        enfoque: datos.enfoque, total_preguntas: datos.total_preguntas,
        motor: datos.motor,
      });

      setEstadoAvatar("saludo");
      await escribirMaquina(datos.apertura.texto);
      setEstadoAvatar("hablando");
      setHablandoBoca(true);
      await hablar(datos.apertura.texto);
      setHablandoBoca(false);

      await presentarTurno(datos.turno);
    } catch (error) {
      console.error("[TUTOIA arrancar]", error && error.stack ? error.stack : error);
      avisar(error.message);
      setEstadoAvatar("idle"); setTextoEstado("Sin enlace");
      marcarOcupado(false);
    }
  }

  async function escribirMaquina(texto) {
    setEscrito(false);
    for (let i = 0; i < texto.length; i++) {
      setBurbujaTexto(texto.slice(0, i + 1));
      if (".;".includes(texto[i])) await esperar(110);
      else if (",:".includes(texto[i])) await esperar(60);
      else await esperar(15);
      if (i % 3 === 2) await esperar(0);
    }
    setBurbujaTexto(texto);
    setEscrito(true);
  }

  async function presentarTurno(turno) {
    setTranscripcion((t) => [...t, {
      clase: "pregunta", texto: turno.texto,
      eje_etiqueta: turno.eje_etiqueta, tipo: turno.tipo,
    }]);
    setTextoEstado(TEXTO_ESTADO[turno.tipo === "seguimiento" ? "pensando" : "saludo"]);
    setEstadoAvatar(turno.tipo === "seguimiento" ? "pensando" : "saludo");
    await escribirMaquina(turno.texto);

    setEstadoAvatar("hablando");
    setHablandoBoca(true);
    await hablar(turno.texto);
    setHablandoBoca(false);

    setEstadoAvatar("idle");
    setTextoEstado(TEXTO_ESTADO.idle);
    setMicroactivo(false);
    marcarOcupado(false);
  }

  /* ═══ envío de la respuesta ═══ */
  async function enviarRespuesta() {
    if (ocupado.current) return;
    const texto = campoRespuesta.trim();
    if (!texto) { avisar("Escribe o dicta tu respuesta antes de enviarla."); return; }
    if (texto.split(/\s+/).length < 4) { avisar("AURA necesita al menos 4 palabras para analizar la respuesta."); return; }

    marcarOcupado(true);
    detenerEscucha(); setMicroactivo(false);
    setCampoRespuesta("");
    setEstadoAvatar("pensando"); setTextoEstado(TEXTO_ESTADO.pensando);
    setEscrito(false);
    setBurbujaTexto(REFLEXIONES[Math.floor(Math.random() * REFLEXIONES.length)]);

    const nombre = (sesion?.estudiante || "Sustentante").split(" ")[0];
    setTranscripcion((t) => [...t, { clase: "respuesta", texto, quien: nombre }]);

    try {
      const datos = await api.responder(sesionId, texto);

      setRegistro((r) => [...r, {
        nota_global: datos.evaluacion.nota_global,
        criterios: datos.evaluacion.criterios,
        tipo: datos.turno.tipo,
        eje: datos.turno.eje,
      }]);
      setTranscripcion((t) => [...t, { clase: "evaluacion", evaluacion: datos.evaluacion }]);

      if (datos.cierre) {
        await finalizarSustentacion();
      } else {
        await presentarTurno(datos.siguiente);
      }
    } catch (error) {
      avisar(error.message);
      setEstadoAvatar("idle"); setTextoEstado(TEXTO_ESTADO.idle);
      marcarOcupado(false);
    }
  }

  async function finalizarSustentacion() {
    setEstadoAvatar("pensando"); setTextoEstado("Consolidando evaluación");
    setEscrito(false);
    setBurbujaTexto("Calculando tu evaluación consolidada…");
    setFinalizada(true);
    try {
      const datos = await api.acta(sesionId);
      setActa(datos);
      detenerVoz();
      await escribirMaquina(datos.guion_cierre.texto);
      setEstadoAvatar("hablando"); setHablandoBoca(true);
      await hablar(datos.guion_cierre.texto);
      setHablandoBoca(false);
    } catch (error) {
      avisar(error.message);
    }
  }

  /* ═══ micrófono ═══ */
  function alternarMicro() {
    if (microactivo) {
      detenerEscucha(); setMicroactivo(false);
      if (!ocupado.current) { setEstadoAvatar("idle"); setTextoEstado(TEXTO_ESTADO.idle); }
      return;
    }
    if (!SoporteSTT) { avisar("Voz no disponible en este navegador: usa Chrome o Edge."); return; }
    setMicroactivo(true);
    setEstadoAvatar("escuchando"); setTextoEstado(TEXTO_ESTADO.escuchando);
    escuchar({
      onFinal: (texto) => setCampoRespuesta((previo) => (previo ? previo.trim() + " " : "") + texto.trim()),
      onParcial: (parcial) => setCampoRespuesta(parcial),
      onError: (mensaje) => {
        avisar(mensaje);
        setMicroactivo(false);
        if (!ocupado.current) { setEstadoAvatar("idle"); setTextoEstado(TEXTO_ESTADO.idle); }
      },
    });
  }

  function alternarMudo() {
    const silencio = conmutarSilencio();
    setMudo(silencio);
    avisar(silencio ? "Voz de AURA silenciada." : "Voz de AURA activada.", true);
  }

  /* ═══ render ═══ */
  if (!sesion) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", flexDirection: "column", gap: 16 }}>
        <AvatarAURA estado="pensando" />
        <p style={{ color: "var(--texto-suave)" }}>Acondicionando la sala de sustentación…</p>
      </div>
    );
  }

  const tecladoEnter = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); enviarRespuesta(); }
  };

  return (
    <div className="marco-sala">
      <header className="barra-sala">
        <div className="logo">T</div>
        <div className="identidad">
          <b>{sesion.tema}</b>
          <span>{sesion.estudiante} · {sesion.enfoque}</span>
        </div>
        <span className="chip"><span className="punto" /> Motor: {sesion.motor}</span>
        <button className="btn btn-fantasma" onClick={alternarMudo} title="Silenciar la voz de AURA">
          {mudo ? "🔇" : "🔊"}
        </button>
        <button className="btn btn-fantasma" onClick={() => navegar("#/")}>⌂ Salir</button>
      </header>

      <main className="pizarra-sala">
        <section className="escenario">
          <div className="escenario-avatar">
            <AuraConParticulas estado={estadoAvatar} hablando={hablandoBoca} />
          </div>

          <div className={`burbuja-aura${escrito ? " escrito" : ""}`}>
            <span className="quien-habla">AURA · Avatar evaluador</span>
            <p className="texto">{burbujaTexto}</p>
          </div>

          <div className="estado-herramientas">
            <span className="badge-estado">
              <span className="punto" />
              <span>{textoEstado || TEXTO_ESTADO[estadoAvatar]}</span>
            </span>
            {hablandoBoca && (
              <button className="btn btn-fantasma" onClick={() => saltarVoz()} title="Omitir el audio y continuar">
                ⏭ Saltar voz
              </button>
            )}
          </div>
        </section>

        <section className="columna-flujo">
          <PanelMetricas registro={registro} totalPreguntas={sesion.total_preguntas} />

          <FolioConversa transcripcion={transcripcion} contador={registro.length} />

          <div className="compositor">
            <button
              className={`boton-microfono${microactivo ? " activo" : ""}`}
              onClick={alternarMicro}
              disabled={finalizada || ocupadoUI}
              title="Dictar la respuesta con la voz">
              {microactivo ? "⏹" : "🎙️"}
            </button>
            <textarea
              value={campoRespuesta}
              onChange={(e) => setCampoRespuesta(e.target.value)}
              onKeyDown={tecladoEnter}
              placeholder="Habla con AURA presionando el micrófono, o escribe aquí tu respuesta…"
              disabled={finalizada || ocupadoUI}>
            </textarea>
            <button className="btn btn-primario" onClick={enviarRespuesta}
                    disabled={finalizada || ocupadoUI}>
              Aceptar&nbsp;➤
            </button>
            <div className="aviso-detalle">
              {finalizada
                ? "Sustentación finalizada: el acta está lista."
                : "Responde también escribiendo; AURA analiza las dos formas."}
            </div>
          </div>
        </section>
      </main>

      {acta && (
        <div className="corto-velo">
          <div className="ventana-nota">
            <div className="anillo-nota">Evaluación consolidada</div>
            <div className="gran-nota">
              {Number(acta.nota_final).toFixed(1)}<small> / 5.0</small>
            </div>
            <div className="banda">{acta.banda}</div>
            <p>
              El acta con el análisis por criterios, gráficas y detalle pregunta por pregunta
              ya está lista para tu jurado.
            </p>
            <div className="acciones">
              <a className="btn btn-orolinea" href={acta.acta_url} target="_blank" rel="noreferrer">
                📊 Abrir acta
              </a>
              <button className="btn btn-fantasma" onClick={() => navegar("#/")}>Nueva sustentación</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* Partículas de polvo holográfico detrás del avatar */
function AuraConParticulas({ estado, hablando }) {
  return (
    <>
      <Particulas />
      <AvatarAURA estado={estado} hablando={hablando} />
    </>
  );
}

function Particulas() {
  const cantidad = 9;
  return (
    <>
      {Array.from({ length: cantidad }, (_, i) => {
        const tono = i % 2 ? "rgba(13,148,136,.5)" : "rgba(16,185,129,.55)";
        return (
          <span key={i} className="particula" style={{
            left: `${8 + Math.random() * 84}%`,
            bottom: `${Math.random() * 40}%`,
            animationDelay: `${(Math.random() * 9).toFixed(1)}s`,
            animationDuration: `${(7 + Math.random() * 6).toFixed(1)}s`,
            background: tono,
          }} />
        );
      })}
    </>
  );
}
