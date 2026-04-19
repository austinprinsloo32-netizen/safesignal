import re
from urllib.parse import urlparse

WEIGHTS = {
    "weak": 1,
    "medium": 2,
    "strong": 4,
    "critical": 6
}

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

INSIGHT_MAP = {
    "urgency": {
        "title": "Urgency Pressure",
        "explanation": "Scammers create panic or time pressure so people act quickly without verifying."
    },
    "credentials": {
        "title": "Credential Harvesting",
        "explanation": "The message appears to be trying to collect passwords, OTPs, PINs, or account access details."
    },
    "money": {
        "title": "Payment Extraction",
        "explanation": "The content pushes for money, fees, refunds, or transfers, which is a common scam goal."
    },
    "impersonation": {
        "title": "Authority Impersonation",
        "explanation": "Scammers often pretend to be trusted institutions or brands to make the message feel legitimate."
    },
    "job_scam": {
        "title": "Job Scam Pattern",
        "explanation": "Fake job offers often promise easy income or request upfront fees for registration, training, or placement."
    },
    "prize_scam": {
        "title": "Prize Bait",
        "explanation": "Messages about winning prizes or rewards are often used to lure people into clicking links or sharing information."
    },
    "sa_specific": {
        "title": "Local Scam Pattern",
        "explanation": "The content matches scam themes commonly seen in South African fraud messages."
    },
    "suspicious_url": {
        "title": "Suspicious Link Structure",
        "explanation": "The URL uses traits often seen in phishing links, such as masking, suspicious keywords, or unusual domain structure."
    },
    "suspicious_sender": {
        "title": "Suspicious Sender Identity",
        "explanation": "The sender information looks inconsistent, manipulative, or unprofessional for a legitimate message."
    }
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


def generate_insights(categories):
    insights = []
    seen = set()

    for category in categories:
        if category in INSIGHT_MAP and category not in seen:
            seen.add(category)
            insights.append({
                "title": INSIGHT_MAP[category]["title"],
                "explanation": INSIGHT_MAP[category]["explanation"]
            })

    return insights


def analyze_patterns(text_lower):
    score = 0
    reasons = []
    categories_found = []

    for category, phrases in SUSPICIOUS_PATTERNS.items():
        for phrase in phrases:
            if phrase in text_lower:
                if category in ["urgency", "job_scam", "prize_scam"]:
                    score += WEIGHTS["weak"]
                elif category in ["credentials", "money"]:
                    score += WEIGHTS["strong"]
                elif category in ["impersonation", "sa_specific"]:
                    score += WEIGHTS["critical"]

                reasons.append(f"Matched {category.replace('_', ' ')} phrase: '{phrase}'")
                categories_found.append(category)

    return score, reasons, categories_found


def analyze_urls(urls):
    score = 0
    reasons = []
    categories_found = []

    if urls:
        score += WEIGHTS["weak"]
        reasons.append("Contains link(s), which increases risk")
        categories_found.append("suspicious_url")

    for url in urls:
        domain = domain_from_url(url)

        if domain in SHORTENER_DOMAINS:
            score += WEIGHTS["strong"]
            reasons.append(f"Uses shortened or suspicious link: '{domain}'")
            categories_found.append("suspicious_url")

        if "@" in url:
            score += WEIGHTS["strong"]
            reasons.append("Link contains '@', which can hide the real destination")
            categories_found.append("suspicious_url")

        if any(char.isdigit() for char in domain) and "." in domain:
            score += WEIGHTS["weak"]
            reasons.append(f"Domain contains unusual numbers: '{domain}'")
            categories_found.append("suspicious_url")

        if domain and not any(hint in domain for hint in SAFE_DOMAINS_HINTS):
            if any(keyword in domain for keyword in ["verify", "secure", "login", "claim", "reward"]):
                score += WEIGHTS["medium"]
                reasons.append(f"Domain looks suspicious: '{domain}'")
                categories_found.append("suspicious_url")

    return score, reasons, categories_found


def analyze_style(text):
    score = 0
    reasons = []
    categories_found = []

    uppercase_words = count_uppercase_words(text)
    exclamations = count_exclamations(text)

    if uppercase_words >= 3:
        score += WEIGHTS["weak"]
        reasons.append("Uses excessive capitalized words to create pressure")
        categories_found.append("urgency")

    if exclamations >= 3:
        score += WEIGHTS["weak"]
        reasons.append("Uses excessive exclamation marks to create urgency")
        categories_found.append("urgency")

    if re.search(r'\b(?:\+27|27|0)\d{9}\b', text.replace(" ", "")):
        score += WEIGHTS["weak"]
        reasons.append("Contains phone-number style contact details often seen in scams")

    return score, reasons, categories_found


def classify_risk(score):
    if score >= 15:
        return "High Risk 🚨", "This looks like a scam. Do NOT click links, send money, or share personal information."
    if score >= 8:
        return "Suspicious ⚠️", "Be careful. Verify the sender using an official contact channel before taking action."
    return "Likely Safe ✅", "No strong scam indicators were found, but stay cautious."


def analyze_text(text):
    text_lower = text.lower()

    score = 0
    reasons = []
    categories_found = []

    pattern_score, pattern_reasons, pattern_categories = analyze_patterns(text_lower)
    score += pattern_score
    reasons.extend(pattern_reasons)
    categories_found.extend(pattern_categories)

    urls = extract_urls(text)
    url_score, url_reasons, url_categories = analyze_urls(urls)
    score += url_score
    reasons.extend(url_reasons)
    categories_found.extend(url_categories)

    style_score, style_reasons, style_categories = analyze_style(text)
    score += style_score
    reasons.extend(style_reasons)
    categories_found.extend(style_categories)

    unique_reasons = list(dict.fromkeys(reasons))
    insights = generate_insights(categories_found)
    risk, advice = classify_risk(score)

    return {
        "risk": risk,
        "score": score,
        "reasons": unique_reasons,
        "insights": insights,
        "advice": advice
    }


def analyze_single_url(url):
    if not url or not url.strip():
        return {
            "risk": "Invalid Input",
            "score": 0,
            "reasons": ["No URL was provided."],
            "insights": [],
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
            "insights": [],
            "advice": "Make sure the link is in a valid format."
        }

    score = 0
    reasons = []
    categories_found = []

    root_domain = extract_root_domain(domain)

    if domain in SHORTENER_DOMAINS or root_domain in SHORTENER_DOMAINS:
        score += WEIGHTS["strong"]
        reasons.append(f"Uses shortened or masked link: '{domain}'")
        categories_found.append("suspicious_url")

    if is_ip_address(domain):
        score += WEIGHTS["critical"]
        reasons.append("Uses an IP address instead of a normal domain")
        categories_found.append("suspicious_url")

    if "@" in original_url:
        score += WEIGHTS["strong"]
        reasons.append("URL contains '@', which can hide the true destination")
        categories_found.append("suspicious_url")

    if "xn--" in domain:
        score += WEIGHTS["critical"]
        reasons.append("Domain contains punycode, which can be used for lookalike scams")
        categories_found.append("suspicious_url")

    if domain.count(".") >= 3:
        score += WEIGHTS["medium"]
        reasons.append("Domain uses many subdomains, which can be suspicious")
        categories_found.append("suspicious_url")

    if any(char.isdigit() for char in domain):
        score += WEIGHTS["weak"]
        reasons.append(f"Domain contains numbers: '{domain}'")
        categories_found.append("suspicious_url")

    if domain.count("-") >= 2:
        score += WEIGHTS["weak"]
        reasons.append("Domain uses many hyphens, which is common in phishing links")
        categories_found.append("suspicious_url")

    if not any(hint in domain for hint in SAFE_DOMAINS_HINTS):
        combined = f"{domain}{path}"
        for keyword in SUSPICIOUS_URL_KEYWORDS:
            if keyword in combined:
                score += WEIGHTS["medium"]
                reasons.append(f"URL contains suspicious keyword: '{keyword}'")
                categories_found.append("suspicious_url")

    unique_reasons = list(dict.fromkeys(reasons))
    insights = generate_insights(categories_found)
    risk, advice = classify_risk(score)

    if not unique_reasons:
        unique_reasons = ["No strong structural scam indicators were found in the URL."]

    return {
        "risk": risk,
        "score": score,
        "reasons": unique_reasons,
        "insights": insights,
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
    categories_found = []

    for insight in result.get("insights", []):
        for key, value in INSIGHT_MAP.items():
            if value["title"] == insight["title"]:
                categories_found.append(key)

    if sender:
        sender_lower = sender.lower()

        if "@" not in sender_lower:
            score += WEIGHTS["medium"]
            reasons.append("Sender format looks unusual or incomplete")
            categories_found.append("suspicious_sender")
        else:
            sender_domain = sender_lower.split("@")[-1]

            if sender_domain in FREE_EMAIL_PROVIDERS:
                score += WEIGHTS["weak"]
                reasons.append(f"Sender uses a free email provider: '{sender_domain}'")
                categories_found.append("suspicious_sender")

            if any(keyword in sender_domain for keyword in ["secure", "verify", "login", "update", "alert"]):
                score += WEIGHTS["strong"]
                reasons.append(f"Sender domain contains suspicious wording: '{sender_domain}'")
                categories_found.append("suspicious_sender")

            if sender_domain.count("-") >= 2:
                score += WEIGHTS["weak"]
                reasons.append("Sender domain uses many hyphens")
                categories_found.append("suspicious_sender")

            if any(char.isdigit() for char in sender_domain):
                score += WEIGHTS["weak"]
                reasons.append("Sender domain contains numbers")
                categories_found.append("suspicious_sender")

    if subject:
        subject_lower = subject.lower()
        if any(word in subject_lower for word in ["urgent", "verify", "suspended", "winner", "refund", "payment"]):
            score += WEIGHTS["strong"]
            reasons.append("Subject line uses urgent or scam-style wording")
            categories_found.append("urgency")

    unique_reasons = list(dict.fromkeys(reasons))
    insights = generate_insights(categories_found)
    risk, advice = classify_risk(score)

    return {
        "risk": risk,
        "score": score,
        "reasons": unique_reasons,
        "insights": insights,
        "advice": advice,
        "sender": sender,
        "subject": subject
    }