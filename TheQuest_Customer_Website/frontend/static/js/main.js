/**
 * THE QUEST HOTEL - CUSTOMER PORTAL CLIENT CONTROLLER
 * Theme: Royal Purple & Warm Amber Gold
 * Tagline: "We shall never deny a guest, even the most ridiculous request"
 */

// ==============================================================================
// GLOBAL STATE & VARIABLES
// ==============================================================================
const QuestApp = {
  cart: [],
  currentSlide: 0,
  carouselTimer: null,
  stayCountdownInterval: null,
  lockoutTimer: null,
  lockoutSecondsLeft: 0
};

// ==============================================================================
// DOM READY INITIALIZATION
// ==============================================================================
document.addEventListener("DOMContentLoaded", () => {
  initPromotionalCarousel();
  initStayCountdown();
  initAuthHandlers();
  initDiningCart();
  initBookingHandlers();
  initChatHandlers();
  initNavbarScroll();
  checkUrlParams();
});

// ==============================================================================
// 1. PROMOTIONAL CAROUSEL (AUTOMATIC & MANUAL CYCLING)
// ==============================================================================
function initPromotionalCarousel() {
  const slides = document.querySelectorAll(".carousel-slide");
  const dots = document.querySelectorAll(".indicator-dot");
  const prevBtn = document.querySelector(".carousel-btn.prev");
  const nextBtn = document.querySelector(".carousel-btn.next");
  const carouselContainer = document.querySelector(".carousel-container");

  if (!slides || slides.length === 0) return;

  function showSlide(index) {
    slides.forEach((s) => s.classList.remove("active"));
    dots.forEach((d) => d.classList.remove("active"));

    QuestApp.currentSlide = (index + slides.length) % slides.length;
    slides[QuestApp.currentSlide].classList.add("active");
    if (dots[QuestApp.currentSlide]) {
      dots[QuestApp.currentSlide].classList.add("active");
    }
  }

  function nextSlide() {
    showSlide(QuestApp.currentSlide + 1);
  }

  function prevSlide() {
    showSlide(QuestApp.currentSlide - 1);
  }

  function startAutoCycle() {
    stopAutoCycle();
    QuestApp.carouselTimer = setInterval(nextSlide, 5000); // 5-second automatic rotation
  }

  function stopAutoCycle() {
    if (QuestApp.carouselTimer) {
      clearInterval(QuestApp.carouselTimer);
      QuestApp.carouselTimer = null;
    }
  }

  if (nextBtn) nextBtn.addEventListener("click", () => { nextSlide(); startAutoCycle(); });
  if (prevBtn) prevBtn.addEventListener("click", () => { prevSlide(); startAutoCycle(); });

  dots.forEach((dot, idx) => {
    dot.addEventListener("click", () => {
      showSlide(idx);
      startAutoCycle();
    });
  });

  if (carouselContainer) {
    carouselContainer.addEventListener("mouseenter", stopAutoCycle);
    carouselContainer.addEventListener("mouseleave", startAutoCycle);
  }

  // Start initial auto cycle
  startAutoCycle();
}

// ==============================================================================
// 2. LIVE STAY DURATION COUNTDOWN (CHECKED-IN GUESTS)
// ==============================================================================
function initStayCountdown() {
  const countdownEl = document.getElementById("stay-countdown");
  if (!countdownEl) return;

  const targetIso = countdownEl.dataset.targetIso;
  if (!targetIso) return;

  const targetDate = new Date(targetIso).getTime();

  function updateTimer() {
    const now = new Date().getTime();
    const diff = targetDate - now;

    const daysEl = document.getElementById("cd-days");
    const hoursEl = document.getElementById("cd-hours");
    const minsEl = document.getElementById("cd-mins");
    const secsEl = document.getElementById("cd-secs");
    const statusTextEl = document.getElementById("cd-status-text");

    if (diff <= 0) {
      if (daysEl) daysEl.innerText = "00";
      if (hoursEl) hoursEl.innerText = "00";
      if (minsEl) minsEl.innerText = "00";
      if (secsEl) secsEl.innerText = "00";
      if (statusTextEl) {
        statusTextEl.innerText = "Stay Duration Completed / Overdue";
        statusTextEl.style.color = "#ef4444";
      }
      return;
    }

    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const mins = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    const secs = Math.floor((diff % (1000 * 60)) / 1000);

    if (daysEl) daysEl.innerText = String(days).padStart(2, "0");
    if (hoursEl) hoursEl.innerText = String(hours).padStart(2, "0");
    if (minsEl) minsEl.innerText = String(mins).padStart(2, "0");
    if (secsEl) secsEl.innerText = String(secs).padStart(2, "0");
  }

  updateTimer();
  QuestApp.stayCountdownInterval = setInterval(updateTimer, 1000);
}

