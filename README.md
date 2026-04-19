# 🛡️ SafeSignal

SafeSignal is a web-based scam detection tool that helps users identify phishing attempts, suspicious links, scam-style emails, and social engineering patterns.

It analyzes input using weighted scoring, URL inspection, and scam-pattern detection to give clear, practical feedback — now including screenshot analysis in production.

---

## 🚀 Live Demo
[Try SafeSignal Live](https://safesignal-7j44.onrender.com)

## 💻 GitHub Repository
[View Source Code](https://github.com/austinprinsloo32-netizen/safesignal)

---

## 🔍 Features

### 1. Text Scanner
- Detects scam phrases and social engineering patterns
- Flags urgency, credential requests, and money-related traps
- Provides a risk score, reasons, and advice

---

### 2. URL Scanner
- Analyzes suspicious domains and link structure
- Detects:
  - shortened URLs
  - suspicious keywords
  - excessive subdomains
  - IP-based links
  - unusual domain traits
- Returns a clear risk verdict

---

### 3. Email Scanner
- Structured input:
  - sender
  - subject
  - body
- Detects:
  - suspicious sender domains
  - scam-style subject lines
  - phishing language in email content

---

### 4. Screenshot Scanner (OCR) ✅ NEW
- Upload screenshots of suspicious messages (WhatsApp, SMS, email, etc.)
- Extracts text using **cloud-based OCR (OCR.space API)**
- Runs full scam analysis on extracted content
- Works in both **local and production environments**

---

### 5. Weighted Risk Scoring
- Combines multiple scam indicators using severity-based weights
- Outputs:
  - Likely Safe ✅
  - Suspicious ⚠️
  - High Risk 🚨

---

### 6. Educational Insights
- Explains *why* content looks suspicious
- Highlights tactics like:
  - urgency pressure
  - authority impersonation
  - credential harvesting
  - payment extraction

---

### 7. User Experience
- Clean, modern UI
- Multiple scan modes
- Built-in demo examples
- Browser-based recent scan history
- Copy-to-clipboard results

---

## 🧠 Why I Built This

Scams, phishing, and fake job offers are increasingly common across messaging apps, email, and social platforms.

SafeSignal was built to:
- help everyday users quickly assess suspicious content
- reduce the risk of falling for scams
- teach users how scam tactics work

---

## 🛠️ Tech Stack

- **Backend:** Python, Flask
- **Frontend:** HTML, CSS, JavaScript
- **OCR:** OCR.space API (cloud-based), Pillow (image preprocessing)
- **Deployment:** Render
- **Other:**
  - LocalStorage
  - Fetch API

---

## ⚙️ Run Locally

### 1. Clone the repository
```bash
git clone https://github.com/austinprinsloo32-netizen/safesignal.git
cd safesignal