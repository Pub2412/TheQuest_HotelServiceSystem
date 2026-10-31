/**
 * The Quest Hotel - Luxury Guest Mobile Application JavaScript
 */

function showToast(message, isSuccess = true) {
  let toast = document.getElementById("mobileToast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "mobileToast";
    document.body.appendChild(toast);
  }
  toast.className = "mobile-toast " + (isSuccess ? "toast-success" : "toast-error");
  toast.innerText = message;
  toast.style.display = "block";
  setTimeout(() => {
    toast.style.display = "none";
  }, 4500);
}

// Live Stay Countdown Clock
function initCountdown(targetIso) {
  if (!targetIso) return;
  const targetDate = new Date(targetIso).getTime();

  function update() {
    const now = new Date().getTime();
    const distance = targetDate - now;

    if (distance <= 0) {
      const d = document.getElementById("cd-days");
      const h = document.getElementById("cd-hours");
      const m = document.getElementById("cd-mins");
      const s = document.getElementById("cd-secs");
      if (d) d.innerText = "00";
      if (h) h.innerText = "00";
      if (m) m.innerText = "00";
      if (s) s.innerText = "00";
      const badge = document.getElementById("stayCountdownBadge");
      if (badge) badge.innerText = "Checkout Due / Overdue";
      return;
    }

    const days = Math.floor(distance / (1000 * 60 * 60 * 24));
    const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((distance % (1000 * 60)) / 1000);

    const d = document.getElementById("cd-days");
    const h = document.getElementById("cd-hours");
    const m = document.getElementById("cd-mins");
    const s = document.getElementById("cd-secs");
    if (d) d.innerText = String(days).padStart(2, "0");
    if (h) h.innerText = String(hours).padStart(2, "0");
    if (m) m.innerText = String(minutes).padStart(2, "0");
    if (s) s.innerText = String(seconds).padStart(2, "0");
  }

  update();
  setInterval(update, 1000);
}

// Digital Room Key & Door Unlock Logic
async function unlockDoor(method, keyToken = null) {
  const wifiSelect = document.getElementById("wifiSelect");
  const wifiSSID = wifiSelect ? wifiSelect.value : "";
  const statusCard = document.getElementById("doorStatusCard");
  const lockIcon = document.getElementById("lockIcon");
  const lockText = document.getElementById("lockStatusText");

  try {
    const res = await fetch("/api/door/unlock", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        method: method,
        wifi_ssid: wifiSSID,
        key_token: keyToken
      })
    });
    const data = await res.json();

    if (data.success) {
      showToast(data.message, true);
      if (statusCard) {
        statusCard.className = "door-lock-display unlocked";
        if (lockIcon) lockIcon.innerText = "🔓";
        if (lockText) lockText.innerText = "DOOR UNLOCKED — WELCOME";
      }

      // Auto relock after 5 seconds
      setTimeout(() => {
        if (statusCard) {
          statusCard.className = "door-lock-display locked";
          if (lockIcon) lockIcon.innerText = "🔒";
          if (lockText) lockText.innerText = "DOOR LOCKED";
        }
      }, 5000);
    } else {
      showToast(data.message, false);
    }
  } catch (err) {
    showToast("Door unlock communication failed: " + err, false);
  }
}

// Web NFC API integration with tap simulation fallback
async function handleNfcTap(keyToken) {
  if ("NDEFReader" in window) {
    try {
      const ndef = new NDEFReader();
      await ndef.scan();
      showToast("NFC sensor active! Tap your phone to the door lock reader...", true);
      ndef.onreading = event => {
        unlockDoor("nfc", keyToken);
      };
      // Also proceed directly so user doesn't get blocked if no physical card is present
      setTimeout(() => {
        unlockDoor("nfc", keyToken);
      }, 600);
      return;
    } catch (e) {
      console.log("Web NFC unavailable or denied, falling back to instant NFC proximity beam:", e);
    }
  }
  // Instant NFC Proximity Beam simulation
  unlockDoor("nfc", keyToken);
}

// Modal Sheet Helpers
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.style.display = "flex";
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.style.display = "none";
}

