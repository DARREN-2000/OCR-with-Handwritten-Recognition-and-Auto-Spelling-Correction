const imageInput = document.getElementById("imageInput");
const languageSelect = document.getElementById("languageSelect");
const runBtn = document.getElementById("runBtn");
const statusEl = document.getElementById("status");
const selectedFileNameEl = document.getElementById("selectedFileName");
const rawTextEl = document.getElementById("rawText");
const correctedTextEl = document.getElementById("correctedText");
const copyBtn = document.getElementById("copyBtn");
const downloadBtn = document.getElementById("downloadBtn");

const tesseractLanguageByChoice = {
    auto: "eng+fra+deu+spa+por",
    "en-US": "eng",
    fr: "fra",
    "de-DE": "deu",
    es: "spa",
    "pt-PT": "por"
};

let worker = null;

function setStatus(message) {
    statusEl.textContent = message;
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
        const replacement = match.replacements && match.replacements[0] ? match.replacements[0].value : null;

        if (start < cursor) {
            continue;
        }

        corrected += text.slice(cursor, start);
        corrected += replacement ?? text.slice(start, end);
        cursor = end;
    }

    corrected += text.slice(cursor);
    return corrected;
}

async function correctText(rawText, selectedLanguage) {
    const params = new URLSearchParams();
    params.append("text", rawText);
    params.append("language", selectedLanguage);

    const response = await fetch("https://api.languagetool.org/v2/check", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: params.toString()
    });

    if (!response.ok) {
        if (response.status === 429) {
            throw new Error("LanguageTool rate limit exceeded. Please try again later.");
        }
        throw new Error(`Language correction request failed with status ${response.status}.`);
    }

    const payload = await response.json();
    return applyLanguageToolCorrections(rawText, payload.matches || []);
}

imageInput.addEventListener("change", (event) => {
    const file = event.target.files && event.target.files[0];
    rawTextEl.value = "";
    correctedTextEl.value = "";

    if (!file) {
        selectedFileNameEl.textContent = "No file selected.";
        return;
    }

    selectedFileNameEl.textContent = file.name;
    setStatus("Image selected.");
});

runBtn.addEventListener("click", async () => {
    const file = imageInput.files && imageInput.files[0];
    if (!file) {
        setStatus("Please choose an image first.");
        return;
    }

    const selectedLanguage = languageSelect.value;
    const tessLang = tesseractLanguageByChoice[selectedLanguage] || tesseractLanguageByChoice.auto;

    runBtn.disabled = true;
    setStatus("Initializing OCR Worker...");

    try {
        if (!worker) {
            worker = await Tesseract.createWorker(tessLang, 1, {
                logger: (message) => {
                    if (message.status === "recognizing text" && typeof message.progress === "number") {
                        setStatus(`Running OCR... ${Math.round(message.progress * 100)}%`);
                    } else if (message.status === "loading tesseract core" || message.status === "loading language traineddata") {
                        setStatus(`Loading OCR Data...`);
                    }
                }
            });
        } else {
            await worker.loadLanguage(tessLang);
            await worker.initialize(tessLang);
        }

        setStatus("Running OCR...");
        const ocrResult = await worker.recognize(file);

        const rawText = (ocrResult.data.text || "").trim();
        rawTextEl.value = rawText;

        if (!rawText) {
            correctedTextEl.value = "";
            setStatus("No text detected in image.");
            return;
        }

        setStatus("Applying spelling and grammar correction...");
        const corrected = await correctText(rawText, selectedLanguage);
        correctedTextEl.value = corrected;
        setStatus("Done.");
    } catch (error) {
        setStatus(`Error: ${error.message}`);
    } finally {
        runBtn.disabled = false;
    }
});

copyBtn.addEventListener("click", async () => {
    const text = correctedTextEl.value;
    if (!text) {
        setStatus("No corrected text to copy.");
        return;
    }

    try {
        await navigator.clipboard.writeText(text);
        setStatus("Corrected text copied.");
    } catch (_error) {
        setStatus("Clipboard access failed.");
    }
});

downloadBtn.addEventListener("click", () => {
    const text = correctedTextEl.value;
    if (!text) {
        setStatus("No corrected text to download.");
        return;
    }

    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "corrected-text.txt";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    setStatus("Downloaded corrected-text.txt");
});
