function getRiskClass(score) {
    if (score >= 15) return "high";
    if (score >= 8) return "medium";
    return "low";
}

function getRiskIcon(score) {
    if (score >= 15) return "🚨";
    if (score >= 8) return "⚠️";
    return "✅";
}

function handleModeChange() {
    const mode = document.getElementById("scanMode").value;
    const singleInputSection = document.getElementById("singleInputSection");
    const emailSection = document.getElementById("emailSection");
    const imageSection = document.getElementById("imageSection");
    const label = document.getElementById("inputLabel");
    const textArea = document.getElementById("inputText");

    if (mode === "url") {
        singleInputSection.classList.remove("hidden");
        emailSection.classList.add("hidden");
        imageSection.classList.add("hidden");
        label.textContent = "Paste a URL";
        textArea.placeholder = "Example: http://paypa1-login-secure.xyz";
    } else if (mode === "email") {
        singleInputSection.classList.add("hidden");
        emailSection.classList.remove("hidden");
        imageSection.classList.add("hidden");
    } else if (mode === "image") {
        singleInputSection.classList.add("hidden");
        emailSection.classList.add("hidden");
        imageSection.classList.remove("hidden");
    } else {
        singleInputSection.classList.remove("hidden");
        emailSection.classList.add("hidden");
        imageSection.classList.add("hidden");
        label.textContent = "Paste a message or link";
        textArea.placeholder = "Example: URGENT! Your bank account is suspended...";
    }
}

function loadExample(type) {
    const modeSelect = document.getElementById("scanMode");
    const textArea = document.getElementById("inputText");
    const emailSender = document.getElementById("emailSender");
    const emailSubject = document.getElementById("emailSubject");
    const emailBody = document.getElementById("emailBody");

    if (type === "bank") {
        modeSelect.value = "text";
        handleModeChange();
        textArea.value = "URGENT! Your bank account is suspended. Verify now using your OTP at http://bit.ly/test";
    } else if (type === "job") {
        modeSelect.value = "text";
        handleModeChange();
        textArea.value = "Congratulations, your job offer has been approved. Pay a registration fee today to secure your position.";
    } else if (type === "safe") {
        modeSelect.value = "text";
        handleModeChange();
        textArea.value = "Hi Austin, just confirming our meeting for tomorrow at 10:00.";
    } else if (type === "url") {
        modeSelect.value = "url";
        handleModeChange();
        textArea.value = "http://paypa1-login-secure.xyz/reset-account";
    } else if (type === "email") {
        modeSelect.value = "email";
        handleModeChange();
        emailSender.value = "support@bank-alerts-secure.com";
        emailSubject.value = "Urgent account verification required";
        emailBody.value = "Dear customer, your online banking profile has been suspended. Verify your account immediately and confirm your OTP to avoid permanent closure.";
    }
}

function clearAll() {
    const result = document.getElementById("result");

    document.getElementById("inputText").value = "";
    document.getElementById("imageInput").value = "";

    const emailSender = document.getElementById("emailSender");
    const emailSubject = document.getElementById("emailSubject");
    const emailBody = document.getElementById("emailBody");

    if (emailSender) emailSender.value = "";
    if (emailSubject) emailSubject.value = "";
    if (emailBody) emailBody.value = "";

    result.classList.add("hidden");
    result.innerHTML = "";
}

function saveToHistory(entry) {
    const history = JSON.parse(localStorage.getItem("safesignal_history") || "[]");
    history.unshift(entry);
    const trimmed = history.slice(0, 5);
    localStorage.setItem("safesignal_history", JSON.stringify(trimmed));
    renderHistory();
}

function clearHistory() {
    localStorage.removeItem("safesignal_history");
    renderHistory();
}

