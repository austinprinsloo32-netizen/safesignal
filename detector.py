import re
from urllib.parse import urlparse


SUSPICIOUS_PATTERNS = {
    "urgency": [
        "urgent", "immediately", "act now", "last chance", "final warning",
        "suspended", "expire", "expires today", "limited time", "now now"
    ],
    "credentials": [
        "verify your account", "confirm your account", "password", "otp",
        "pin", "login", "banking details", "security code", "username"
    ],
    "money": [
        "payment", "pay now", "deposit", "release fee", "clearance fee",
        "processing fee", "transfer funds", "claim now", "refund", "cashout"
    ],
    "impersonation": [
        "bank", "sars", "courier", "customs", "hr department", "recruiter",
        "microsoft", "paypal", "capitec", "fnb", "absa", "nedbank", "standard bank"
    ],
    "job_scam": [
        "job offer", "registration fee", "training fee", "work from home",
        "earn daily", "earn per day", "no experience needed"
    ],
    "prize_scam": [
        "winner", "you have won", "congratulations", "prize", "lottery",
        "claim your reward", "gift"
    ],
    "sa_specific": [
        "sars refund", "parcel release", "clear your parcel", "ewallet reversal",
        "bank verification", "sim swap", "load shedding grant"
    ]
}

SHORTENER_DOMAINS = {
    "bit.ly", "tinyurl.com", "goo.gl", "t.co", "is.gd", "ow.ly", "buff.ly", "grabify.link"
}

SAFE_DOMAINS_HINTS = {
    "gov.za", "sars.gov.za", "bank.co.za"
}

SUSPICIOUS_URL_KEYWORDS = {
    "verify", "secure", "login", "claim", "reward", "update",
    "bank", "wallet", "confirm", "password", "account", "pay"
}

FREE_EMAIL_PROVIDERS = {
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com", "proton.me"
}


def extract_urls(text):
    return re.findall(r'https?://[^\s]+', text)


def count_uppercase_words(text):
    words = re.findall(r'\b[A-Z]{3,}\b', text)
    return len(words)


def count_exclamations(text):
    return text.count("!")


def domain_from_url(url):
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower().replace("www.", "")
    except Exception:
        return ""


def extract_root_domain(domain):
    parts = domain.split(".")
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return domain


