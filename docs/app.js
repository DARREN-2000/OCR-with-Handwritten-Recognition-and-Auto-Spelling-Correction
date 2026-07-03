const imageInput = document.getElementById("imagefile");
const languageSelect = document.getElementById("languageSelect");
const runBtn = document.getElementById("runBtn");
const statusEl = document.getElementById("status");
const fileNameEl = document.getElementById("file-name");
const rawTextEl = document.getElementById("rawText");
const correctedTextEl = document.getElementById("correctedText");
const copyBtn = document.getElementById("copyBtn");
const downloadBtn = document.getElementById("downloadBtn");
const resetBtn = document.getElementById("resetBtn");

const uploadSection = document.getElementById("uploadSection");
const featuresSection = document.getElementById("featuresSection");
const resultSection = document.getElementById("resultSection");
const imagePreview = document.getElementById("imagePreview");

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

    if (!file) {
        fileNameEl.textContent = "";
        imagePreview.style.display = "none";
        imagePreview.src = "";
        return;
    }

    fileNameEl.textContent = file.name;
    setStatus("Image selected. Ready to process.");

    // Update image preview
    const reader = new FileReader();
    reader.onload = (e) => {
        imagePreview.src = e.target.result;
        imagePreview.style.display = "block";
    };
    reader.readAsDataURL(file);
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
    imageInput.disabled = true;
    languageSelect.disabled = true;
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
            // Re-enable form
            runBtn.disabled = false;
            imageInput.disabled = false;
            languageSelect.disabled = false;
            return;
        }

        setStatus("Applying spelling and grammar correction...");
        const corrected = await correctText(rawText, selectedLanguage);
        correctedTextEl.value = corrected;
        setStatus("Done.");

        // Switch sections
        uploadSection.classList.add("hidden");
        featuresSection.classList.add("hidden");
        resultSection.classList.remove("hidden");

    } catch (error) {
        setStatus(`Error: ${error.message}`);
    } finally {
        runBtn.disabled = false;
        imageInput.disabled = false;
        languageSelect.disabled = false;
    }
});

resetBtn.addEventListener("click", () => {
    // Reset inputs
    imageInput.value = "";
    fileNameEl.textContent = "";
    rawTextEl.value = "";
    correctedTextEl.value = "";
    setStatus("");
    imagePreview.src = "";
    imagePreview.style.display = "none";

    // Switch sections
    resultSection.classList.add("hidden");
    uploadSection.classList.remove("hidden");
    featuresSection.classList.remove("hidden");
});

copyBtn.addEventListener("click", async () => {
    const text = correctedTextEl.value;
    if (!text) {
        return;
    }

    try {
        await navigator.clipboard.writeText(text);
        const originalText = copyBtn.textContent;
        copyBtn.textContent = "Copied!";
        setTimeout(() => {
            copyBtn.textContent = originalText;
        }, 2000);
    } catch (_error) {
        alert("Clipboard access failed.");
    }
});

downloadBtn.addEventListener("click", () => {
    const text = correctedTextEl.value;
    if (!text) {
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
});
