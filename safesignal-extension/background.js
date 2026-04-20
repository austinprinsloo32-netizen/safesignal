chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "safesignal-check-selection",
    title: "Check selected text with SafeSignal",
    contexts: ["selection"]
  });
});

chrome.contextMenus.onClicked.addListener((info) => {
  if (info.menuItemId === "safesignal-check-selection" && info.selectionText) {
    chrome.storage.local.set({
      pendingSelection: info.selectionText
    });
  }
});