function renderHistory() {
    const historyList = document.getElementById("historyList");
    const history = JSON.parse(localStorage.getItem("safesignal_history") || "[]");

    if (!history.length) {
        historyList.innerHTML = `<div class="empty-state">No scans yet.</div>`;
        return;
    }

    historyList.innerHTML = history.map(item => `
        <div class="history-item">
            <div class="history-item-top">
                <span class="badge ${getRiskClass(item.score)}">${getRiskIcon(item.score)} ${item.risk}</span>
                <span class="score-pill">${item.score} pts</span>
            </div>
            <div class="history-snippet">${item.text}</div>
        </div>
    `).join("");
}

async function copyResult(text) {
    try {
        await navigator.clipboard.writeText(text);
        alert("Result copied to clipboard.");
    } catch (error) {
        alert("Could not copy result.");
    }
}

async function checkScam() {
    const result = document.getElementById("result");
    const button = document.getElementById("analyzeBtn");
    const btnText = button.querySelector(".btn-text");
    const btnLoader = button.querySelector(".btn-loader");

    const mode = document.getElementById("scanMode").value;
    const text = document.getElementById("inputText").value.trim();
    const sender = document.getElementById("emailSender").value.trim();
    const subject = document.getElementById("emailSubject").value.trim();
    const body = document.getElementById("emailBody").value.trim();
    const imageInput = document.getElementById("imageInput");

    let payload = {};
    let historyText = "";
    let useFormData = false;

    if (mode === "email") {
        if (!sender && !subject && !body) {
            result.classList.remove("hidden");
            result.innerHTML = `
                <div class="empty-state">
                    Please fill in the email fields before analyzing.
                </div>
            `;
            return;
        }

        payload = {
            mode: "email",
            sender,
            subject,
            body
        };

        historyText = `${subject || "No subject"} | ${sender || "No sender"}`;
    } else if (mode === "url") {
        if (!text) {
            result.classList.remove("hidden");
            result.innerHTML = `
                <div class="empty-state">
                    Please paste a URL before analyzing.
                </div>
            `;
            return;
        }

        payload = {
            mode: "url",
            url: text
        };

        historyText = text;
    } else if (mode === "image") {
        const file = imageInput.files[0];

        if (!file) {
            result.classList.remove("hidden");
            result.innerHTML = `
                <div class="empty-state">
                    Please upload a screenshot before analyzing.
                </div>
            `;
            return;
        }

        const formData = new FormData();
        formData.append("mode", "image");
        formData.append("image", file);

        payload = formData;
        historyText = `Screenshot scan: ${file.name}`;
        useFormData = true;
    } else {
        if (!text) {
            result.classList.remove("hidden");
            result.innerHTML = `
                <div class="empty-state">
                    Please paste a message or link before analyzing.
                </div>
            `;
            return;
        }

        payload = {
            mode: "text",
            text: text
        };

        historyText = text;
    }

    button.disabled = true;
    btnText.textContent = "Analyzing...";
    btnLoader.classList.remove("hidden");

    result.classList.remove("hidden");

    try {
        const fetchOptions = {
            method: "POST"
        };

        if (useFormData) {
            fetchOptions.body = payload;
        } else {
            fetchOptions.headers = {
                "Content-Type": "application/json"
            };
            fetchOptions.body = JSON.stringify(payload);
        }

        const response = await fetch("/analyze", fetchOptions);

        if (!response.ok) {
            throw new Error("Server returned an error.");
        }

        const data = await response.json();
        const riskClass = getRiskClass(data.score);
        const riskIcon = getRiskIcon(data.score);

        // Show main result card
        result.className = `result-card ${riskClass}`;
        result.classList.remove("hidden");

        // Top summary
        document.getElementById("resultBadge").textContent = "Analysis Result";
        document.getElementById("resultTitle").textContent = `${riskIcon} ${data.risk}`;
        document.getElementById("resultScore").textContent = data.score;
        document.getElementById("resultMode").textContent = mode.toUpperCase();

        // Confidence
        let confidence = "Medium";
        if (data.ocr_quality) {
            confidence = data.ocr_quality;
        } else if (data.score >= 12) {
            confidence = "High";
        } else if (data.score <= 3) {
            confidence = "Low";
        }
        document.getElementById("resultConfidence").textContent = confidence;

        // Summary
        let summary = "No strong scam indicators were found.";
        if (data.score >= 12) {
            summary = "Multiple strong scam signals were detected. This looks high risk.";
        } else if (data.score >= 6) {
            summary = "Some suspicious patterns were detected. Proceed carefully.";
        } else if (data.legit_reasons && data.legit_reasons.length) {
            summary = "This looks more legitimate based on the detected structure and contact details.";
        }
        document.getElementById("resultSummary").textContent = summary;

        // Advice
        document.getElementById("resultAdvice").textContent = data.advice || "No advice available.";

        // Risk reasons
        const riskList = document.getElementById("riskReasons");
        riskList.innerHTML = "";
        if (data.reasons && data.reasons.length) {
            data.reasons.forEach(reason => {
                const li = document.createElement("li");
                li.textContent = reason;
                riskList.appendChild(li);
            });
        } else {
            riskList.innerHTML = "<li>No specific warning signals were found.</li>";
        }

        // Legit reasons
        const legitList = document.getElementById("legitReasons");
        legitList.innerHTML = "";
        if (data.legit_reasons && data.legit_reasons.length) {
            data.legit_reasons.forEach(reason => {
                const li = document.createElement("li");
                li.textContent = reason;
                legitList.appendChild(li);
            });
        } else {
            legitList.innerHTML = "<li>No strong legitimacy signals were detected.</li>";
        }

        // Insights
        const insightsList = document.getElementById("insightsList");
        insightsList.innerHTML = "";
        if (data.insights && data.insights.length) {
            data.insights.forEach(insight => {
                const div = document.createElement("div");
                div.className = "insight-card";
                div.innerHTML = `
                    <div class="insight-title">${insight.title}</div>
                    <div class="insight-text">${insight.explanation}</div>
                `;
                insightsList.appendChild(div);
            });
        } else {
            insightsList.innerHTML = `<p class="empty-state">No educational insights available for this scan.</p>`;
        }

        // OCR blocks reset
        const ocrMetaBlock = document.getElementById("ocrMetaBlock");
        const extractedTextBlock = document.getElementById("extractedTextBlock");
        const urlsBlock = document.getElementById("urlsBlock");
        const phonesBlock = document.getElementById("phonesBlock");

        ocrMetaBlock.classList.add("hidden");
        extractedTextBlock.classList.add("hidden");
        urlsBlock.classList.add("hidden");
        phonesBlock.classList.add("hidden");

        // OCR + extracted details for screenshot scans
        if (data.extracted_text !== undefined) {
            ocrMetaBlock.classList.remove("hidden");
            extractedTextBlock.classList.remove("hidden");

            document.getElementById("ocrQualityText").textContent = data.ocr_quality || "Unknown";
            document.getElementById("ocrConfidenceText").textContent = data.ocr_confidence ?? "0";
            document.getElementById("extractedText").textContent = data.extracted_text || "No text extracted.";

            // URLs
            const urlsContainer = document.getElementById("detectedUrls");
            urlsContainer.innerHTML = "";
            if (data.extracted_urls && data.extracted_urls.length) {
                urlsBlock.classList.remove("hidden");
                data.extracted_urls.forEach(url => {
                    const span = document.createElement("span");
                    span.className = "tag";
                    span.textContent = url;
                    urlsContainer.appendChild(span);
                });
            }

            // Phones
            const phonesContainer = document.getElementById("detectedPhones");
            phonesContainer.innerHTML = "";
            if (data.extracted_phones && data.extracted_phones.length) {
                phonesBlock.classList.remove("hidden");
                data.extracted_phones.forEach(phone => {
                    const span = document.createElement("span");
                    span.className = "tag";
                    span.textContent = phone;
                    phonesContainer.appendChild(span);
                });
            }
        }

        saveToHistory({
            text: historyText.length > 90 ? historyText.slice(0, 90) + "..." : historyText,
            risk: data.risk,
            score: data.score
        });

    } catch (error) {
        result.classList.remove("hidden");
        result.innerHTML = `
            <div class="error-state">
                Could not connect to the backend. Make sure <strong>python app.py</strong> is running.
            </div>
        `;
    } finally {
        button.disabled = false;
        btnText.textContent = "Analyze";
        btnLoader.classList.add("hidden");
    }
}

       // Show result container
