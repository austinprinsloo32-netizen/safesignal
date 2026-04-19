# 🛡️ SafeSignal

SafeSignal is a web-based scam detection tool that helps users identify phishing attempts, suspicious links, and scam-style messages in seconds.

It analyzes input using pattern detection, URL inspection, and risk scoring to give clear, actionable feedback.

---

## 🚀 Live Demo
[Try SafeSignal Live](https://safesignal-7j44.onrender.com)

## 💻 GitHub Repository
[View Source Code](https://github.com/austinprinsloo32-netizen)

---

## 🔍 Features

### 1. Text Scanner
- Detects scam phrases and social engineering patterns
- Flags urgency, credential requests, and financial traps
- Provides a risk score and explanation

### 2. URL Scanner
- Analyzes domains and link structure
- Detects:
  - shortened URLs
  - suspicious keywords
  - excessive subdomains
  - IP-based links
- Returns a clear risk verdict

### 3. Email Scanner
- Structured input:
  - sender
  - subject
  - body
- Detects:
  - suspicious sender domains
  - scam-style subject lines
  - phishing language in email content

### 4. Risk Scoring System
- Combines multiple detection signals
- Outputs:
  - Likely Safe ✅
  - Suspicious ⚠️
  - High Risk 🚨

### 5. Educational Feedback
- Explains *why* something looks suspicious
- Helps users learn scam patterns

### 6. User Experience
- Clean, modern UI
- Mode switching (Text / URL / Email)
- Demo examples
- Local scan history
- Copy-to-clipboard results

---

## 🧠 Why I Built This

Scams, phishing, and fake job offers are increasingly common — especially across messaging apps, email, and social media.

SafeSignal was built to:
- help everyday users quickly assess risk
- reduce the chances of falling for scams
- teach users how scam tactics work

---

## 🛠️ Tech Stack

- **Backend:** Python, Flask
- **Frontend:** HTML, CSS, JavaScript
- **Other:**
  - LocalStorage (scan history)
  - Fetch API (frontend → backend communication)

---

## ⚙️ Run Locally

### 1. Clone the repository
```bash
git clone https://github.com/austinprinsloo32-netizen/safesignal
cd safesignal