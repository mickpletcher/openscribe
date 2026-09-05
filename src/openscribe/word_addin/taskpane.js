"use strict";
let preview = null;
const status = (text) => { document.getElementById("status").textContent = text; };
function officeCall(invoke) {
  return new Promise((resolve, reject) => invoke(result => {
    if (result.status === Office.AsyncResultStatus.Succeeded) resolve(result.value);
    else reject(new Error(result.error.message));
  }));
}
async function documentBytes() {
  const file = await officeCall(done => Office.context.document.getFileAsync(
    Office.FileType.Compressed, {sliceSize: 65536}, done));
  try {
    if (file.size > 20 * 1024 * 1024) throw new Error("Document exceeds the 20 MiB limit.");
    const chunks = [];
    let size = 0;
    for (let i = 0; i < file.sliceCount; i++) {
      const slice = await officeCall(done => file.getSliceAsync(i, done));
      chunks.push(new Uint8Array(slice.data));
      size += slice.data.length;
    }
    const bytes = new Uint8Array(size);
    let offset = 0;
    for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.length; }
    return bytes;
  } finally { await officeCall(done => file.closeAsync(done)); }
}
async function request(path, body, contentType) {
  const response = await fetch(path, {method: "POST", redirect: "error", credentials: "omit", cache: "no-store",
    headers: {"Authorization": "Bearer " + document.getElementById("token").value, "Content-Type": contentType}, body});
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || "Local bridge request failed.");
  return payload;
}
async function previewDocument() {
  preview = null;
  document.getElementById("apply").disabled = true;
  const bytes = await documentBytes();
  preview = await request("/preview", bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document");
  document.getElementById("diff").textContent = preview.units.map(unit => unit.id + ": " + unit.status).join("\n")
    + "\n\n" + preview.diff;
  status(preview.blocked ? "Import blocked. Resolve conflicts and tracked changes, then preview again."
    : "Review the diff. Apply is a separate action and creates a local checkpoint.");
  document.getElementById("apply").disabled = preview.blocked;
}
async function applyDocument() {
  if (!preview) return;
  const bytes = await documentBytes();
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  const hash = Array.from(new Uint8Array(digest), value => value.toString(16).padStart(2, "0")).join("");
  if (hash !== preview.document_hash) throw new Error("Word changed after preview. Preview again.");
  const result = await request("/apply", JSON.stringify({preview_id: preview.preview_id, document_hash: hash}), "application/json");
  preview = null;
  document.getElementById("apply").disabled = true;
  status("Applied " + result.applied + " chapter changes. Backup: " + (result.backup || "no changes"));
}
async function run(operation) {
  document.getElementById("preview").disabled = true;
  document.getElementById("apply").disabled = true;
  try { await operation(); }
  catch (error) { preview = null; status(error.message); }
  finally { document.getElementById("preview").disabled = false; }
}
Office.onReady(info => {
  if (info.host !== Office.HostType.Word || !Office.context.requirements.isSetSupported("CompressedFile", "1.1")) {
    status("This host does not support compressed Word document access. Use the OpenScribe CLI import instead.");
    return;
  }
  document.getElementById("preview").disabled = false;
  document.getElementById("preview").addEventListener("click", () => run(previewDocument));
  document.getElementById("apply").addEventListener("click", () => run(applyDocument));
  status("Enter the token displayed by your local bridge, then preview the active document.");
});
