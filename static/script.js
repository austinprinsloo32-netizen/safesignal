function getRiskClass(score) {
    if (score >= 8) return "high";
    if (score >= 4) return "medium";
    return "low";
}

function getRiskIcon(score) {
    if (score >= 8) return "🚨";
    if (score >= 4) return "⚠️";
    return "✅";
}

function loadExample(type) {
    const textArea = document.getElementById("inputText");

    const examples = {
        bank: "URGENT! Your bank account is suspended. Verify now using your OTP at http://bit.ly/test",
        job: "Congratulations, your job offer has been approved. Pay a registration fee today to secure your position.",
        safe: "Hi Austin, just confirming our meeting for tomorrow at 10:00."
    };

    textArea.value = examples[type] || "";
}

function clearAll() {
    document.getElementById("inputText").value = "";
    const result = document.getElementById("result");
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
    const textArea = document.getElementById("inputText");
    const result = document.getElementById("result");
    const button = document.getElementById("analyzeBtn");
    const btnText = button.querySelector(".btn-text");
    const btnLoader = button.querySelector(".btn-loader");

    const text = textArea.value.trim();

    if (!text) {
        result.classList.remove("hidden");
        result.innerHTML = `
            <div class="empty-state">
                Please paste a message or link before analyzing.
            </div>
        `;
        return;
    }

    button.disabled = true;
    btnText.textContent = "Analyzing...";
    btnLoader.classList.remove("hidden");

    result.classList.remove("hidden");
    result.innerHTML = `
        <div class="empty-state">Checking message for scam signals...</div>
    `;

    try {
    const response = await fetch("/analyze", {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    body: JSON.stringify({ text })
});

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

            <div class="action-row">
                <button class="action-chip" onclick='copyResult(${JSON.stringify(copyText)})'>Copy result</button>
            </div>
        `;

        saveToHistory({
            text: text.length > 90 ? text.slice(0, 90) + "..." : text,
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

document.addEventListener("DOMContentLoaded", renderHistory);