const imageInput = document.getElementById("imagefile");
const languageSelect = document.getElementById("languageSelect");
const runBtn = document.getElementById("runBtn");
const statusEl = document.getElementById("status");
const progressBar = document.getElementById("progressBar");
const fileNameEl = document.getElementById("file-name");
const dropZone = document.getElementById("dropZone");
const rawTextEl = document.getElementById("rawText");
const correctedTextEl = document.getElementById("correctedText");
const copyBtn = document.getElementById("copyBtn");
const downloadBtn = document.getElementById("downloadBtn");
const resetBtn = document.getElementById("resetBtn");

const uploadSection = document.getElementById("uploadSection");
const featuresSection = document.getElementById("featuresSection");
const resultSection = document.getElementById("resultSection");
const imagePreview = document.getElementById("imagePreview");
const preprocessedCanvas = document.getElementById("preprocessedCanvas");

const tesseractLanguageByChoice = {
    auto: "eng+fra+deu+spa+por",
    "en-US": "eng",
    fr: "fra",
    "de-DE": "deu",
    es: "spa",
    "pt-PT": "por"
};

let worker = null;
let currentWorkerLang = null;
let cvReady = false;

function onOpenCvReady() {
    cvReady = true;
    console.log("OpenCV is ready.");
}

function setStatus(message) {
    statusEl.textContent = message;
}

async function preprocessImage(imgElement) {
    if (!cvReady) {
        console.warn("OpenCV not ready yet, skipping preprocessing.");
        return imgElement;
    }
    return new Promise((resolve) => {
        let src, gray, denoised, binary;
        try {
            src = cv.imread(imgElement);

            // 1. Grayscale
            gray = new cv.Mat();
            cv.cvtColor(src, gray, cv.COLOR_RGBA2GRAY, 0);

            // 2. Denoising
            denoised = new cv.Mat();
            try {
                cv.fastNlMeansDenoising(gray, denoised, 10, 7, 21);
            } catch (denoiseErr) {
                console.warn("OpenCV denoising failed, skipping:", denoiseErr);
                gray.copyTo(denoised); // Fallback to grayscale without denoising
            }

            // 3. Adaptive Thresholding
            binary = new cv.Mat();
            cv.adaptiveThreshold(denoised, binary, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY, 11, 2);

            // Display on canvas
            preprocessedCanvas.style.display = "block";
            cv.imshow('preprocessedCanvas', binary);

            resolve(preprocessedCanvas);
        } catch (err) {
            console.error("OpenCV preprocessing error:", err);
            resolve(imgElement); // Fallback to original image
        } finally {
            // Cleanup
            if (src) src.delete();
            if (gray) gray.delete();
            if (denoised) denoised.delete();
            if (binary) binary.delete();
        }
    });
}

function tokenizeAndClean(text) {
    // Mimic basic NLP tokenization/cleaning (like NLTK in backend)
    // 1. Normalize whitespace
    let cleaned = text.replace(/\s+/g, ' ').trim();
    // 2. Fix punctuation spacing (e.g. "word , word" -> "word, word")
    cleaned = cleaned.replace(/\s+([.,;:!?])/g, '$1');
    // 3. Ensure space after punctuation (e.g. "word,word" -> "word, word")
    cleaned = cleaned.replace(/([.,;:!?])(?=[^\s])/g, '$1 ');
    return cleaned;
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

    let detectedName = null;
    if (selectedLanguage === "auto" && payload.language && payload.language.detectedLanguage) {
        detectedName = payload.language.detectedLanguage.name;
    }

    return {
        corrected: applyLanguageToolCorrections(rawText, payload.matches || []),
        detectedName: detectedName
    };
}

function handleFileSelect(file) {
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
}

// Drag and drop support
dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover");
});

dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("dragover");
});

dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragover");

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        imageInput.files = e.dataTransfer.files;
        handleFileSelect(e.dataTransfer.files[0]);
    }
});

imageInput.addEventListener("change", (event) => {
    const file = event.target.files && event.target.files[0];
    handleFileSelect(file);
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
        progressBar.style.display = "block";
        progressBar.value = 0;

        if (!worker) {
            worker = await Tesseract.createWorker(tessLang, 1, {
                logger: (message) => {
                    if (message.status === "recognizing text" && typeof message.progress === "number") {
                        const pct = Math.round(message.progress * 100);
                        setStatus(`Running OCR... ${pct}%`);
                        progressBar.value = pct;
                    } else if (message.status === "loading tesseract core" || message.status === "loading language traineddata") {
                        setStatus(`Loading OCR Data...`);
                        progressBar.removeAttribute("value"); // indeterminate state
                    }
                }
            });
            currentWorkerLang = tessLang;
        } else if (currentWorkerLang !== tessLang) {
            await worker.loadLanguage(tessLang);
            await worker.initialize(tessLang);
            currentWorkerLang = tessLang;
        }

        setStatus("Pre-processing image...");
        let targetForOCR = file;

        // Use an Image element to load the file, then process it
        const imgForProcessing = new Image();
        imgForProcessing.src = URL.createObjectURL(file);
        await new Promise(resolve => imgForProcessing.onload = resolve);

        targetForOCR = await preprocessImage(imgForProcessing);

        setStatus("Running OCR...");
        const ocrResult = await worker.recognize(targetForOCR);

        let rawText = (ocrResult.data.text || "").trim();

        if (rawText) {
            rawText = tokenizeAndClean(rawText);
        }

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
        const result = await correctText(rawText, selectedLanguage);
        correctedTextEl.value = result.corrected;
        if (result.detectedName) {
            setStatus(`Done. Detected Language: ${result.detectedName}`);
        } else {
            setStatus("Done.");
        }

        // Switch sections
        uploadSection.classList.add("hidden");
        featuresSection.classList.add("hidden");
        resultSection.classList.remove("hidden");

    } catch (error) {
        setStatus(`Error: ${error.message}`);
    } finally {
        progressBar.style.display = "none";
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
    preprocessedCanvas.style.display = "none";
    const ctx = preprocessedCanvas.getContext("2d");
    if(ctx) ctx.clearRect(0, 0, preprocessedCanvas.width, preprocessedCanvas.height);

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
