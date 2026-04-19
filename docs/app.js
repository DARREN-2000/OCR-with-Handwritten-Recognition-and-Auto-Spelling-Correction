const imageInput = document.getElementById("imageInput");
const browseBtn = document.getElementById("browseBtn");
const dropzone = document.getElementById("dropzone");
const imagePreview = document.getElementById("imagePreview");
const previewPlaceholder = document.getElementById("previewPlaceholder");

const languageSelect = document.getElementById("languageSelect");
const enableCorrection = document.getElementById("enableCorrection");
const runBtn = document.getElementById("runBtn");
const clearBtn = document.getElementById("clearBtn");

const statusEl = document.getElementById("status");
const progressBar = document.getElementById("progressBar");

const selectedFileNameEl = document.getElementById("selectedFileName");
const selectedFileTypeEl = document.getElementById("selectedFileType");
const selectedFileSizeEl = document.getElementById("selectedFileSize");

const rawTextEl = document.getElementById("rawText");
const correctedTextEl = document.getElementById("correctedText");

const copyRawBtn = document.getElementById("copyRawBtn");
const copyBtn = document.getElementById("copyBtn");
const downloadRawBtn = document.getElementById("downloadRawBtn");
const downloadBtn = document.getElementById("downloadBtn");

const tesseractLanguageByChoice = {
    auto: "eng+fra+deu+spa+por",
    "en-US": "eng",
    fr: "fra",
    "de-DE": "deu",
    es: "spa",
    "pt-PT": "por"
};

let selectedFile = null;
let previewUrl = null;

function setStatus(message, tone = "") {
    statusEl.textContent = message;
    statusEl.className = `status ${tone}`.trim();
}

function setProgress(percent) {
    const clamped = Math.max(0, Math.min(100, Number(percent) || 0));
    progressBar.style.width = `${clamped}%`;
}

function toReadableFileSize(sizeInBytes) {
    if (!Number.isFinite(sizeInBytes) || sizeInBytes <= 0) {
        return "—";
    }
    const units = ["B", "KB", "MB", "GB"];
    let value = sizeInBytes;
    let unitIndex = 0;
    while (value >= 1024 && unitIndex < units.length - 1) {
        value /= 1024;
        unitIndex += 1;
    }
    return `${value.toFixed(unitIndex === 0 ? 0 : 2)} ${units[unitIndex]}`;
}

function clearPreviewUrl() {
    if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
        previewUrl = null;
    }
}

function clearOutputs() {
    rawTextEl.value = "";
    correctedTextEl.value = "";
    setProgress(0);
}

function updateFileDetails(file) {
    if (!file) {
        selectedFileNameEl.textContent = "—";
        selectedFileTypeEl.textContent = "—";
        selectedFileSizeEl.textContent = "—";
        return;
    }
    selectedFileNameEl.textContent = file.name;
    selectedFileTypeEl.textContent = file.type || "Unknown";
    selectedFileSizeEl.textContent = toReadableFileSize(file.size);
}

function setSelectedFile(file) {
    clearOutputs();

    if (!file) {
        selectedFile = null;
        imageInput.value = "";
        clearPreviewUrl();
        imagePreview.hidden = true;
        previewPlaceholder.hidden = false;
        previewPlaceholder.textContent = "No image selected yet.";
        updateFileDetails(null);
        setStatus("Ready.");
        return;
    }

    if (!file.type.startsWith("image/")) {
        setStatus("Please select a valid image file.", "error");
        return;
    }

    selectedFile = file;
    updateFileDetails(file);

    clearPreviewUrl();
    previewUrl = URL.createObjectURL(file);
    imagePreview.src = previewUrl;
    imagePreview.hidden = false;
    previewPlaceholder.hidden = true;

    setStatus("Image selected. Configure options and run OCR.");
}

function applyLanguageToolCorrections(text, matches) {
    if (!matches || matches.length === 0) {
        return text;
    }

    const ordered = [...matches].sort((a, b) => a.offset - b.offset);
    let corrected = "";
    let cursor = 0;

    for (const match of ordered) {
        const start = match.offset;
        const end = match.offset + match.length;
        const replacement = match.replacements?.[0]?.value;

        if (!Number.isFinite(start) || !Number.isFinite(end) || start < cursor || start > text.length) {
            continue;
        }

        corrected += text.slice(cursor, start);
        corrected += replacement ?? text.slice(start, end);
        cursor = end;
    }

    corrected += text.slice(cursor);
    return corrected;
}

function fetchWithTimeout(url, options, timeoutMs = 25000) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);
    return fetch(url, { ...options, signal: controller.signal }).finally(() => {
        clearTimeout(timeout);
    });
}

