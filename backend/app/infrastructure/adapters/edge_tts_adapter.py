"""Adaptador TTS neuronal colombiano con edge-tts y decorador de respaldo."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

from app.domain.exceptions.fdc_exceptions import AiProviderUnavailableError, FdcDomainError
from app.domain.ports.defense_ai_ports import SpeechTtsPort, SynthesizedAudio

logger = logging.getLogger(__name__)


class EdgeTtsAdapter:
    """Implementa SpeechTtsPort usando Microsoft Edge TTS neuronal (sin API key)."""

    def __init__(self, voice: str = "es-CO-GonzaloNeural") -> None:
        self._voice = voice.strip() or "es-CO-GonzaloNeural"

    def synthesize(self, text: str) -> SynthesizedAudio:
        """Sintetiza texto en español colombiano a audio MP3."""
        clean_text = text.strip()
        if not clean_text:
            raise AiProviderUnavailableError(
                message="El texto para síntesis TTS está vacío.",
                context={"voice": self._voice},
            )
        try:
            audio_bytes = self._run_async(self._synthesize_async(clean_text))
        except FdcDomainError:
            raise
        except Exception as exc:
            logger.warning(
                "EdgeTtsAdapter falló | voice=%s | error_type=%s | detail=%s",
                self._voice,
                type(exc).__name__,
                exc,
            )
            raise AiProviderUnavailableError(
                message="Error al sintetizar voz con Edge TTS.",
                context={"voice": self._voice, "error_type": type(exc).__name__, "reason": str(exc)},
            ) from exc

        if not audio_bytes:
            logger.warning("EdgeTtsAdapter devolvió audio vacío | voice=%s", self._voice)
            raise AiProviderUnavailableError(
                message="Edge TTS devolvió una respuesta de audio vacía.",
                context={"voice": self._voice},
            )
        return SynthesizedAudio(
            audio_bytes=audio_bytes,
            mime_type="audio/mpeg",
            model_used=f"edge-tts:{self._voice}",
        )

    async def _synthesize_async(self, text: str) -> bytes:
        import edge_tts

        communicate = edge_tts.Communicate(text=text, voice=self._voice)
        chunks: list[bytes] = []
        async for chunk in communicate.stream():
            if chunk.get("type") == "audio" and chunk.get("data"):
                chunks.append(chunk["data"])
        return b"".join(chunks)

    @staticmethod
    def _run_async(coro) -> bytes:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)
        with ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result()


class FallbackTtsAdapter:
    """Decorador que intenta el proveedor TTS primario y cae al secundario si falla."""

    def __init__(
        self,
        primary: SpeechTtsPort,
        secondary: SpeechTtsPort | None = None,
        primary_name: str = "primary",
        secondary_name: str = "secondary",
    ) -> None:
        self._primary = primary
        self._secondary = secondary
        self._primary_name = primary_name
        self._secondary_name = secondary_name

    def synthesize(self, text: str) -> SynthesizedAudio:
        """Ejecuta TTS primario y activa respaldo silencioso si ocurre un fallo."""
        try:
            return self._primary.synthesize(text)
        except Exception as exc:
            logger.warning(
                "TTS primario (%s) falló | error_type=%s | detail=%s",
                self._primary_name,
                type(exc).__name__,
                exc,
            )
            if self._secondary is None:
                if isinstance(exc, FdcDomainError):
                    raise
                raise AiProviderUnavailableError(
                    message=f"Falló el proveedor TTS '{self._primary_name}'.",
                    context={"error_type": type(exc).__name__, "reason": str(exc)},
                ) from exc
            logger.info("Activando proveedor TTS de respaldo: %s", self._secondary_name)
            return self._secondary.synthesize(text)
