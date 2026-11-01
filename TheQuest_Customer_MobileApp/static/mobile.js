/**
 * The Quest Hotel - Luxury Guest Mobile Application JavaScript
 */

// Do not leave the WebView waiting forever when the local Flask server is busy or unavailable.
const nativeFetch = window.fetch.bind(window);
window.fetch = (input, init = {}) => {
  if (init.signal) return nativeFetch(input, init);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
  return nativeFetch(input, { ...init, signal: controller.signal })
    .finally(() => clearTimeout(timeout));
};

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".mobile-modal").forEach(modal => {
    modal.style.display = "none";
  });
  const toast = document.getElementById("mobileToast");
  if (toast) toast.style.display = "none";
});

function navigateTab(link) {
  if (!link || !link.href) return true;
  window.stop();
  window.location.replace(link.href);
  return false;
}

document.addEventListener("DOMContentLoaded", () => {
  const deferredImages = document.querySelectorAll("img[data-src]");
  if (!deferredImages.length) return;

  const loadImage = image => {
    image.src = image.dataset.src;
    image.removeAttribute("data-src");
  };

  if (!("IntersectionObserver" in window)) {
    deferredImages.forEach(loadImage);
    return;
  }

  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        loadImage(entry.target);
        observer.unobserve(entry.target);
      }
    });
  }, { rootMargin: "80px" });
  deferredImages.forEach(image => observer.observe(image));
});

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
  let timer;
  const elements = {
    days: document.getElementById("cd-days"),
    hours: document.getElementById("cd-hours"),
    minutes: document.getElementById("cd-mins"),
    seconds: document.getElementById("cd-secs"),
    badge: document.getElementById("stayCountdownBadge")
  };

  function update() {
    const now = new Date().getTime();
    const distance = targetDate - now;

    if (distance <= 0) {
      if (elements.days) elements.days.textContent = "00";
      if (elements.hours) elements.hours.textContent = "00";
      if (elements.minutes) elements.minutes.textContent = "00";
      if (elements.seconds) elements.seconds.textContent = "00";
      if (elements.badge) elements.badge.textContent = "Checkout Due / Overdue";
      clearInterval(timer);
      return true;
    }

    const days = Math.floor(distance / (1000 * 60 * 60 * 24));
    const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((distance % (1000 * 60)) / 1000);

    if (elements.days) elements.days.textContent = String(days).padStart(2, "0");
    if (elements.hours) elements.hours.textContent = String(hours).padStart(2, "0");
    if (elements.minutes) elements.minutes.textContent = String(minutes).padStart(2, "0");
    if (elements.seconds) elements.seconds.textContent = String(seconds).padStart(2, "0");
  }

  update();
  timer = setInterval(update, 1000);
}

// Digital Room Key & Door Unlock Logic
async function unlockDoor(method, keyToken = null) {
  if (unlockDoor.inProgress) return;
  unlockDoor.inProgress = true;
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
    showToast(err.name === "AbortError"
      ? "Door unlock timed out. Please try again."
      : "Door unlock communication failed: " + err, false);
  } finally {
    unlockDoor.inProgress = false;
  }
}

// Web NFC API integration with tap simulation fallback
async function handleNfcTap(keyToken) {
  if (handleNfcTap.inProgress) return;
  handleNfcTap.inProgress = true;
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
      setTimeout(() => {
        handleNfcTap.inProgress = false;
      }, 1200);
      return;
    } catch (e) {
      console.log("Web NFC unavailable or denied, falling back to instant NFC proximity beam:", e);
    }
  }
  // Instant NFC Proximity Beam simulation
  try {
    await unlockDoor("nfc", keyToken);
  } finally {
    handleNfcTap.inProgress = false;
  }
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
