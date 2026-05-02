const BASE_URL = "https://safesignal-7j44.onrender.com";
const API_URL = `${BASE_URL}/analyze`;
const DASHBOARD_URL = `${BASE_URL}/dashboard-data`;
const REGISTER_URL = `${BASE_URL}/register`;
const LOGIN_URL = `${BASE_URL}/login`;
const LOGOUT_URL = `${BASE_URL}/logout`;
const ME_URL = `${BASE_URL}/me`;

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

async function checkAuthStatus() {
    try {
        const response = await fetch(ME_URL, {
            method: "GET",
            credentials: "include"
        });

        const data = await response.json();
        updateAuthUI(data);

    } catch (error) {
        console.error("Auth status error:", error);
    }
}

function updateAuthUI(data) {
    const authForm = document.getElementById("authForm");
    const userPanel = document.getElementById("userPanel");
    const authStatus = document.getElementById("authStatus");
    const authUserEmail = document.getElementById("authUserEmail");
    const authMessage = document.getElementById("authMessage");

    if (!authForm || !userPanel) return;

    if (data.logged_in) {
        authForm.classList.add("hidden");
        userPanel.classList.remove("hidden");
        authStatus.textContent = "Your scans are now linked to your account.";
        authUserEmail.textContent = data.user.email;
        if (authMessage) authMessage.textContent = "";
    } else {
        authForm.classList.remove("hidden");
        userPanel.classList.add("hidden");
        authStatus.textContent = "Create an account or log in to save your scans.";
        authUserEmail.textContent = "";
    }
}

