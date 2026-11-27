export function triggerBrowserFileDownload(blob: Blob, filename: string): void {
  const objectUrl = window.URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = filename;
  anchor.style.display = "none";
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  window.setTimeout(() => window.URL.revokeObjectURL(objectUrl), 1000);
}