// ==============================================================================
// 3. AUTHENTICATION MODAL & 3-STRIKE LOCKOUT
// ==============================================================================
function initAuthHandlers() {
  const modal = document.getElementById("auth-modal");
  const openBtns = document.querySelectorAll(".open-auth-btn");
  const closeBtns = document.querySelectorAll(".close-auth-btn");

  openBtns.forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      const tab = btn.dataset.tab || "login";
      openAuthModal(tab);
    });
  });

  closeBtns.forEach((btn) => {
    btn.addEventListener("click", closeAuthModal);
  });

  // Tab switching inside auth modal
  const tabBtns = document.querySelectorAll(".auth-tab-btn");
  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      tabBtns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const targetPane = btn.dataset.target;
      document.querySelectorAll(".auth-pane").forEach((p) => (p.style.display = "none"));
      const activePane = document.getElementById(targetPane);
      if (activePane) activePane.style.display = "block";
    });
  });

  // Login Form Submission
  const loginForm = document.getElementById("login-form");
  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const identifier = document.getElementById("login-identifier").value.trim();
      const password = document.getElementById("login-password").value;

      try {
        const res = await fetch("/api/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ identifier, password })
        });
        const data = await res.json();

        if (data.success) {
          showToast("Welcome to The Quest", data.message, "success");
          setTimeout(() => window.location.reload(), 1000);
        } else {
          if (data.is_locked) {
            startLockoutCountdown(data.lockout_seconds || 60);
          } else {
            showToast("Access Denied", data.message, "error");
          }
        }
      } catch (err) {
        showToast("Error", "Unable to connect to authentication service.", "error");
      }
    });
  }

  // Register Form Submission
  const registerForm = document.getElementById("register-form");
  if (registerForm) {
    registerForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const name = document.getElementById("reg-name").value.trim();
      const email = document.getElementById("reg-email").value.trim();
      const mobile = document.getElementById("reg-mobile").value.trim();
      const password = document.getElementById("reg-password").value;

      try {
        const res = await fetch("/api/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name, email, mobile_number: mobile, password })
        });
        const data = await res.json();

        if (data.success) {
          showToast("Registration Complete", data.message, "success");
          setTimeout(() => window.location.reload(), 1200);
        } else {
          showToast("Registration Failed", data.message, "error");
        }
      } catch (err) {
        showToast("Error", "Could not complete registration.", "error");
      }
    });
  }

  // Forgot Password Submission
  const forgotForm = document.getElementById("forgot-form");
  if (forgotForm) {
    forgotForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const identifier = document.getElementById("forgot-identifier").value.trim();
      const newPassword = document.getElementById("forgot-new-password").value;

      try {
        const res = await fetch("/api/forgot-password", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ identifier, new_password: newPassword })
        });
        const data = await res.json();
        if (data.success) {
          showToast("Password Reset", data.message, "success");
          openAuthModal("login");
        } else {
          showToast("Reset Failed", data.message, "error");
        }
      } catch (err) {
        showToast("Error", "Password reset failed.", "error");
      }
    });
  }

  // Social Login Buttons
  const socialBtns = document.querySelectorAll(".social-login-trigger");
  socialBtns.forEach((btn) => {
    btn.addEventListener("click", async () => {
      const provider = btn.dataset.provider;
      const demoEmail = prompt(`Enter ${provider} email to sign in:`, provider === "Google" ? "amelia.watson@gmail.com" : "diana.prince@outlook.com");
      if (!demoEmail) return;

      try {
        const res = await fetch("/api/social-login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ provider, email: demoEmail, name: demoEmail.split("@")[0].replace(".", " ").toUpperCase() })
        });
        const data = await res.json();
        if (data.success) {
          showToast(`Signed In via ${provider}`, data.message, "success");
          setTimeout(() => window.location.reload(), 1000);
        } else {
          showToast("Sign In Failed", data.message, "error");
        }
      } catch (err) {
        showToast("Error", "Social login failed.", "error");
      }
    });
  });
}

