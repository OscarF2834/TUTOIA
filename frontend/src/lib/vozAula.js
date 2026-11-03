/* ═════════════════════════════════════════════════════════════════
   TUTOIA · vozAula
   Envoltura de la Web Speech API del navegador (nativa, sin costo):
   · hablar(texto) → síntesis de voz en español (TTS)
   · escuchar(...) → reconocimiento de voz continuo (STT)
   Módulo único de sesión: el navegador es el proveedor de voz.
   ═════════════════════════════════════════════════════════════════ */

let vozEscogida = null;
let silencio = false;
let reconocimiento = null;

function prepararVoz() {
  if (!("speechSynthesis" in window)) return;
  const asignar = () => {
    const voces = speechSynthesis.getVoices();
    vozEscogida =
      voces.find((v) => v.lang.toLowerCase().replace("_", "-") === "es-co") ||
      voces.find((v) => /^(es)[-_/]/i.test(v.lang) && /lat[a|i]n|am(e|é)rica|colombia/i.test(v.name)) ||
      voces.find((v) => v.lang.toLowerCase().startsWith("es")) ||
      null;
  };
  asignar();
  speechSynthesis.onvoiceschanged = asignar;
}
prepararVoz();

let resolverPendiente = null;

/* ── Síntesis (TTS) ──────────────────────────────────────────────── */
export function hablar(texto) {
  return new Promise((resolver) => {
    if (!texto) { resolver(); return; }
    detenerVoz();
    resolverPendiente = resolver;
    if (!("speechSynthesis" in window) || silencio) {
      // Fallback estimado por longitud: el ritmo de la conversación se sostiene
      resolverTras(texto.length * 42).then(() => resolver());
      return;
    }
    const fragmento = new SpeechSynthesisUtterance(texto);
    if (vozEscogida) fragmento.voice = vozEscogida;
    fragmento.lang = vozEscogida ? vozEscogida.lang : "es-ES";
    fragmento.rate = 1.02;
    fragmento.pitch = 1.0;
    fragmento.onend = () => resolver();
    fragmento.onerror = () => resolver();
    // Guardia anti-bloqueo: navegadores sin voces instaladas nunca
    // disparan onend; la conversación no puede quedarse congelada.
    resolverTras(Math.min(30000, 2500 + texto.length * 45)).then(() => resolver());
    try {
      speechSynthesis.speak(fragmento);
    } catch {
      resolverTras(texto.length * 42).then(() => resolver());
    }
  });
}

/* Interacción maestra: omite el turno hablado (uso en demo o sin sonido) */
export function saltarVoz() {
  detenerVoz();
  if (resolverPendiente) { const r = resolverPendiente; resolverPendiente = null; r(); return true; }
  return false;
}

export function detenerVoz() {
  if ("speechSynthesis" in window) speechSynthesis.cancel();
}

export function conmutarSilencio() {
  silencio = !silencio;
  if (silencio) detenerVoz();
  return silencio;
}

/* ── Reconocimiento (STT) ────────────────────────────────────────── */
export const SoporteSTT = Boolean(window.SpeechRecognition || window.webkitSpeechRecognition);

export function escuchar({ onFinal, onParcial, onError } = {}) {
  if (!SoporteSTT) {
    onError?.("El navegador no soporta reconocimiento de voz (usa Chrome o Edge).");
    return;
  }
  detenerEscucha();
  const Motor = window.SpeechRecognition || window.webkitSpeechRecognition;
  reconocimiento = new Motor();
  reconocimiento.lang = "es-CO";
  reconocimiento.interimResults = true;
  reconocimiento.continuous = true;
  reconocimiento.maxAlternatives = 1;

  reconocimiento.onresult = (evento) => {
    let parcial = "";
    for (let i = evento.resultIndex; i < evento.results.length; i++) {
      const transcripcion = evento.results[i][0].transcript;
      if (evento.results[i].isFinal) onFinal?.(transcripcion);
      else parcial += transcripcion;
    }
    if (parcial) onParcial?.(parcial);
  };

  reconocimiento.onerror = (evento) => {
    onError?.(
      evento.error === "not-allowed"
        ? "Permiso de micrófono denegado: habilítalo en el navegador."
        : `Error de escucha: ${evento.error}`
    );
  };

  try { reconocimiento.start(); } catch { onError?.("No fue posible iniciar el micrófono."); }
}

export function detenerEscucha() {
  if (reconocimiento) {
    try { reconocimiento.stop(); } catch { /* ya detenido */ }
    reconocimiento = null;
  }
}

/* ── Ayudantes ───────────────────────────────────────────────────── */
function resolverTras(ms) {
  return new Promise((r) => setTimeout(r, ms));
}
