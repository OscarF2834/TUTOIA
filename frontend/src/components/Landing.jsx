/* ═════════════════════════════════════════════════════════════════
   TUTOIA · <Landing />
   Presentación + sala de configuración de la sustentación.
   ═════════════════════════════════════════════════════════════════ */
import { useState } from "react";
import { api } from "../lib/api";
import { avisar } from "./ZonaAvisos";
import AvatarAURA from "./AvatarAURA";
import { navegar } from "../App";

const PASOS = [
  { numero: "1", titulo: "Rúbrica integrada", detalle: "Pertinencia · Coherencia · Fundamentación teórica · Dominio metodológico, ponderados en la escala 0–5." },
  { numero: "2", titulo: "Diálogo adaptativo", detalle: "AURA pregunta eje por eje y profundiza con retro-preguntas cuando la argumentación se debilita." },
  { numero: "3", titulo: "Análisis en vivo", detalle: "El PLN evalúa la respuesta mientras el estudiante aún la dicta, con señales léxicas trazables." },
  { numero: "4", titulo: "Acta automática", detalle: "Reporte cuantitativo y cualitativo con radar, línea de tiempo y bandas cualitativas, listo en PDF." },
];

const PROGRAMAS = [
  "Ingeniería de Sistemas",
  "Ingeniería Electrónica",
  "Ingeniería Industrial",
  "Licenciatura en Informática",
  "Administración de Empresas",
  "Otro",
];

const DEMO = {
  estudiante: "Ana María Sofán Ruiz",
  enfoque: "Ingeniería de Sistemas",
  tema: "Plataforma inteligente de tutorías adaptativas basada en PLN para la gestión académica de la UTS",
  resumen:
    "El proyecto aborda la baja disponibilidad de tutorías personalizadas en la universidad mediante una plataforma que " +
    "recomienda itinerarios de aprendizaje adaptativos. Se aplicó una metodología iterativa con encuestas a 120 estudiantes " +
    "y se entrenó un modelo de clasificación en español sobre corpus académico, alcanzando una precisión del 87% en la " +
    "recomendación de recursos. El prototipo se validó con pruebas funcionales automatizadas y un análisis comparativo " +
    "entre las recomendaciones del sistema y las emitidas por docentes tutores, mostrando un 82% de concordancia.",
};

export default function Landing() {
  const [contenido, setContenido] = useState({
    estudiante: "", enfoque: PROGRAMAS[0], tema: "", resumen: "",
  });
  const [totalPreguntas, setTotalPreguntas] = useState(6);
  const [enviando, setEnviando] = useState(false);

  const cambiar = (campo) => (evento) =>
    setContenido({ ...contenido, [campo]: evento.target.value });

  async function abrirSala(evento) {
    evento.preventDefault();
    setEnviando(true);
    try {
      const datos = await api.crearSesion({ ...contenido, total_preguntas: totalPreguntas });
      navegar(`#/sala?s=${datos.sesion_id}`);
    } catch (error) {
      avisar(error.message);
      setEnviando(false);
    }
  }

  return (
    <div className="marco-landing">
      <header className="barra-superior">
        <div className="logo">T</div>
        <div className="logo-texto">TUTO<span>IA</span></div>
        <span className="chip"><span className="punto"></span> Motor IA conectado</span>
      </header>

      <section className="portada">
        <span className="etiqueta-badge">Unidades Tecnológicas de Santander · Periodo 2026</span>
        <h1>
          Sustentaciones de grado<br />
          <span className="destello">evaluadas por un avatar inteligente</span>
        </h1>
        <p>
          Tutoia conduce la sustentación de trabajos de grado mediante <b>procesamiento de lenguaje
          natural</b>: su avatar <b>AURA</b> formula las preguntas, analiza cada respuesta en tiempo
          real contra la rúbrica institucional y emite el acta del desempeño — al servicio del jurado humano.
        </p>

        <div className="pasos">
          {PASOS.map((paso) => (
            <div className="paso" key={paso.numero}>
              <span className="numero">{paso.numero}</span>
              <h3>{paso.titulo}</h3>
              <p>{paso.detalle}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="sala-config">
        <aside className="tarjeta panel-aura">
          <AvatarAURA estado="saludo" />
          <h2>AURA</h2>
          <div className="rol">Avatar Universitario para la Retroalimentación Académica</div>
          <p className="descripcion">
            Soy la evaluadora virtual de tu sustentación. Recibo tu <b>tema y resumen</b> con
            antelación, estructuro las preguntas por <b>ejes temáticos</b> y registro tu
            desempeño con la <b>rúbrica institucional</b> en cada respuesta.
          </p>
        </aside>

        <form className="tarjeta formulario-sustentacion" onSubmit={abrirSala}>
          <h2>Programar sustentación</h2>
          <p className="subtitulo">
            La información de la tesis alimenta el motor de PLN: cuanto más rica, más precisa la evaluación.
          </p>

          <div className="rejilla">
            <div className="grupo">
              <label htmlFor="estudiante">Sustentante</label>
              <input id="estudiante" required placeholder="Nombre completo del estudiante"
                     value={contenido.estudiante} onChange={cambiar("estudiante")} />
            </div>
            <div className="grupo">
              <label htmlFor="enfoque">Programa académico</label>
              <select id="enfoque" value={contenido.enfoque} onChange={cambiar("enfoque")}>
                {PROGRAMAS.map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
          </div>

          <div className="grupo">
            <label htmlFor="tema">Tema del trabajo de grado</label>
            <input id="tema" required placeholder="Ej.: Sistema adaptativo de tutorías basado en PLN…"
                   value={contenido.tema} onChange={cambiar("tema")} />
          </div>

          <div className="grupo">
            <label htmlFor="resumen">Resumen del trabajo (abstract)</label>
            <textarea id="resumen" required
                      placeholder="Incluye el problema, la metodología utilizada, resultados clave y conclusiones…"
                      value={contenido.resumen} onChange={cambiar("resumen")} />
            <p className="ayudita">
              Este texto es la referencia semántica contra la que se mide la cobertura y pertinencia de las respuestas.
            </p>
          </div>

          <div className="grupo selector-preguntas">
            <div>
              <label htmlFor="preguntas">Número de ejes temáticos</label>
              <input id="preguntas" type="range" min="3" max="6" step="1"
                     value={totalPreguntas}
                     onChange={(e) => setTotalPreguntas(Number(e.target.value))} />
            </div>
            <div className="escala-valor">{totalPreguntas}</div>
          </div>

          <div className="acciones-formulario">
            <button type="submit" className="btn btn-primario" disabled={enviando}>
              {enviando ? "Acondicionando la sala…" : "🛰️  Abrir sala de sustentación"}
            </button>
            <button type="button" className="btn btn-fantasma"
                    onClick={() => { setContenido(DEMO); setTotalPreguntas(6); }}>
              ⚡ Cargar caso demo
            </button>
          </div>
        </form>
      </section>

      <footer className="pie-landing">
        <b>TUTOIA</b> — plataforma inteligente con avatar evaluador para la automatización de
        sustentaciones de trabajos de grado mediante PLN.<br />
        Proyecto de grado · Unidades Tecnológicas de Santander · 2026
      </footer>
    </div>
  );
}
