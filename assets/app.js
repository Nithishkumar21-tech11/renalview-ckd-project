const fields = [
  { key: "bp", label: "Blood pressure", unit: "mmHg", type: "number", min: 0, max: 200, step: 1 },
  { key: "sg", label: "Specific gravity", unit: "", type: "number", min: 1, max: 1.05, step: 0.005 },
  { key: "al", label: "Urine albumin", unit: "scale 0-5", type: "number", min: 0, max: 5, step: 1 },
  { key: "su", label: "Urine sugar", unit: "scale 0-5", type: "number", min: 0, max: 5, step: 1 },
  { key: "rbc", label: "Red blood cells in urine", unit: "microscopy", type: "select", options: [["", "Select value"], ["1", "Normal"], ["0", "Abnormal"]] },
  { key: "bu", label: "Blood urea", unit: "mg/dL", type: "number", min: 0, max: 200, step: 0.1 },
  { key: "sc", label: "Serum creatinine", unit: "mg/dL", type: "number", min: 0, max: 20, step: 0.1 },
  { key: "sod", label: "Sodium", unit: "mEq/L", type: "number", min: 100, max: 160, step: 0.1 },
  { key: "pot", label: "Potassium", unit: "mEq/L", type: "number", min: 2, max: 10, step: 0.1 },
  { key: "hemo", label: "Hemoglobin", unit: "g/dL", type: "number", min: 0, max: 25, step: 0.1 },
  { key: "wbcc", label: "White blood cell count", unit: "cells/mm³", type: "number", min: 1000, max: 50000, step: 1 },
  { key: "rbcc", label: "Red blood cell count", unit: "million cells/mm³", type: "number", min: 0, max: 10, step: 0.1 },
  { key: "htn", label: "Hypertension", unit: "", type: "select", options: [["", "Select value"], ["1", "Yes"], ["0", "No"]] },
];
const fieldGrid = document.querySelector("#field-grid");
const fileInput = document.querySelector("#pdf-file");
const extractButton = document.querySelector("#extract-button");
const uploadStatus = document.querySelector("#upload-status");
const selectedFile = document.querySelector("#selected-file");
const fileName = document.querySelector("#file-name");
const resultPanel = document.querySelector("#result-panel");

function buildFields() {
  fieldGrid.innerHTML = fields.map((field) => {
    const id = `field-${field.key}`;
    const label = `${field.label}${field.unit ? ` <span>· ${field.unit}</span>` : ""}`;
    const input = field.type === "select"
      ? `<select id="${id}" name="${field.key}" required>${field.options.map(([value, text]) => `<option value="${value}">${text}</option>`).join("")}</select>`
      : `<input id="${id}" name="${field.key}" type="number" min="${field.min}" max="${field.max}" step="${field.step}" placeholder="Enter value" required>`;
    return `<div class="field"><label for="${id}">${label}</label>${input}</div>`;
  }).join("");
}
function setStatus(message, isError = false) {
  uploadStatus.textContent = message;
  uploadStatus.classList.toggle("error", isError);
}
function showPickedFile(file) {
  selectedFile.hidden = !file;
  extractButton.disabled = !file;
  fileName.textContent = file ? file.name : "";
  if (file) setStatus("");
}
function applyExtractedValues(values) {
  for (const field of fields) {
    document.querySelector(`#field-${field.key}`).value = values[field.key] ?? "";
  }
}
function closeResult() {
  resultPanel.hidden = true;
  resultPanel.classList.remove("is-ckd");
}
buildFields();