function openAuthModal(defaultTab = "login") {
  const modal = document.getElementById("auth-modal");
  if (!modal) return;
  modal.classList.add("open");

  const tabBtn = document.querySelector(`.auth-tab-btn[data-target="${defaultTab}-pane"]`);
  if (tabBtn) tabBtn.click();
}

function closeAuthModal() {
  const modal = document.getElementById("auth-modal");
  if (modal) modal.classList.remove("open");
}

function startLockoutCountdown(seconds) {
  QuestApp.lockoutSecondsLeft = seconds;
  const alertBox = document.getElementById("lockout-alert-box");
  const timerSpan = document.getElementById("lockout-timer-val");
  const submitBtn = document.getElementById("login-submit-btn");

  if (alertBox) alertBox.style.display = "flex";
  if (submitBtn) submitBtn.disabled = true;

  if (QuestApp.lockoutTimer) clearInterval(QuestApp.lockoutTimer);

  QuestApp.lockoutTimer = setInterval(() => {
    QuestApp.lockoutSecondsLeft--;
    if (timerSpan) timerSpan.innerText = `${QuestApp.lockoutSecondsLeft}s`;

    if (QuestApp.lockoutSecondsLeft <= 0) {
      clearInterval(QuestApp.lockoutTimer);
      if (alertBox) alertBox.style.display = "none";
      if (submitBtn) submitBtn.disabled = false;
      showToast("Unlocked", "You may now attempt to sign in again.", "info");
    }
  }, 1000);
}

// ==============================================================================
// 4. DINING CART & IN-STAY SERVICES
// ==============================================================================
function initDiningCart() {
  const addBtns = document.querySelectorAll(".add-to-cart-btn");
  const cartDrawer = document.getElementById("dining-cart-drawer");
  const openCartBtn = document.getElementById("open-cart-fab");
  const closeCartBtn = document.getElementById("close-cart-btn");
  const submitOrderBtn = document.getElementById("submit-food-order-btn");

  addBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.dataset.id;
      const name = btn.dataset.name;
      const price = parseFloat(btn.dataset.price);

      addToCart({ id, name, price, quantity: 1 });
      showToast("Added to Dining Cart", `${name} added to your in-room order.`, "success");
    });
  });

  if (openCartBtn) {
    openCartBtn.addEventListener("click", () => {
      renderCartItems();
      if (cartDrawer) cartDrawer.classList.add("open");
    });
  }

  if (closeCartBtn) {
    closeCartBtn.addEventListener("click", () => {
      if (cartDrawer) cartDrawer.classList.remove("open");
    });
  }

  if (submitOrderBtn) {
    submitOrderBtn.addEventListener("click", async () => {
      if (QuestApp.cart.length === 0) {
        showToast("Cart Empty", "Please select dishes from the culinary menu.", "error");
        return;
      }

      const deliveryTime = document.getElementById("cart-delivery-time").value;
      const notes = document.getElementById("cart-kitchen-notes").value;

      try {
        const res = await fetch("/api/services/order-food", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            items: QuestApp.cart,
            delivery_time: deliveryTime,
            notes: notes
          })
        });
        const data = await res.json();

        if (data.success) {
          showToast("Order Dispatched", data.message, "success");
          QuestApp.cart = [];
          updateCartCounter();
          if (cartDrawer) cartDrawer.classList.remove("open");
        } else {
          showToast("Order Failed", data.message, "error");
        }
      } catch (err) {
        showToast("Error", "Could not submit culinary order.", "error");
      }
    });
  }

  // Book Hotel Service (Spa, Laundry, Buffets)
  const bookServiceBtns = document.querySelectorAll(".book-service-trigger");
  bookServiceBtns.forEach((btn) => {
    btn.addEventListener("click", async () => {
      const serviceId = btn.dataset.serviceId;
      const serviceName = btn.dataset.serviceName;
      const scheduledTime = prompt(`Schedule ${serviceName} for what time?`, "Today at 3:00 PM");
      if (!scheduledTime) return;

      try {
        const res = await fetch("/api/services/book-service", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            service_id: serviceId,
            scheduled_time: scheduledTime,
            notes: "Guest booked via website portal"
          })
        });
        const data = await res.json();
        if (data.success) {
          showToast("Privilege Confirmed", data.message, "success");
        } else {
          showToast("Booking Notice", data.message, "error");
        }
      } catch (err) {
        showToast("Error", "Failed to book service.", "error");
      }
    });
  });

  // Dedicated Ridiculous Request Concierge Submission
  const submitRidiculousBtn = document.getElementById("submit-ridiculous-btn");
  if (submitRidiculousBtn) {
    submitRidiculousBtn.addEventListener("click", async () => {
      const textarea = document.getElementById("ridiculous-request-text");
      const text = textarea ? textarea.value.trim() : "";
      if (!text) {
        showToast("Request Details Needed", "Please tell our concierge your desire.", "error");
        return;
      }

      try {
        const res = await fetch("/api/services/ridiculous-request", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ request_text: text })
        });
        const data = await res.json();
        if (data.success) {
          showToast("Sacred Oath Honored", data.message, "success");
          if (textarea) textarea.value = "";
        } else {
          showToast("Notice", data.message, "error");
        }
      } catch (err) {
        showToast("Error", "Submission failed.", "error");
      }
    });
  }
}

