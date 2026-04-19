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
    result.innerHTML = `
        <div class="empty-state">Checking for scam signals...</div>
    `;

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

        const copyText = `SafeSignal Result
Risk: ${data.risk}
Score: ${data.score}
Advice: ${data.advice}
Reasons:
${(data.reasons || []).map(r => `- ${r}`).join("\n")}`;

        result.innerHTML = `
            <div class="result-top">
                <h2 class="result-title">Analysis Result</h2>
                <span class="badge ${riskClass}">
                    ${riskIcon} ${data.risk}
                </span>
            </div>

            ${
                data.extracted_text !== undefined
                    ? `<div class="section-label">Extracted Text</div>
                       <div class="extracted-box">${data.extracted_text || "No text extracted."}</div>`
                    : ``
            }

            <div class="section-label">Score</div>
            <div class="score-pill">${data.score} risk points detected</div>

            <div class="section-label">Advice</div>
            <div class="advice-box">${data.advice}</div>

            <div class="section-label">Reasons</div>
            ${
                data.reasons && data.reasons.length
                    ? `<ul class="reasons-list">
                        ${data.reasons.map(reason => `<li>${reason}</li>`).join("")}
                       </ul>`
                    : `<div class="empty-state">No specific warning signals were found.</div>`
            }

            <div class="section-label">Insights</div>
            ${
                data.insights && data.insights.length
                    ? `<div class="insights-list">
                        ${data.insights.map(insight => `
                            <div class="insight-card">
                                <div class="insight-title">${insight.title}</div>
                                <div class="insight-text">${insight.explanation}</div>
                            </div>
                        `).join("")}
                       </div>`
                    : `<div class="empty-state">No educational insights available for this scan.</div>`
            }

            <div class="action-row">
                <button class="action-chip" onclick='copyResult(${JSON.stringify(copyText)})'>Copy result</button>
            </div>
        `;

        saveToHistory({
            text: historyText.length > 90 ? historyText.slice(0, 90) + "..." : historyText,
            risk: data.risk,
            score: data.score
        });

    } catch (error) {
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

document.addEventListener("DOMContentLoaded", () => {
    renderHistory();
    handleModeChange();
});