async function correctText(rawText, selectedLanguage) {
    const params = new URLSearchParams();
    params.append("text", rawText);
    params.append("language", selectedLanguage === "auto" ? "auto" : selectedLanguage);

    const response = await fetchWithTimeout("https://api.languagetool.org/v2/check", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: params.toString()
    });

    if (!response.ok) {
        if (response.status === 429) {
            throw new Error("LanguageTool API is rate-limited. Please wait and retry.");
        }
        throw new Error("Language correction request failed.");
    }

    const payload = await response.json();
    return applyLanguageToolCorrections(rawText, payload.matches || []);
}

async function runPipeline() {
    if (!selectedFile) {
        setStatus("Please upload an image first.", "warning");
        return;
    }

    const selectedLanguage = languageSelect.value;
    const tessLang = tesseractLanguageByChoice[selectedLanguage] || tesseractLanguageByChoice.auto;
    const shouldCorrect = enableCorrection.checked;

    runBtn.disabled = true;
    clearBtn.disabled = true;
    setProgress(5);
    setStatus("Starting OCR...");

    const startTs = performance.now();

    try {
        const ocrResult = await Tesseract.recognize(selectedFile, tessLang, {
            logger: (message) => {
                if (message.status === "recognizing text" && typeof message.progress === "number") {
                    const progress = Math.round(message.progress * 80);
                    setProgress(progress);
                    setStatus(`Running OCR... ${Math.round(message.progress * 100)}%`);
                }
            }
        });

        const rawText = (ocrResult?.data?.text || "").trim();
        rawTextEl.value = rawText;

        if (!rawText) {
            correctedTextEl.value = "";
            setProgress(100);
            setStatus("No text detected in image. Try a clearer image.", "warning");
            return;
        }

        if (!shouldCorrect) {
            correctedTextEl.value = rawText;
            setProgress(100);
            const elapsed = ((performance.now() - startTs) / 1000).toFixed(1);
            setStatus(`Done in ${elapsed}s (OCR only).`, "success");
            return;
        }

        setProgress(85);
        setStatus("Applying spelling and grammar correction...");

        try {
            const corrected = await correctText(rawText, selectedLanguage);
            correctedTextEl.value = corrected;
            setProgress(100);
            const elapsed = ((performance.now() - startTs) / 1000).toFixed(1);
            setStatus(`Done in ${elapsed}s.`, "success");
        } catch (error) {
            correctedTextEl.value = rawText;
            setProgress(100);
            setStatus(
                `${error.message} Returned OCR text without correction.`,
                "warning"
            );
        }
    } catch (error) {
        setProgress(0);
        setStatus(`OCR failed: ${error.message}`, "error");
    } finally {
        runBtn.disabled = false;
        clearBtn.disabled = false;
    }
}

async function copyText(text, emptyMessage, successMessage) {
    if (!text) {
        setStatus(emptyMessage, "warning");
        return;
    }

    try {
        await navigator.clipboard.writeText(text);
        setStatus(successMessage, "success");
    } catch (_error) {
        setStatus("Clipboard access failed in this browser/session.", "error");
    }
}

function downloadTextFile(text, fileName, emptyMessage) {
    if (!text) {
        setStatus(emptyMessage, "warning");
        return;
    }

    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    setStatus(`Downloaded ${fileName}`, "success");
}

browseBtn.addEventListener("click", () => imageInput.click());

dropzone.addEventListener("click", () => imageInput.click());
dropzone.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        imageInput.click();
    }
});

dropzone.addEventListener("dragover", (event) => {
    event.preventDefault();
    dropzone.classList.add("dragover");
});

dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("dragover");
});

dropzone.addEventListener("drop", (event) => {
    event.preventDefault();
    dropzone.classList.remove("dragover");

    const file = event.dataTransfer?.files?.[0];
    if (file) {
        setSelectedFile(file);
    }
});

imageInput.addEventListener("change", (event) => {
    const file = event.target.files?.[0];
    setSelectedFile(file || null);
});

runBtn.addEventListener("click", runPipeline);

clearBtn.addEventListener("click", () => {
    setSelectedFile(null);
    setStatus("Cleared. Ready for a new image.", "success");
});

copyRawBtn.addEventListener("click", () => {
    copyText(rawTextEl.value, "No raw OCR text to copy.", "Raw OCR text copied.");
});

copyBtn.addEventListener("click", () => {
    copyText(correctedTextEl.value, "No corrected text to copy.", "Corrected text copied.");
});

downloadRawBtn.addEventListener("click", () => {
    downloadTextFile(rawTextEl.value, "raw-ocr-text.txt", "No raw OCR text to download.");
});

downloadBtn.addEventListener("click", () => {
    downloadTextFile(correctedTextEl.value, "corrected-text.txt", "No corrected text to download.");
});

setSelectedFile(null);
