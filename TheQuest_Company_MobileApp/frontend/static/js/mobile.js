/**
 * The Quest Hotel - Mobile Portal Interactive Scripts
 * Slogan: "We shall never deny a guest, even the most ridiculous request"
 */

document.addEventListener("DOMContentLoaded", function () {
  initDeviceSimulator();
  initSoftphone();
  initLockoutTimer();
});

/* ==============================================================================
   1. DEVICE SIMULATOR TOGGLE (Phone Frame vs Full Responsive Width)
============================================================================== */
function initDeviceSimulator() {
  const btnFrame = document.getElementById("btn-view-frame");
  const btnFull = document.getElementById("btn-view-full");
  const body = document.body;

  if (!btnFrame || !btnFull) return;

  // Restore saved view preference (default to phone frame on desktop)
  const savedView = localStorage.getItem("quest_mobile_view_mode") || "frame";
  if (savedView === "full") {
    body.classList.remove("device-frame-mode");
    body.classList.add("full-width-mode");
    btnFull.classList.add("active");
    btnFrame.classList.remove("active");
  } else {
    body.classList.add("device-frame-mode");
    body.classList.remove("full-width-mode");
    btnFrame.classList.add("active");
    btnFull.classList.remove("active");
  }

  btnFrame.addEventListener("click", function () {
    body.classList.add("device-frame-mode");
    body.classList.remove("full-width-mode");
    btnFrame.classList.add("active");
    btnFull.classList.remove("active");
    localStorage.setItem("quest_mobile_view_mode", "frame");
  });

  btnFull.addEventListener("click", function () {
    body.classList.remove("device-frame-mode");
    body.classList.add("full-width-mode");
    btnFull.classList.add("active");
    btnFrame.classList.remove("active");
    localStorage.setItem("quest_mobile_view_mode", "full");
  });
}

/* ==============================================================================
   2. INTERACTIVE SOFTPHONE CALL SYSTEM
============================================================================== */
let softphoneState = {
  isConnected: false,
  startTime: null,
  timerInterval: null,
  durationSeconds: 0,
  contactName: "Staff Member",
  roleTitle: "Staff",
  isMuted: false
};

function initSoftphone() {
  const modal = document.getElementById("softphone-modal");
  const endBtn = document.getElementById("softphone-end-btn");
  const muteBtn = document.getElementById("softphone-mute-btn");
  const speakerBtn = document.getElementById("softphone-speaker-btn");

  if (!modal) return;

  if (endBtn) {
    endBtn.addEventListener("click", endSoftphoneCall);
  }

  if (muteBtn) {
    muteBtn.addEventListener("click", function () {
      softphoneState.isMuted = !softphoneState.isMuted;
      muteBtn.classList.toggle("active", softphoneState.isMuted);
      muteBtn.innerHTML = softphoneState.isMuted ? "🔇" : "🎤";
    });
  }

  if (speakerBtn) {
    speakerBtn.addEventListener("click", function () {
      speakerBtn.classList.toggle("active");
    });
  }
}

window.startSoftphoneCall = function (name, phone, role, imagePath) {
  const modal = document.getElementById("softphone-modal");
  if (!modal) return;

  softphoneState.contactName = name || "Staff Dispatch";
  softphoneState.roleTitle = role || "Staff Member";
  softphoneState.durationSeconds = 0;
  softphoneState.isConnected = false;
  softphoneState.isMuted = false;

  // Set modal elements
  document.getElementById("call-contact-name").textContent = softphoneState.contactName;
  document.getElementById("call-contact-role").textContent = softphoneState.roleTitle;
  document.getElementById("call-contact-number").textContent = phone || "+63 900 000 0000";
  document.getElementById("call-timer-text").textContent = "00:00";

  const avatarImg = document.getElementById("call-contact-avatar");
  if (avatarImg) {
    avatarImg.src = imagePath || "/assets/imgs/employees/m/1.jpg";
  }

  const statusLabel = document.getElementById("call-status-label");
  statusLabel.className = "call-status-label";
  statusLabel.textContent = "Dialing...";

  modal.classList.add("open");

  // Call sequence: Dialing -> Ringing -> Connected
  setTimeout(() => {
    if (modal.classList.contains("open") && !softphoneState.isConnected) {
      statusLabel.textContent = "Ringing... 📳";
    }
  }, 900);

  setTimeout(() => {
    if (modal.classList.contains("open")) {
      connectSoftphoneCall();
    }
  }, 2300);
};

function connectSoftphoneCall() {
  softphoneState.isConnected = true;
  softphoneState.startTime = Date.now();
  const statusLabel = document.getElementById("call-status-label");
  statusLabel.className = "call-status-label connected";
  statusLabel.textContent = "Connected (Live Audio) 🟢";

  if (softphoneState.timerInterval) clearInterval(softphoneState.timerInterval);

  softphoneState.timerInterval = setInterval(() => {
    softphoneState.durationSeconds = Math.floor((Date.now() - softphoneState.startTime) / 1000);
    const mins = String(Math.floor(softphoneState.durationSeconds / 60)).padStart(2, "0");
    const secs = String(softphoneState.durationSeconds % 60).padStart(2, "0");
    const timerElem = document.getElementById("call-timer-text");
    if (timerElem) timerElem.textContent = `${mins}:${secs}`;
  }, 1000);
}

function endSoftphoneCall() {
  if (softphoneState.timerInterval) {
    clearInterval(softphoneState.timerInterval);
    softphoneState.timerInterval = null;
  }

  const modal = document.getElementById("softphone-modal");
  if (modal) modal.classList.remove("open");

  const mins = Math.floor(softphoneState.durationSeconds / 60);
  const secs = softphoneState.durationSeconds % 60;
  const durStr = mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;

  if (softphoneState.durationSeconds > 0) {
    alert(`📞 Call Ended with ${softphoneState.contactName} (${softphoneState.roleTitle})\nDuration: ${durStr}`);
  }
}

/* ==============================================================================
   3. BRUTE-FORCE LOCKOUT COUNTDOWN
============================================================================== */
function initLockoutTimer() {
  const banner = document.getElementById("lockout-banner");
  if (!banner) return;

  let remaining = parseInt(banner.getAttribute("data-seconds") || "0", 10);
  if (remaining <= 0) return;

  const submitBtn = document.getElementById("btn-login-submit");
  const usernameInput = document.getElementById("input-username");
  const passwordInput = document.getElementById("input-password");

  if (submitBtn) submitBtn.disabled = true;
  if (usernameInput) usernameInput.disabled = true;
  if (passwordInput) passwordInput.disabled = true;

  const interval = setInterval(() => {
    remaining--;
    if (remaining > 0) {
      banner.textContent = `⚠️ System locked due to 3 failed attempts. Try again in ${remaining}s.`;
    } else {
      clearInterval(interval);
      banner.style.display = "none";
      if (submitBtn) submitBtn.disabled = false;
      if (usernameInput) usernameInput.disabled = false;
      if (passwordInput) passwordInput.disabled = false;
    }
  }, 1000);
}

/* ==============================================================================
   4. BOTTOM SHEET & MODAL HELPERS
============================================================================== */
window.openSheet = function (sheetId) {
  const elem = document.getElementById(sheetId);
  if (elem) elem.classList.add("open");
};

window.closeSheet = function (sheetId) {
  const elem = document.getElementById(sheetId);
  if (elem) elem.classList.remove("open");
};

/* Close bottom sheet when tapping backdrop */
document.addEventListener("click", function (e) {
  if (e.target.classList.contains("bottom-sheet-backdrop")) {
    e.target.classList.remove("open");
  }
});
