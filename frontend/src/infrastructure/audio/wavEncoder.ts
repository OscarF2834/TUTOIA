function writeAsciiString(view: DataView, offset: number, value: string): void {
  for (let i = 0; i < value.length; i += 1) {
    view.setUint8(offset + i, value.charCodeAt(i));
  }
}

function encodeMonoPcmWav(samples: Float32Array, sampleRate: number): Blob {
  const bytesPerSample = 2;
  const dataLength = samples.length * bytesPerSample;
  const buffer = new ArrayBuffer(44 + dataLength);
  const view = new DataView(buffer);

  writeAsciiString(view, 0, "RIFF");
  view.setUint32(4, 36 + dataLength, true);
  writeAsciiString(view, 8, "WAVE");
  writeAsciiString(view, 12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * bytesPerSample, true);
  view.setUint16(32, bytesPerSample, true);
  view.setUint16(34, 16, true);
  writeAsciiString(view, 36, "data");
  view.setUint32(40, dataLength, true);

  let offset = 44;
  for (let i = 0; i < samples.length; i += 1) {
    const clamped = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(offset, clamped < 0 ? clamped * 0x8000 : clamped * 0x7fff, true);
    offset += 2;
  }

  return new Blob([buffer], { type: "audio/wav" });
}

async function convertBlobToWav(blob: Blob): Promise<Blob> {
  const AudioCtx =
    window.AudioContext ||
    (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
  const context = new AudioCtx();
  try {
    const decoded = await context.decodeAudioData(await blob.arrayBuffer());
    const channelData = decoded.getChannelData(0);
    return encodeMonoPcmWav(channelData, decoded.sampleRate);
  } finally {
    await context.close().catch(() => {});
  }
}

export async function normalizeRecordedAudioForBackend(
  blob: Blob,
  mimeType: string,
): Promise<{ blob: Blob; filename: string }> {
  const baseMime = mimeType.split(";")[0].trim().toLowerCase();
  if (baseMime === "audio/webm") {
    return { blob: new Blob([blob], { type: "audio/webm" }), filename: "respuesta.webm" };
  }
  if (baseMime === "audio/ogg") {
    return { blob: new Blob([blob], { type: "audio/ogg" }), filename: "respuesta.ogg" };
  }
  if (baseMime === "audio/wav" || baseMime === "audio/x-wav") {
    return { blob: new Blob([blob], { type: "audio/wav" }), filename: "respuesta.wav" };
  }
  if (baseMime === "audio/mp3" || baseMime === "audio/mpeg") {
    return { blob: new Blob([blob], { type: "audio/mpeg" }), filename: "respuesta.mp3" };
  }
  const wavBlob = await convertBlobToWav(blob);
  return { blob: wavBlob, filename: "respuesta.wav" };
}