fileInput.addEventListener("change", () => {
  const file = fileInput.files[0];
  if (file && file.type !== "application/pdf") {
    fileInput.value = "";
    showPickedFile(null);
    setStatus("Please choose a PDF file.", true);
    return;
  }
  showPickedFile(file);
  closeResult();
});
document.querySelector("#remove-file").addEventListener("click", () => {
  fileInput.value = "";
  showPickedFile(null);
});
const dropzone = document.querySelector("#dropzone");
for (const name of ["dragenter", "dragover"]) dropzone.addEventListener(name, (event) => {
  event.preventDefault(); dropzone.classList.add("dragover");
});
for (const name of ["dragleave", "drop"]) dropzone.addEventListener(name, (event) => {
  event.preventDefault(); dropzone.classList.remove("dragover");
});
dropzone.addEventListener("drop", (event) => {
  const file = event.dataTransfer.files[0];
  if (file && file.type === "application/pdf") {
    fileInput.files = event.dataTransfer.files;
    showPickedFile(file);
    closeResult();
  } else setStatus("Please choose a PDF file.", true);
});

extractButton.addEventListener("click", async () => {
  const file = fileInput.files[0];
  if (!file) return;
  const body = new FormData(); body.append("file", file);
  extractButton.disabled = true;
  extractButton.innerHTML = 'Reading PDF <span class="spinner"></span>';
  setStatus("Looking for measurements in the PDF...");
  try {
    const response = await fetch("/api/extract", { method: "POST", body });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Could not read the PDF.");
    applyExtractedValues(data.values);
    closeResult();
    setStatus(`Found ${data.found} of ${data.total} measurements. Review and complete the fields.`);
  } catch (error) {
    setStatus(error.message || "Could not read the PDF.", true);
  } finally {
    extractButton.disabled = false;
    extractButton.innerHTML = 'Read PDF values <span aria-hidden="true">→</span>';
  }
});

document.querySelector("#review-form").addEventListener("submit", async (event) => {
  event.preventDefault(); closeResult();
  const form = new FormData(event.currentTarget); const payload = {};
  for (const field of fields) {
    const raw = form.get(field.key);
    if (raw === null || raw === "") {
      document.querySelector(`#field-${field.key}`).focus();
      document.querySelector("#form-hint").textContent = `Please enter ${field.label.toLowerCase()}.`;
      return;
    }
    const value = Number(raw);
    if (!Number.isFinite(value) || (field.type === "number" && (value < field.min || value > field.max))) {
      document.querySelector(`#field-${field.key}`).focus();
      document.querySelector("#form-hint").textContent = `Check the value for ${field.label.toLowerCase()}.`;
      return;
    }
    payload[field.key] = value;
  }
  const button = document.querySelector("#predict-button");
  button.disabled = true; button.innerHTML = 'Analyzing <span class="spinner"></span>';
  document.querySelector("#form-hint").textContent = "Generating the model classification...";
  try {
    const response = await fetch("/api/predict", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    const data = await response.json();
    if (!response.ok) throw new Error(Array.isArray(data.detail) ? "Check the values and allowed ranges." : (data.detail || "Could not generate a result."));
    const isCkd = data.label === "CKD";
    resultPanel.classList.toggle("is-ckd", isCkd);
    document.querySelector("#result-icon").textContent = isCkd ? "!" : "✓";
    document.querySelector("#result-title").textContent = data.label;
    document.querySelector("#result-copy").textContent = "Predicted class for the entered measurements";
    resultPanel.hidden = false;
    document.querySelector("#form-hint").textContent = "Model classification generated.";
    resultPanel.scrollIntoView({ behavior: "smooth", block: "nearest" });
  } catch (error) {
    document.querySelector("#form-hint").textContent = error.message || "Could not generate a result.";
  } finally {
    button.disabled = false; button.innerHTML = 'Generate result <span aria-hidden="true">→</span>';
  }
});
document.querySelector("#result-close").addEventListener("click", closeResult);
document.querySelector("#menu-toggle").addEventListener("click", (event) => {
  const nav = document.querySelector("#main-nav"); const opened = nav.classList.toggle("is-open");
  event.currentTarget.setAttribute("aria-expanded", String(opened));
});
document.querySelectorAll(".main-nav a").forEach((link) => link.addEventListener("click", () => {
  document.querySelector("#main-nav").classList.remove("is-open");
  document.querySelector("#menu-toggle").setAttribute("aria-expanded", "false");
}));