def is_ip_address(domain):
    return bool(re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", domain))


def analyze_patterns(text_lower):
    score = 0
    reasons = []

    for category, phrases in SUSPICIOUS_PATTERNS.items():
        for phrase in phrases:
            if phrase in text_lower:
                score += 1
                reasons.append(f"Matched {category.replace('_', ' ')} phrase: '{phrase}'")

    return score, reasons


def analyze_urls(urls):
    score = 0
    reasons = []

    if urls:
        score += len(urls)
        reasons.append("Contains link(s), which increases risk")

    for url in urls:
        domain = domain_from_url(url)

        if domain in SHORTENER_DOMAINS:
            score += 3
            reasons.append(f"Uses shortened or suspicious link: '{domain}'")

        if "@" in url:
            score += 2
            reasons.append("Link contains '@', which can hide the real destination")

        if any(char.isdigit() for char in domain) and "." in domain:
            score += 1
            reasons.append(f"Domain contains unusual numbers: '{domain}'")

        if domain and not any(hint in domain for hint in SAFE_DOMAINS_HINTS):
            if any(keyword in domain for keyword in ["verify", "secure", "login", "claim", "reward"]):
                score += 2
                reasons.append(f"Domain looks suspicious: '{domain}'")

    return score, reasons


def analyze_style(text):
    score = 0
    reasons = []

    uppercase_words = count_uppercase_words(text)
    exclamations = count_exclamations(text)

    if uppercase_words >= 3:
        score += 1
        reasons.append("Uses excessive capitalized words to create pressure")

    if exclamations >= 3:
        score += 1
        reasons.append("Uses excessive exclamation marks to create urgency")

    if re.search(r'\b(?:\+27|27|0)\d{9}\b', text.replace(" ", "")):
        score += 1
        reasons.append("Contains phone-number style contact details often seen in scams")

    return score, reasons


def classify_risk(score):
    if score >= 8:
        return "High Risk 🚨", "Do NOT click links, send money, or share personal information."
    if score >= 4:
        return "Suspicious ⚠️", "Be careful. Verify the sender using an official contact channel."
    return "Likely Safe ✅", "No strong scam indicators were found, but stay cautious."


def analyze_text(text):
    text_lower = text.lower()

    score = 0
    reasons = []

    pattern_score, pattern_reasons = analyze_patterns(text_lower)
    score += pattern_score
    reasons.extend(pattern_reasons)

    urls = extract_urls(text)
    url_score, url_reasons = analyze_urls(urls)
    score += url_score
    reasons.extend(url_reasons)

    style_score, style_reasons = analyze_style(text)
    score += style_score
    reasons.extend(style_reasons)

    unique_reasons = list(dict.fromkeys(reasons))

    risk, advice = classify_risk(score)

    return {
        "risk": risk,
        "score": score,
        "reasons": unique_reasons,
        "advice": advice
    }


def analyze_single_url(url):
    if not url or not url.strip():
        return {
            "risk": "Invalid Input",
            "score": 0,
            "reasons": ["No URL was provided."],
            "advice": "Paste a full link to analyze it."
        }

    original_url = url.strip()

    if not original_url.startswith(("http://", "https://")):
        original_url = "http://" + original_url

    parsed = urlparse(original_url)
    domain = parsed.netloc.lower().replace("www.", "")
    path = parsed.path.lower()

    if not domain:
        return {
            "risk": "Invalid Input",
            "score": 0,
            "reasons": ["Could not read a valid domain from that URL."],
            "advice": "Make sure the link is in a valid format."
        }

    score = 0
    reasons = []

    root_domain = extract_root_domain(domain)

    if domain in SHORTENER_DOMAINS or root_domain in SHORTENER_DOMAINS:
        score += 3
        reasons.append(f"Uses shortened or masked link: '{domain}'")

    if is_ip_address(domain):
        score += 3
        reasons.append("Uses an IP address instead of a normal domain")

    if "@" in original_url:
        score += 2
        reasons.append("URL contains '@', which can hide the true destination")

    if "xn--" in domain:
        score += 3
        reasons.append("Domain contains punycode, which can be used for lookalike scams")

    if domain.count(".") >= 3:
        score += 2
        reasons.append("Domain uses many subdomains, which can be suspicious")

    if any(char.isdigit() for char in domain):
        score += 1
        reasons.append(f"Domain contains numbers: '{domain}'")

    if domain.count("-") >= 2:
        score += 1
        reasons.append("Domain uses many hyphens, which is common in phishing links")

    if not any(hint in domain for hint in SAFE_DOMAINS_HINTS):
        combined = f"{domain}{path}"
        for keyword in SUSPICIOUS_URL_KEYWORDS:
            if keyword in combined:
                score += 2
                reasons.append(f"URL contains suspicious keyword: '{keyword}'")

    risk, advice = classify_risk(score)

    unique_reasons = list(dict.fromkeys(reasons))

    if not unique_reasons:
        unique_reasons = ["No strong structural scam indicators were found in the URL."]

    return {
        "risk": risk,
        "score": score,
        "reasons": unique_reasons,
        "advice": advice,
        "domain": domain
    }


def analyze_email(sender, subject, body):
    sender = (sender or "").strip()
    subject = (subject or "").strip()
    body = (body or "").strip()

    combined_text = f"{subject}\n{body}"
    result = analyze_text(combined_text)

    score = result["score"]
    reasons = list(result["reasons"])

    if sender:
        sender_lower = sender.lower()

        if "@" not in sender_lower:
            score += 2
            reasons.append("Sender format looks unusual or incomplete")
        else:
            sender_domain = sender_lower.split("@")[-1]

            if sender_domain in FREE_EMAIL_PROVIDERS:
                score += 1
                reasons.append(f"Sender uses a free email provider: '{sender_domain}'")

            if any(keyword in sender_domain for keyword in ["secure", "verify", "login", "update", "alert"]):
                score += 2
                reasons.append(f"Sender domain contains suspicious wording: '{sender_domain}'")

            if sender_domain.count("-") >= 2:
                score += 1
                reasons.append("Sender domain uses many hyphens")

            if any(char.isdigit() for char in sender_domain):
                score += 1
                reasons.append("Sender domain contains numbers")

    if subject:
        subject_lower = subject.lower()
        if any(word in subject_lower for word in ["urgent", "verify", "suspended", "winner", "refund", "payment"]):
            score += 2
            reasons.append("Subject line uses urgent or scam-style wording")

    unique_reasons = list(dict.fromkeys(reasons))
    risk, advice = classify_risk(score)

    return {
        "risk": risk,
        "score": score,
        "reasons": unique_reasons,
        "advice": advice,
        "sender": sender,
        "subject": subject
    }