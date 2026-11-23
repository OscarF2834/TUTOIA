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

const PARTICULAS_FIJAS = [
  { left: "12%", bottom: "8%", delay: "0.4s", duration: "8.2s", background: "rgba(16,185,129,.55)" },
  { left: "24%", bottom: "26%", delay: "2.1s", duration: "10.5s", background: "rgba(13,148,136,.5)" },
  { left: "36%", bottom: "14%", delay: "4.6s", duration: "7.8s", background: "rgba(16,185,129,.55)" },
  { left: "48%", bottom: "32%", delay: "1.3s", duration: "11.4s", background: "rgba(13,148,136,.5)" },
  { left: "58%", bottom: "10%", delay: "5.8s", duration: "9.1s", background: "rgba(16,185,129,.55)" },
  { left: "69%", bottom: "22%", delay: "3.2s", duration: "12.0s", background: "rgba(13,148,136,.5)" },
  { left: "78%", bottom: "16%", delay: "6.7s", duration: "8.6s", background: "rgba(16,185,129,.55)" },
  { left: "86%", bottom: "30%", delay: "1.9s", duration: "10.1s", background: "rgba(13,148,136,.5)" },
  { left: "18%", bottom: "36%", delay: "7.4s", duration: "9.7s", background: "rgba(16,185,129,.55)" },
];

const esperar = (ms) => new Promise((r) => setTimeout(r, ms));