result.classList.remove("hidden");

// Top summary
document.getElementById("resultTitle").textContent = `${riskIcon} ${data.risk}`;
document.getElementById("resultScore").textContent = data.score;
document.getElementById("resultMode").textContent = mode.toUpperCase();

// Confidence logic
let confidence = "Medium";
if (data.ocr_quality) {
    confidence = data.ocr_quality;
} else if (data.score >= 12) {
    confidence = "High";
} else if (data.score <= 3) {
    confidence = "Low";
}
document.getElementById("resultConfidence").textContent = confidence;

// Smart explanation
let summary = "No strong scam indicators were found.";
if (data.score >= 12) {
    summary = "Multiple strong scam signals detected. High risk.";
} else if (data.score >= 6) {
    summary = "Some suspicious patterns detected. Proceed with caution.";
}
document.getElementById("resultSummary").textContent = summary;

// Advice
document.getElementById("resultAdvice").textContent = data.advice;

// Risk reasons
const riskList = document.getElementById("riskReasons");
riskList.innerHTML = "";
if (data.reasons && data.reasons.length) {
    data.reasons.forEach(r => {
        const li = document.createElement("li");
        li.textContent = r;
        riskList.appendChild(li);
    });
} else {
    riskList.innerHTML = "<li>No specific warning signals found.</li>";
}

