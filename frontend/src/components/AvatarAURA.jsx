/* ═════════════════════════════════════════════════════════════════
   TUTOIA · <AvatarAURA />
   Avatar evaluador en SVG puro (sin dependencias de render 3D):
   · estados: idle · escuchando · pensando · hablando · saludo
   · parpadeo natural autónomo (2.4–4.6 s)
   · boca animada por rAF mientras la síntesis de voz está activa
   ═════════════════════════════════════════════════════════════════ */
import { useEffect, useRef } from "react";

const ESTADOS_VALIDOS = ["idle", "escuchando", "pensando", "hablando", "saludo"];

export default function AvatarAURA({ estado = "idle", hablando = false }) {
  const bocaRef = useRef(null);
  const ojoIzqRef = useRef(null);
  const ojoDerRef = useRef(null);
  const relojParpadeo = useRef(null);
  const marcoHabla = useRef(0);

  /* Parpadeo autónomo */
  useEffect(() => {
    const ciclo = () => {
      parpadear();
      relojParpadeo.current = setTimeout(ciclo, 2400 + Math.random() * 2200);
    };
    relojParpadeo.current = setTimeout(ciclo, 1600);
    return () => clearTimeout(relojParpadeo.current);
  }, []);

  function parpadear() {
    [ojoIzqRef.current, ojoDerRef.current].forEach((ojo) => {
      if (ojo) ojo.style.transform = "scaleY(0.08)";
    });
    setTimeout(() => {
      [ojoIzqRef.current, ojoDerRef.current].forEach((ojo) => {
        if (ojo) ojo.style.transform = "scaleY(1)";
      });
    }, 130);
  }

  /* Boca sincronizada mientras habla */
  useEffect(() => {
    if (hablando) {
      inicioBoca();
    } else {
      cancelAnimationFrame(marcoHabla.current);
      reposar();
    }
    return () => cancelAnimationFrame(marcoHabla.current);
  }, [hablando]);

  function pasoHabla() {
    if (!bocaRef.current) return;
    const t = performance.now() / 1000;
    const abertura = 3.2 + Math.abs(Math.sin(t * 11.5)) * 7.5 + Math.random() * 1.4;
    const anchura = 24 + Math.sin(t * 5.3) * 3.4;
    bocaRef.current.setAttribute("ry", abertura.toFixed(1));
    bocaRef.current.setAttribute("rx", anchura.toFixed(1));
    marcoHabla.current = requestAnimationFrame(pasoHabla);
  }

  function inicioBoca() {
    cancelAnimationFrame(marcoHabla.current);
    marcoHabla.current = requestAnimationFrame(pasoHabla);
  }

  function reposar() {
    if (!bocaRef.current) return;
    bocaRef.current.setAttribute("ry", "5.2");
    bocaRef.current.setAttribute("rx", "26");
  }

  const claseEstado = ESTADOS_VALIDOS.includes(estado) ? `estado-${estado}` : "estado-idle";

  return (
    <svg viewBox="0 0 420 480" className={`avatar-svg ${claseEstado}`} aria-label="Avatar AURA">
      <defs>
        <linearGradient id="auraCabeza" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#ffffff" />
          <stop offset="1" stopColor="#e8f3ed" />
        </linearGradient>
        <linearGradient id="auraCuerpo" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#d5ebdf" />
          <stop offset="1" stopColor="#f2faf6" />
        </linearGradient>
        <linearGradient id="auraPlaca" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#122c22" />
          <stop offset="1" stopColor="#1d4a38" />
        </linearGradient>
      </defs>

      {/* presencia: pulso + aro de energía */}
      <circle className="pulso-estado" cx="200" cy="205" r="168" />
      <circle className="aro-energia" cx="200" cy="205" r="182" />

      {/* el torso */}
      <path d="M 100 470 C 100 388, 148 352, 200 352 C 252 352, 300 388, 300 470 Z"
            fill="url(#auraCuerpo)" stroke="#b8d4c6" strokeWidth="2.5" />
      <circle className="nucleo" cx="200" cy="418" r="13" />
      <circle className="anillo-nucleo" cx="200" cy="418" r="19" fill="none" strokeWidth="2.5" strokeOpacity="0.6" />

      {/* la cabeza */}
      <circle cx="200" cy="205" r="112" fill="url(#auraCabeza)" stroke="#b8d4c6" strokeWidth="3" />

      {/* placa facial */}
      <rect x="122" y="142" width="156" height="128" rx="52"
            fill="url(#auraPlaca)" stroke="#2f6b55" strokeWidth="2" />

      {/* ojos */}
      <g ref={ojoIzqRef} className="ojo">
        <ellipse cx="163" cy="196" rx="17" ry="15" fill="#eafff5" />
        <circle cx="163" cy="196" r="7.5" fill="#0c1f18" />
        <circle cx="166" cy="192.5" r="2.6" fill="#a7f3d0" />
      </g>
      <g ref={ojoDerRef} className="ojo">
        <ellipse cx="237" cy="196" rx="17" ry="15" fill="#eafff5" />
        <circle cx="237" cy="196" r="7.5" fill="#0c1f18" />
        <circle cx="240" cy="192.5" r="2.6" fill="#a7f3d0" />
      </g>

      {/* cejas expresivas */}
      <path className="ceja ceja-izq"
            d="M 144 168 Q 163 158 182 167" fill="none"
            stroke="#9fdcc2" strokeWidth="5" strokeLinecap="round"
            transform-origin="163px 168px" />
      <path className="ceja ceja-der"
            d="M 218 167 Q 237 158 256 168" fill="none"
            stroke="#9fdcc2" strokeWidth="5" strokeLinecap="round"
            transform-origin="237px 167px" />

      {/* boca */}
      <ellipse ref={bocaRef} className="boca" cx="200" cy="244" rx="26" ry="5.2"
               fill="#eafff5" stroke="#3e8f72" strokeWidth="1.8" />

      {/* antena */}
      <line x1="200" y1="93" x2="200" y2="66" stroke="#7fb8a2" strokeWidth="4" strokeLinecap="round" />
      <circle cx="200" cy="60" r="7" fill="#b45309">
        <animate attributeName="opacity" values="1;.35;1" dur="2s" repeatCount="indefinite" />
      </circle>
    </svg>
  );
}