function addToCart(item) {
  const existing = QuestApp.cart.find((it) => it.id === item.id);
  if (existing) {
    existing.quantity += 1;
  } else {
    QuestApp.cart.push(item);
  }
  updateCartCounter();
}

function updateCartCounter() {
  const counterEl = document.getElementById("cart-counter-badge");
  const totalItems = QuestApp.cart.reduce((sum, it) => sum + it.quantity, 0);
  if (counterEl) {
    counterEl.innerText = totalItems;
    counterEl.style.display = totalItems > 0 ? "flex" : "none";
  }
}

function renderCartItems() {
  const listEl = document.getElementById("cart-items-list");
  const subtotalEl = document.getElementById("cart-subtotal-val");
  if (!listEl) return;

  listEl.innerHTML = "";
  let subtotal = 0;

  if (QuestApp.cart.length === 0) {
    listEl.innerHTML = `<p style="text-align: center; color: rgba(255,255,255,0.5); padding: 2rem 0;">Your dining cart is empty.</p>`;
    if (subtotalEl) subtotalEl.innerText = "₱0.00";
    return;
  }

  QuestApp.cart.forEach((it, idx) => {
    const itemTotal = it.price * it.quantity;
    subtotal += itemTotal;

    const row = document.createElement("div");
    row.style.cssText = "display: flex; justify-content: space-between; align-items: center; padding: 0.8rem 0; border-bottom: 1px solid rgba(255,255,255,0.08);";
    row.innerHTML = `
      <div>
        <div style="font-weight: 600; color: #fff;">${it.name}</div>
        <div style="font-size: 0.8rem; color: #f59e0b;">₱${it.price.toLocaleString()} x ${it.quantity}</div>
      </div>
      <div style="display: flex; align-items: center; gap: 0.75rem;">
        <span style="font-weight: 700; color: #fef3c7;">₱${itemTotal.toLocaleString()}</span>
        <button onclick="removeFromCart(${idx})" style="background: transparent; border: none; color: #ef4444; cursor: pointer; font-size: 1rem;"><i class="fa-solid fa-trash"></i></button>
      </div>
    `;
    listEl.appendChild(row);
  });

  if (subtotalEl) subtotalEl.innerText = `₱${subtotal.toLocaleString()}`;
}

window.removeFromCart = function (index) {
  QuestApp.cart.splice(index, 1);
  updateCartCounter();
  renderCartItems();
};