async function registerUser() {
    const email = document.getElementById("authEmail").value.trim();
    const password = document.getElementById("authPassword").value;
    const authMessage = document.getElementById("authMessage");

    try {
        const response = await fetch(REGISTER_URL, {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();
        authMessage.textContent = data.message;

        if (data.success) {
            document.getElementById("authPassword").value = "";
            await checkAuthStatus();
            await updateDashboard();
        }

    } catch (error) {
        authMessage.textContent = "Could not register. Please try again.";
        console.error("Register error:", error);
    }
}

async function loginUser() {
    const email = document.getElementById("authEmail").value.trim();
    const password = document.getElementById("authPassword").value;
    const authMessage = document.getElementById("authMessage");

    try {
        const response = await fetch(LOGIN_URL, {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();
        authMessage.textContent = data.message;

        if (data.success) {
            document.getElementById("authPassword").value = "";
            await checkAuthStatus();
            await updateDashboard();
        }

    } catch (error) {
        authMessage.textContent = "Could not log in. Please try again.";
        console.error("Login error:", error);
    }
}

async function logoutUser() {
    try {
        await fetch(LOGOUT_URL, {
            method: "POST",
            credentials: "include"
        });

        await checkAuthStatus();
        await updateDashboard();

    } catch (error) {
        console.error("Logout error:", error);
    }
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

    result.className = "result-card hidden";
    result.innerHTML = "";
}

function saveToHistory(entry) {
    const history = JSON.parse(localStorage.getItem("safesignal_history") || "[]");
    history.unshift(entry);
    const trimmed = history.slice(0, 20);
    localStorage.setItem("safesignal_history", JSON.stringify(trimmed));
    renderHistory();
    updateDashboard();
}

function clearHistory() {
    localStorage.removeItem("safesignal_history");
    renderHistory();
    updateDashboard();
}

function renderHistory() {
    const historyList = document.getElementById("historyList");
    if (!historyList) return;

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

async function updateDashboard() {
    try {
        const response = await fetch(DASHBOARD_URL, {
            method: "GET",
            credentials: "include"
        });

        if (!response.ok) {
            throw new Error("Could not load dashboard data.");
        }

        const data = await response.json();

        const totalScans = document.getElementById("totalScans");
        const highRiskScans = document.getElementById("highRiskScans");
        const mediumRiskScans = document.getElementById("mediumRiskScans");
        const lowRiskScans = document.getElementById("lowRiskScans");
        const rewardBalance = document.getElementById("rewardBalance");

        if (totalScans) totalScans.textContent = data.total_scans;
        if (highRiskScans) highRiskScans.textContent = data.high_risk;
        if (mediumRiskScans) mediumRiskScans.textContent = data.medium_risk;
        if (lowRiskScans) lowRiskScans.textContent = data.low_risk;
        if (rewardBalance) rewardBalance.textContent = `${data.reward_balance} coins`;

    } catch (error) {
        console.error("Dashboard error:", error);
    }
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
            result.innerHTML = `<div class="empty-state">Please fill in the email fields before analyzing.</div>`;
            return;
        }

        payload = { mode: "email", sender, subject, body };
        historyText = `${subject || "No subject"} | ${sender || "No sender"}`;

    } else if (mode === "url") {
        if (!text) {
            result.classList.remove("hidden");
            result.innerHTML = `<div class="empty-state">Please paste a URL before analyzing.</div>`;
            return;
        }

        payload = { mode: "url", url: text };
        historyText = text;

    } else if (mode === "image") {
        const file = imageInput.files[0];

        if (!file) {
            result.classList.remove("hidden");
            result.innerHTML = `<div class="empty-state">Please upload a screenshot before analyzing.</div>`;
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
            result.innerHTML = `<div class="empty-state">Please paste a message or link before analyzing.</div>`;
            return;
        }

        payload = { mode: "text", text };
        historyText = text;
    }

    button.disabled = true;
    btnText.textContent = "Analyzing...";
    btnLoader.classList.remove("hidden");
    result.classList.remove("hidden");

    try {
        const fetchOptions = {
            method: "POST",
            credentials: "include"
        };

        if (useFormData) {
            fetchOptions.body = payload;
        } else {
            fetchOptions.headers = { "Content-Type": "application/json" };
            fetchOptions.body = JSON.stringify(payload);
        }

        const response = await fetch(API_URL, fetchOptions);

        if (!response.ok) {
            throw new Error("Server returned an error.");
        }

        const data = await response.json();
        const riskClass = getRiskClass(data.score);
        const riskIcon = getRiskIcon(data.score);

        result.className = `result-card ${riskClass}`;
        result.classList.remove("hidden");

        document.getElementById("resultBadge").textContent = "Analysis Result";
        document.getElementById("resultTitle").textContent = `${riskIcon} ${data.risk}`;
        document.getElementById("resultScore").textContent = data.score;
        document.getElementById("resultMode").textContent = mode.toUpperCase();

        let confidence = "Medium";
        if (data.ocr_quality) {
            confidence = data.ocr_quality;
        } else if (data.score >= 12) {
            confidence = "High";
        } else if (data.score <= 3) {
            confidence = "Low";
        }

        document.getElementById("resultConfidence").textContent = confidence;

        let summary = "No strong scam indicators were found.";
        if (data.score >= 12) {
            summary = "Multiple strong scam signals were detected. This looks high risk.";
        } else if (data.score >= 6) {
            summary = "Some suspicious patterns were detected. Proceed carefully.";
        } else if (data.legit_reasons && data.legit_reasons.length) {
            summary = "This looks more legitimate based on the detected structure and contact details.";
        }

        document.getElementById("resultSummary").textContent = summary;
        document.getElementById("resultAdvice").textContent = data.advice || "No advice available.";

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

        const ocrMetaBlock = document.getElementById("ocrMetaBlock");
        const extractedTextBlock = document.getElementById("extractedTextBlock");
        const urlsBlock = document.getElementById("urlsBlock");
        const phonesBlock = document.getElementById("phonesBlock");

        if (ocrMetaBlock) ocrMetaBlock.classList.add("hidden");
        if (extractedTextBlock) extractedTextBlock.classList.add("hidden");
        if (urlsBlock) urlsBlock.classList.add("hidden");
        if (phonesBlock) phonesBlock.classList.add("hidden");

        if (data.extracted_text !== undefined) {
            ocrMetaBlock.classList.remove("hidden");
            extractedTextBlock.classList.remove("hidden");

            document.getElementById("ocrQualityText").textContent = data.ocr_quality || "Unknown";
            document.getElementById("ocrConfidenceText").textContent = data.ocr_confidence ?? "0";
            document.getElementById("extractedText").textContent = data.extracted_text || "No text extracted.";

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
        result.className = "result-card";
        result.classList.remove("hidden");
        result.innerHTML = `
            <div class="error-state">
                Could not connect to the backend. Please check that the Render backend service is live.
            </div>
        `;
        console.error("SafeSignal backend error:", error);
    } finally {
        button.disabled = false;
        btnText.textContent = "Analyze";
        btnLoader.classList.add("hidden");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    renderHistory();
    checkAuthStatus();
    updateDashboard();
    handleModeChange();
});