// Legit reasons
const legitList = document.getElementById("legitReasons");
legitList.innerHTML = "";
if (data.legit_reasons && data.legit_reasons.length) {
    data.legit_reasons.forEach(r => {
        const li = document.createElement("li");
        li.textContent = r;
        legitList.appendChild(li);
    });
} else {
    legitList.innerHTML = "<li>No strong legitimacy signals detected.</li>";
}

// Insights
const insightsList = document.getElementById("insightsList");
insightsList.innerHTML = "";
if (data.insights && data.insights.length) {
    data.insights.forEach(insight => {
        const div = document.createElement("div");
        div.className = "insight-card";
        div.innerHTML = `
            <div class="insight-title">${insight.title}</div>
            <div class="insight-text">${insight.explanation}</div>
        `;
        insightsList.appendChild(div);
    });
} else {
    insightsList.innerHTML = `<p class="empty-state">No educational insights available.</p>`;
}

// OCR + extracted data (only for screenshots)
if (data.extracted_text !== undefined) {
    document.getElementById("ocrMetaBlock").classList.remove("hidden");
    document.getElementById("extractedTextBlock").classList.remove("hidden");

    document.getElementById("ocrQualityText").textContent = data.ocr_quality;
    document.getElementById("ocrConfidenceText").textContent = data.ocr_confidence;

    document.getElementById("extractedText").textContent = data.extracted_text;

    // URLs
    const urlsBlock = document.getElementById("urlsBlock");
    const urlsContainer = document.getElementById("detectedUrls");
    urlsContainer.innerHTML = "";

    if (data.extracted_urls && data.extracted_urls.length) {
        urlsBlock.classList.remove("hidden");
        data.extracted_urls.forEach(url => {
            const span = document.createElement("span");
            span.className = "tag";
            span.textContent = url;
            urlsContainer.appendChild(span);
        });
    }

    // Phones
    const phonesBlock = document.getElementById("phonesBlock");
    const phonesContainer = document.getElementById("detectedPhones");
    phonesContainer.innerHTML = "";

    if (data.extracted_phones && data.extracted_phones.length) {
        phonesBlock.classList.remove("hidden");
        data.extracted_phones.forEach(phone => {
            const span = document.createElement("span");
            span.className = "tag";
            span.textContent = phone;
            phonesContainer.appendChild(span);
        });
    }
}

// Save history
saveToHistory({
    text: historyText.length > 90 ? historyText.slice(0, 90) + "..." : historyText,
    risk: data.risk,
    score: data.score
});