// ==============================================================================
// 5. BOOKING & STAY EXTENSION HANDLERS
// ==============================================================================
function initBookingHandlers() {
  const bookBtns = document.querySelectorAll(".book-room-trigger");
  const bookingModal = document.getElementById("booking-modal");
  const closeBookingBtn = document.getElementById("close-booking-btn");
  const bookingForm = document.getElementById("booking-form");

  // Open booking modal
  bookBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const roomId = btn.dataset.roomId;
      const roomNumber = btn.dataset.roomNumber;
      const roomType = btn.dataset.roomType;
      const roomPrice = parseFloat(btn.dataset.roomPrice);
      const packs = btn.dataset.packs;

      document.getElementById("modal-room-id").value = roomId;
      document.getElementById("modal-room-name").innerText = `Suite ${roomNumber} • ${roomType}`;
      document.getElementById("modal-room-price").innerText = `₱${roomPrice.toLocaleString()} / night`;
      document.getElementById("modal-room-price").dataset.price = roomPrice;

      // Set default check-in tomorrow, check-out in 3 days
      const today = new Date();
      const tomorrow = new Date(today);
      tomorrow.setDate(tomorrow.getDate() + 1);
      const checkout = new Date(tomorrow);
      checkout.setDate(checkout.getDate() + 2);

      const inInput = document.getElementById("modal-check-in");
      const outInput = document.getElementById("modal-check-out");

      if (inInput) inInput.value = tomorrow.toISOString().split("T")[0];
      if (outInput) outInput.value = checkout.toISOString().split("T")[0];

      calculateBookingTotal();
      if (bookingModal) bookingModal.classList.add("open");
    });
  });

  if (closeBookingBtn) {
    closeBookingBtn.addEventListener("click", () => {
      if (bookingModal) bookingModal.classList.remove("open");
    });
  }

  // Recalculate price on date changes
  const inDateEl = document.getElementById("modal-check-in");
  const outDateEl = document.getElementById("modal-check-out");
  if (inDateEl) inDateEl.addEventListener("change", calculateBookingTotal);
  if (outDateEl) outDateEl.addEventListener("change", calculateBookingTotal);

  // Submit Reservation
  if (bookingForm) {
    bookingForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const roomId = document.getElementById("modal-room-id").value;
      const checkIn = document.getElementById("modal-check-in").value;
      const checkOut = document.getElementById("modal-check-out").value;
      const specialReq = document.getElementById("modal-special-requests").value;
      const numGuests = document.getElementById("modal-guests").value;

      try {
        const res = await fetch("/api/reservations/book", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            room_id: roomId,
            check_in_date: checkIn,
            check_out_date: checkOut,
            special_requests: specialReq,
            num_guests: numGuests
          })
        });
        const data = await res.json();

        if (data.success) {
          showToast("Reservation Confirmed", data.message, "success");
          if (bookingModal) bookingModal.classList.remove("open");
          setTimeout(() => (window.location.href = "/profile"), 1500);
        } else {
          if (data.requires_login) {
            showToast("Login Required", data.message, "info");
            if (bookingModal) bookingModal.classList.remove("open");
            openAuthModal("login");
          } else {
            showToast("Booking Notice", data.message, "error");
          }
        }
      } catch (err) {
        showToast("Error", "Could not complete booking.", "error");
      }
    });
  }

  // Extend Stay Modal Trigger
  const extendStayBtns = document.querySelectorAll(".extend-stay-trigger");
  const extendModal = document.getElementById("extend-stay-modal");
  const closeExtendBtn = document.getElementById("close-extend-btn");
  const extendForm = document.getElementById("extend-stay-form");

  extendStayBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      if (extendModal) extendModal.classList.add("open");
    });
  });

  if (closeExtendBtn) {
    closeExtendBtn.addEventListener("click", () => {
      if (extendModal) extendModal.classList.remove("open");
    });
  }

  if (extendForm) {
    extendForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const days = document.getElementById("extend-days-select").value;
      const paymentMethod = document.getElementById("extend-payment-method").value;

      try {
        const res = await fetch("/api/reservations/extend", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            additional_days: parseInt(days),
            payment_method: paymentMethod
          })
        });
        const data = await res.json();

        if (data.success) {
          showToast("Stay Extended", data.message, "success");
          if (extendModal) extendModal.classList.remove("open");
          setTimeout(() => window.location.reload(), 1500);
        } else {
          showToast("Extension Notice", data.message, "error");
        }
      } catch (err) {
        showToast("Error", "Could not extend stay.", "error");
      }
    });
  }
}

function calculateBookingTotal() {
  const inVal = document.getElementById("modal-check-in").value;
  const outVal = document.getElementById("modal-check-out").value;
  const priceEl = document.getElementById("modal-room-price");
  const totalNightsEl = document.getElementById("calc-nights-count");
  const totalCostEl = document.getElementById("calc-total-cost");

  if (!inVal || !outVal || !priceEl) return;

  const dIn = new Date(inVal);
  const dOut = new Date(outVal);
  const diffTime = dOut - dIn;
  const nights = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

  if (nights > 0) {
    const unitPrice = parseFloat(priceEl.dataset.price || 0);
    const total = nights * unitPrice;
    if (totalNightsEl) totalNightsEl.innerText = `${nights} night(s)`;
    if (totalCostEl) totalCostEl.innerText = `₱${total.toLocaleString()}`;
  } else {
    if (totalNightsEl) totalNightsEl.innerText = "0 nights";
    if (totalCostEl) totalCostEl.innerText = "₱0.00";
  }
}