function reconstruirHistorial(estadoSesion) {
  const turnos = estadoSesion.turnos || [];
  const nombre = (estadoSesion.estudiante || "Sustentante").split(" ")[0];
  const nuevoRegistro = [];
  const nuevaTranscripcion = [];

  turnos.forEach((t, idx) => {
    nuevaTranscripcion.push({
      clase: "pregunta",
      texto: t.pregunta,
      eje_etiqueta: t.eje_etiqueta,
      tipo: t.tipo,
    });
    nuevaTranscripcion.push({
      clase: "respuesta",
      texto: t.respuesta,
      quien: nombre,
    });
    const sigTurno = turnos[idx + 1] || estadoSesion.pregunta_pendiente;
    const huboRefuerzo = Boolean(sigTurno && sigTurno.tipo === "seguimiento" && sigTurno.eje === t.eje);
    nuevoRegistro.push({
      nota_global: t.nota_global,
      criterios: t.criterios,
      tipo: t.tipo,
      eje: t.eje,
    });
    nuevaTranscripcion.push({
      clase: "evaluacion",
      evaluacion: {
        nota_global: t.nota_global,
        criterios: t.criterios,
        fortalezas: t.fortalezas,
        oportunidades: t.oportunidades,
        motor: t.motor,
        hubo_refuerzo: huboRefuerzo,
      },
    });
  });

  return { nuevoRegistro, nuevaTranscripcion };
}

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
  const montadoRef = useRef(true);
  const baseDictadoRef = useRef("");

  function marcarOcupado(valor) {
    ocupado.current = valor;
    setOcupadoUI(valor);
  }

  /* ═══ arranque: una sola vez por sesión ═══ */
  const arranqueHecho = useRef(false);
  useEffect(() => {
    montadoRef.current = true;
    if (!arranqueHecho.current) {
      arranqueHecho.current = true;
      arrancar();
    }
    return () => {
      montadoRef.current = false;
      detenerVoz();
      detenerEscucha();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function arrancar() {
    try {
      const estadoPrevio = await api.obtenerSesion(sesionId);
      if (!montadoRef.current) return;

      const tieneTurnos = Array.isArray(estadoPrevio.turnos) && estadoPrevio.turnos.length > 0;
      if (tieneTurnos) {
        const { nuevoRegistro, nuevaTranscripcion } = reconstruirHistorial(estadoPrevio);
        setRegistro(nuevoRegistro);
        setTranscripcion(nuevaTranscripcion);
      }

      if (estadoPrevio.estado === "finalizada") {
        setSesion({
          id: sesionId, tema: estadoPrevio.tema, estudiante: estadoPrevio.estudiante,
          enfoque: estadoPrevio.enfoque, total_preguntas: estadoPrevio.total_preguntas,
          motor: estadoPrevio.motor,
        });
        setFinalizada(true);
        const datosActa = await api.acta(sesionId);
        if (!montadoRef.current) return;
        setActa(datosActa);
        setBurbujaTexto(datosActa.guion_cierre.texto);
        setEscrito(true);
        setEstadoAvatar("idle");
        setTextoEstado(TEXTO_ESTADO.idle);
        marcarOcupado(false);
        return;
      }

      if (estadoPrevio.estado === "en_curso" && tieneTurnos && estadoPrevio.pregunta_pendiente) {
        setSesion({
          id: sesionId, tema: estadoPrevio.tema, estudiante: estadoPrevio.estudiante,
          enfoque: estadoPrevio.enfoque, total_preguntas: estadoPrevio.total_preguntas,
          motor: estadoPrevio.motor,
        });
        await presentarTurno(estadoPrevio.pregunta_pendiente);
        return;
      }

      const datos = await api.iniciar(sesionId);
      if (!montadoRef.current) return;
      setSesion({
        id: sesionId, tema: datos.tema, estudiante: datos.estudiante,
        enfoque: datos.enfoque, total_preguntas: datos.total_preguntas,
        motor: datos.motor,
      });

      setEstadoAvatar("saludo");
      await escribirMaquina(datos.apertura.texto);
      if (!montadoRef.current) return;
      setEstadoAvatar("hablando");
      setHablandoBoca(true);
      await hablar(datos.apertura.texto);
      if (!montadoRef.current) return;
      setHablandoBoca(false);

      await presentarTurno(datos.turno);
    } catch (error) {
      if (!montadoRef.current) return;
      console.error("[TUTOIA arrancar]", error && error.stack ? error.stack : error);
      avisar(error.message);
      setEstadoAvatar("idle"); setTextoEstado("Sin enlace");
      marcarOcupado(false);
    }
  }

  async function escribirMaquina(texto) {
    setEscrito(false);
    for (let i = 0; i < texto.length; i++) {
      if (!montadoRef.current) return;
      setBurbujaTexto(texto.slice(0, i + 1));
      if (".;".includes(texto[i])) await esperar(110);
      else if (",:".includes(texto[i])) await esperar(60);
      else await esperar(15);
      if (i % 3 === 2) await esperar(0);
    }
    if (!montadoRef.current) return;
    setBurbujaTexto(texto);
    setEscrito(true);
  }

  async function presentarTurno(turno) {
    if (!montadoRef.current || !turno) return;
    setTranscripcion((t) => [...t, {
      clase: "pregunta", texto: turno.texto,
      eje_etiqueta: turno.eje_etiqueta, tipo: turno.tipo,
    }]);
    setTextoEstado(TEXTO_ESTADO[turno.tipo === "seguimiento" ? "pensando" : "saludo"]);
    setEstadoAvatar(turno.tipo === "seguimiento" ? "pensando" : "saludo");
    await escribirMaquina(turno.texto);
    if (!montadoRef.current) return;

    setEstadoAvatar("hablando");
    setHablandoBoca(true);
    await hablar(turno.texto);
    if (!montadoRef.current) return;
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
    baseDictadoRef.current = "";
    setCampoRespuesta("");
    setEstadoAvatar("pensando"); setTextoEstado(TEXTO_ESTADO.pensando);
    setEscrito(false);
    setBurbujaTexto(REFLEXIONES[Math.floor(Math.random() * REFLEXIONES.length)]);

    const nombre = (sesion?.estudiante || "Sustentante").split(" ")[0];
    setTranscripcion((t) => [...t, { clase: "respuesta", texto, quien: nombre }]);

    try {
      const datos = await api.responder(sesionId, texto);
      if (!montadoRef.current) return;

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
      if (!montadoRef.current) return;
      avisar(error.message);
      setEstadoAvatar("idle"); setTextoEstado(TEXTO_ESTADO.idle);
      marcarOcupado(false);
    }
  }

  async function finalizarSustentacion() {
    if (!montadoRef.current) return;
    setEstadoAvatar("pensando"); setTextoEstado("Consolidando evaluación");
    setEscrito(false);
    setBurbujaTexto("Calculando tu evaluación consolidada…");
    setFinalizada(true);
    try {
      const datos = await api.acta(sesionId);
      if (!montadoRef.current) return;
      setActa(datos);
      detenerVoz();
      await escribirMaquina(datos.guion_cierre.texto);
      if (!montadoRef.current) return;
      setEstadoAvatar("hablando"); setHablandoBoca(true);
      await hablar(datos.guion_cierre.texto);
      if (!montadoRef.current) return;
      setHablandoBoca(false);
    } catch (error) {
      if (!montadoRef.current) return;
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
    baseDictadoRef.current = campoRespuesta.trim();
    setMicroactivo(true);
    setEstadoAvatar("escuchando"); setTextoEstado(TEXTO_ESTADO.escuchando);
    escuchar({
      onFinal: (texto) => {
        const fragmento = texto.trim();
        if (!fragmento) return;
        baseDictadoRef.current = (baseDictadoRef.current ? baseDictadoRef.current + " " : "") + fragmento;
        setCampoRespuesta(baseDictadoRef.current);
      },
      onParcial: (parcial) => {
        const prefijo = baseDictadoRef.current ? baseDictadoRef.current + " " : "";
        setCampoRespuesta(prefijo + parcial.trim());
      },
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
              onChange={(e) => {
                setCampoRespuesta(e.target.value);
                if (!microactivo) baseDictadoRef.current = e.target.value.trim();
              }}
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
  return (
    <>
      {PARTICULAS_FIJAS.map((p, i) => (
        <span key={i} className="particula" style={{
          left: p.left,
          bottom: p.bottom,
          animationDelay: p.delay,
          animationDuration: p.duration,
          background: p.background,
        }} />
      ))}
    </>
  );
}
