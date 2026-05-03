const RENDER_URL = "https://safesignal-7j44.onrender.com/analyze";
const APP_URL = "https://safesignal-7j44.onrender.com";

function fillList(elementId, items, fallback) {
  const el = document.getElementById(elementId);
  el.innerHTML = "";

  if (items && items.length) {
    items.forEach(item => {
      const li = document.createElement("li");
      li.textContent = item;
      el.appendChild(li);
    });
  } else {
    const li = document.createElement("li");
    li.textContent = fallback;
    el.appendChild(li);
  }
}

function getModePayload(mode, content) {
  if (mode === "url") {
    return { mode: "url", url: content };
  }

  return { mode: "text", text: content };
}

document.getElementById("analyzeBtn").addEventListener("click", async () => {
  const mode = document.getElementById("mode").value;
  const content = document.getElementById("content").value.trim();

  if (!content) {
    alert("Paste some text or a URL first.");
    return;
  }

  try {
    const response = await fetch(RENDER_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      credentials: "include",
      body: JSON.stringify(getModePayload(mode, content))
    });

    const data = await response.json();

    document.getElementById("result").classList.remove("hidden");

    if (response.status === 403 && data.error === "limit_reached") {
      document.getElementById("riskLabel").textContent = "Free limit reached";
      document.getElementById("scoreBox").textContent = "5/5";
      document.getElementById("advice").innerHTML = `
        You used your free scans for today.<br><br>
        Open SafeSignal to unlock more scans.<br><br>
        <button id="openAppBtn">Unlock more scans</button>
      `;

      fillList("reasons", ["Daily free scan limit reached."], "Daily limit reached.");
      fillList("legitReasons", ["You can unlock more scans from the main app."], "Open SafeSignal.");

      return;
    }

    if (!response.ok) {
      throw new Error("Server returned an error.");
    }

    document.getElementById("riskLabel").textContent = data.risk;
    document.getElementById("scoreBox").textContent = data.score;
    document.getElementById("advice").textContent = data.advice || "No advice available.";

    fillList("reasons", data.reasons, "No specific warning signals found.");
    fillList("legitReasons", data.legit_reasons, "No strong legitimacy signals detected.");

  } catch (error) {
    alert("Could not connect to SafeSignal.");
    console.error(error);
  }
});

document.getElementById("useSelectionBtn").addEventListener("click", async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  if (!tab?.id || tab.url.startsWith("chrome://")) {
    alert("Selected text cannot be used on Chrome internal pages. Try it on a normal website.");
    return;
  }

  try {
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => window.getSelection().toString()
    });

    const selectedText = results?.[0]?.result || "";

    if (!selectedText) {
      alert("No text selected on the page.");
      return;
    }

    document.getElementById("content").value = selectedText;

  } catch (error) {
    alert("Could not access selected text on this page.");
    console.error(error);
  }
});

document.addEventListener("DOMContentLoaded", async () => {
  const { pendingSelection } = await chrome.storage.local.get("pendingSelection");

  if (pendingSelection) {
    document.getElementById("content").value = pendingSelection;
    await chrome.storage.local.remove("pendingSelection");
  }
});
document.addEventListener("click", (e) => {
  if (e.target.id === "openAppBtn") {
    chrome.tabs.create({ url: APP_URL });
  }
});