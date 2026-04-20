const RENDER_URL = "https://safesignal-7j44.onrender.com/analyze";

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
      body: JSON.stringify(getModePayload(mode, content))
    });

    if (!response.ok) {
      throw new Error("Server returned an error.");
    }

    const data = await response.json();

    document.getElementById("result").classList.remove("hidden");
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

  if (!tab?.id) return;

  const results = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => window.getSelection().toString()
  });

  const selectedText = results?.[0]?.result || "";
  document.getElementById("content").value = selectedText;
});

document.addEventListener("DOMContentLoaded", async () => {
  const { pendingSelection } = await chrome.storage.local.get("pendingSelection");
  if (pendingSelection) {
    document.getElementById("content").value = pendingSelection;
    await chrome.storage.local.remove("pendingSelection");
  }
});