// ==============================================================================
// 6. FRONT DESK CONCIERGE CHAT & CALLBACK
// ==============================================================================
function initChatHandlers() {
  const chatForm = document.getElementById("concierge-chat-form");
  const callbackBtn = document.getElementById("request-callback-btn");

  if (chatForm) {
    chatForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const input = document.getElementById("chat-message-input");
      const msg = input.value.trim();
      const dept = document.getElementById("chat-dept-select").value;
      if (!msg) return;

      appendChatMessage(msg, "customer");
      input.value = "";

      try {
        const res = await fetch("/api/ask/send", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ department: dept, message: msg })
        });
        const data = await res.json();
        if (data.success && data.reply) {
          setTimeout(() => {
            appendChatMessage(data.reply, "staff");
          }, 600);
        }
      } catch (err) {
        appendChatMessage("Message delivery error. Please dial 0 from your suite phone.", "staff");
      }
    });
  }

  if (callbackBtn) {
    callbackBtn.addEventListener("click", async () => {
      const phone = prompt("Enter the phone number or room extension you wish to be called on:", "Suite Room Phone");
      if (!phone) return;

      try {
        const res = await fetch("/api/ask/callback", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ phone: phone, notes: "Requested immediate desk callback" })
        });
        const data = await res.json();
        showToast("Callback Dispatched", data.message, "success");
      } catch (err) {
        showToast("Error", "Callback request failed.", "error");
      }
    });
  }
}

function appendChatMessage(text, sender) {
  const container = document.getElementById("chat-messages-box");
  if (!container) return;

  const bubble = document.createElement("div");
  bubble.className = `chat-bubble ${sender}`;
  bubble.innerHTML = `<div>${text}</div><div style="font-size: 0.65rem; opacity: 0.6; margin-top: 0.3rem;">Just now</div>`;

  container.appendChild(bubble);
  container.scrollTop = container.scrollHeight;
}

// ==============================================================================
// 7. LOYALTY REWARDS REDEMPTION
// ==============================================================================
window.redeemReward = async function (rewardId, rewardName, pointsRequired) {
  const confirmRedeem = confirm(`Redeem '${rewardName}' for ${pointsRequired} loyalty points?`);
  if (!confirmRedeem) return;

  try {
    const res = await fetch("/api/rewards/redeem", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reward_id: rewardId })
    });
    const data = await res.json();

    if (data.success) {
      alert(`Voucher Redeemed!\n\nVoucher Code: ${data.voucher_code}\n\nPresent this code to the front desk or during room dining service.`);
      window.location.reload();
    } else {
      showToast("Redemption Notice", data.message, "error");
    }
  } catch (err) {
    showToast("Error", "Could not redeem voucher.", "error");
  }
};

// ==============================================================================
// 8. TOAST NOTIFICATION SYSTEM
// ==============================================================================
function showToast(title, message, type = "info") {
  let container = document.querySelector(".toast-container");
  if (!container) {
    container = document.createElement("div");
    container.className = "toast-container";
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  toast.className = `quest-toast ${type}`;

  const icon = type === "success" ? "fa-circle-check" : type === "error" ? "fa-circle-exclamation" : "fa-bell";
  toast.innerHTML = `
    <div class="toast-icon"><i class="fa-solid ${icon}"></i></div>
    <div class="toast-content">
      <div class="toast-title">${title}</div>
      <div class="toast-msg">${message}</div>
    </div>
  `;

  container.appendChild(toast);

  // Play subtle chime sound
  playNotificationChime();

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(-30px)";
    toast.style.transition = "all 0.4s ease";
    setTimeout(() => toast.remove(), 400);
  }, 4500);
}

function playNotificationChime() {
  try {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(587.33, audioCtx.currentTime); // D5
    osc.frequency.exponentialRampToValueAtTime(880, audioCtx.currentTime + 0.15); // A5
    gain.gain.setValueAtTime(0.05, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + 0.3);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + 0.3);
  } catch (e) {
    // Ignore audio autoplay restrictions
  }
}

// ==============================================================================
// 9. NAVBAR SCROLL & HELPER UTILITIES
// ==============================================================================
function initNavbarScroll() {
  const navbar = document.querySelector(".quest-navbar");
  if (!navbar) return;
  window.addEventListener("scroll", () => {
    if (window.scrollY > 40) {
      navbar.classList.add("scrolled");
    } else {
      navbar.classList.remove("scrolled");
    }
  });
}

function checkUrlParams() {
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get("open_login") === "true") {
    openAuthModal("login");
  }
}
