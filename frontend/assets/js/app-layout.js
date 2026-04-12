let lastNotifId = null;
const NOTIF_SEEN_KEY = "cvevo_notif_seen_ids";

function playNotificationSound() {
  try {
    const context = new (window.AudioContext || window.webkitAudioContext)();
    const osc = context.createOscillator();
    const gain = context.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(880, context.currentTime);
    osc.frequency.exponentialRampToValueAtTime(440, context.currentTime + 0.5);
    gain.gain.setValueAtTime(0.05, context.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, context.currentTime + 0.5);
    osc.connect(gain);
    gain.connect(context.destination);
    osc.start();
    osc.stop(context.currentTime + 0.5);
  } catch (e) { }
}

function showToast(message, type = "info", silent = false) {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const items = container.querySelectorAll(".toast-item");
  if (items.length >= 5) {
    const oldest = items[0];
    oldest.style.animation = "toastSlideOut 0.3s ease forwards";
    setTimeout(() => oldest.remove(), 300);
  }

  const toast = document.createElement("div");
  toast.className = "toast-item";
  
  const icons = {
    success: '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>',
    info: '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>',
    warning: '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>',
    error: '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>'
  };

  const themes = {
    success: { bg: "linear-gradient(135deg, #10b981, #059669)" },
    info: { bg: "linear-gradient(135deg, #3b82f6, #2563eb)" },
    warning: { bg: "linear-gradient(135deg, #f59e0b, #d97706)" },
    error: { bg: "linear-gradient(135deg, #ef4444, #dc2626)" }
  };

  const theme = themes[type] || themes.info;

  toast.innerHTML = `
    <div style="
      display: flex; align-items: center; gap: 14px; 
      padding: 16px 24px; 
      background: ${theme.bg}; 
      color: white; 
      border-radius: 16px; 
      box-shadow: 0 20px 25px -5px rgba(0,0,0,0.2);
      backdrop-filter: blur(10px);
      margin-bottom: 12px;
      pointer-events: auto;
      min-width: 350px;
      animation: toastSlideIn 0.5s cubic-bezier(0.19, 1, 0.22, 1) forwards;
    ">
      <div style="flex-shrink: 0; background: rgba(255,255,255,0.2); border-radius: 12px; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;">
        ${icons[type] || icons.info}
      </div>
      <div style="flex: 1; font-size: 14px; font-weight: 700; line-height: 1.4;">${message}</div>
    </div>
  `;

  container.appendChild(toast);
  if (!silent) playNotificationSound();

  setTimeout(() => {
    if (toast.parentNode) {
      toast.style.animation = "toastSlideOut 0.4s ease forwards";
      setTimeout(() => toast.remove(), 400);
    }
  }, 6000);
}

async function loadNotifications(isInitial = false) {
  const body = document.getElementById("notificationsBody");
  const dot = document.getElementById("bell-dot");

  try {
    const res = await fetch("/api/notifications/", { credentials: "include" });
    if (!res.ok) return;

    const data = await res.json();
    const notifications = data.notifications || [];
    const count = data.unread_count || 0;

    if (dot) dot.style.display = count > 0 ? "block" : "none";

    // Seen Tracker Logic
    let seenIds = [];
    try { seenIds = JSON.parse(localStorage.getItem(NOTIF_SEEN_KEY) || "[]"); } catch(e){}
    
    let fired = false;
    notifications.forEach(n => {
      if (!n.is_read && !seenIds.includes(n.id)) {
        showToast(n.message, n.type || "info");
        seenIds.push(n.id);
        fired = true;
      }
    });

    if (fired) {
      // Keep only latest 20 seen IDs to save space
      localStorage.setItem(NOTIF_SEEN_KEY, JSON.stringify(seenIds.slice(-20)));
    }

    if (!body) return;
    if (notifications.length === 0) {
      body.innerHTML = `<div style="padding:40px; text-align:center; color:#94a3b8; font-size:13px; font-weight:600;">No messages yet</div>`;
      return;
    }

    body.innerHTML = notifications.map(n => `
      <div class="nd-item ${n.type || ""} ${n.is_read ? "" : "unread"}" style="padding:16px; border-bottom:1px solid #f1f5f9; display:flex; gap:12px;">
        <div style="font-size:18px;">${n.icon || "🔔"}</div>
        <div style="flex:1;">
          <div style="font-size:13px; font-weight:700; color:#1e293b;">${n.message}</div>
          <div style="font-size:11px; color:#94a3b8; margin-top:4px;">${n.created_at || "Just now"}</div>
        </div>
      </div>
    `).join("");
  } catch (err) { }
}

function startNotificationPolling() {
  setInterval(() => loadNotifications(false), 15000);
}

// --- Rest of the layout logic ---

async function loadPartial(selector, path) {
  const mount = document.querySelector(selector);
  if (!mount) return;
  try {
    const res = await fetch(path);
    const html = await res.text();
    mount.innerHTML = html;
    const scripts = mount.querySelectorAll("script");
    scripts.forEach(oldScript => {
      const newScript = document.createElement("script");
      Array.from(oldScript.attributes).forEach(attr => newScript.setAttribute(attr.name, attr.value));
      newScript.appendChild(document.createTextNode(oldScript.innerHTML));
      oldScript.parentNode.replaceChild(newScript, oldScript);
    });
  } catch (err) { console.error("Partial failed:", path); }
}

function setActiveSidebar(pageKey) {
  document.querySelectorAll(".nav-item[data-page]").forEach((item) => {
    item.classList.toggle("active", item.dataset.page === pageKey);
  });
}

function setActiveStepper(stepKey) {
  document.querySelectorAll(".stepper-item[data-step]").forEach((item) => {
    item.classList.toggle("active", item.dataset.step === stepKey);
  });
}

function setTopbar(title, subtitle) {
  const t = document.getElementById("topbarTitle");
  const s = document.getElementById("topbarSubtitle");
  if (t) t.textContent = title || "Dashboard";
  if (s) s.textContent = subtitle || "";
}

function getCurrentUser() {
  try { return JSON.parse(localStorage.getItem("currentUser") || "null"); }
  catch (err) { return null; }
}

function setUserUI() {
  const user = getCurrentUser();
  if (!user) return;
  const avatar = document.getElementById("topbarAvatar");
  const name = document.getElementById("topbarUserName");
  let label = user.full_name || user.email || "User";
  if (user.role === "hr" && user.company) label = user.company;
  if (name) name.textContent = label.slice(0, 15);
  if (avatar) avatar.textContent = label.slice(0, 1).toUpperCase();
}

function configureSidebarByRole() {
  const user = getCurrentUser();
  if (!user) return;
  const ids = ["jobseekerSections", "hrSections", "adminSections"];
  ids.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.style.display = "none";
  });

  const brandLink = document.getElementById("sidebarBrandLink");
  const profileLink = document.getElementById("sidebarProfileLink");
  const helpLink = document.getElementById("sidebarHelpLink");

  if (user.role === "jobseeker") {
    document.getElementById("jobseekerSections").style.display = "block";
    if (brandLink) brandLink.href = "../jobseeker/jobseeker_dashboard.html";
    if (profileLink) profileLink.href = "../jobseeker/profile_settings.html";
  } else if (user.role === "hr") {
    document.getElementById("hrSections").style.display = "block";
    if (brandLink) brandLink.href = "../hr/hr_dashboard.html";
    if (profileLink) profileLink.href = "../hr/hr_profile_settings.html";
  }
  if (helpLink) {
    helpLink.style.display = "flex";
    helpLink.href = "../shared/help_support.html";
  }
}

async function protectPage() {
  let user = getCurrentUser();
  if (!user) {
    try {
      const res = await fetch("/api/users/me/", { credentials: "include" });
      if (res.ok) {
        user = await res.json();
        localStorage.setItem("currentUser", JSON.stringify(user));
        return true;
      }
    } catch (err) { }
    window.location.href = "../public/login.html";
    return false;
  }
  return true;
}

function appConfirm(arg1, arg2, iconType = "warning", confirmText = "Confirm", cancelText = "Cancel") {
  console.log("DEBUG: appConfirm called with:", { arg1, arg2 });
  let title, message;

  if (typeof arg1 === "object" && arg1 !== null && !Array.isArray(arg1)) {
    title = arg1.title;
    message = arg1.message;
    iconType = arg1.iconType || "warning";
    confirmText = arg1.confirmText || "Confirm";
    cancelText = arg1.cancelText || "Cancel";
  } else {
    title = arg1;
    message = arg2;
  }

  const modal = document.getElementById("appConfirmModal");
  if (!modal) {
    console.warn("DEBUG: appConfirmModal not found! Falling back to browser confirm.");
    return Promise.resolve(window.confirm(message || "Are you sure?"));
  }

  const h3 = modal.querySelector(".confirm-h3");
  const p = modal.querySelector(".confirm-p");
  const ico = modal.querySelector(".confirm-ico");
  const btnConfirm = modal.querySelector(".c-btn-confirm");
  const btnCancel = modal.querySelector(".c-btn-cancel");

  if (h3) h3.textContent = title || "Are you sure?";
  if (p) p.textContent = message || "This action cannot be undone.";
  if (btnConfirm) btnConfirm.textContent = confirmText;
  if (btnCancel) btnCancel.textContent = cancelText;

  // Set Icon
  if (ico) {
    if (iconType === "warning" || iconType === "danger") {
      ico.style.background = "#fee2e2";
      ico.style.color = "#ef4444";
      ico.innerHTML = `
        <svg viewBox="0 0 24 24" width="42" height="42" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="3 6 5 6 21 6"></polyline>
          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
          <line x1="10" y1="11" x2="10" y2="17"></line>
          <line x1="14" y1="11" x2="14" y2="17"></line>
        </svg>`;
    } else {
      ico.style.background = "#eff6ff";
      ico.style.color = "#3b82f6";
      ico.innerHTML = `
        <svg viewBox="0 0 24 24" width="42" height="42" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="12" y1="16" x2="12" y2="12"></line>
          <line x1="12" y1="8" x2="12.01" y2="8"></line>
        </svg>`;
    }
  }

  modal.style.display = "flex";
  setTimeout(() => modal.classList.add("is-active"), 5);
  document.body.style.overflow = "hidden";

  return new Promise((resolve) => {
    const closeModal = (val) => {
      modal.classList.remove("is-active");
      document.body.style.overflow = "";
      setTimeout(() => {
        modal.style.display = "none";
        resolve(val);
      }, 300);
    };

    if (btnConfirm) {
      btnConfirm.onclick = () => closeModal(true);
    } else {
      console.warn("DEBUG: .c-btn-confirm NOT FOUND IN MODAL!");
      closeModal(true);
    }

    if (btnCancel) {
      btnCancel.onclick = () => closeModal(false);
    }

    modal.onclick = (e) => {
      if (e.target === modal) closeModal(false);
    }
  });
}

async function initAppLayout({ pageKey, stepKey, title, subtitle }) {
  if (!(await protectPage())) return;

  await loadPartial("#sidebarMount", "../../partials/sidebar.html");
  await loadPartial("#topbarMount", "../../partials/topbar.html");

  configureSidebarByRole();
  setActiveSidebar(pageKey);
  setTopbar(title, subtitle);
  setUserUI();

  // Notification Setup
  const bellBtn = document.getElementById("bell-btn");
  const dropdown = document.getElementById("notifications-dropdown");
  if (bellBtn && dropdown) {
    bellBtn.onclick = (e) => {
      e.stopPropagation();
      dropdown.style.display = dropdown.style.display === "block" ? "none" : "block";
    };
    
    // SECRET TEST: Right-click the bell for a success toast!
    bellBtn.oncontextmenu = (e) => {
      e.preventDefault();
      showToast("Real-time notifications are UP! 🚀🔊", "success");
    };

    window.onclick = () => dropdown.style.display = "none";
    dropdown.onclick = (e) => e.stopPropagation();
  }

  const markAllBtn = document.getElementById("markAllReadBtn");
  if (markAllBtn) {
    markAllBtn.onclick = async () => {
      await fetch("/api/notifications/read/", { method: "POST", credentials: "include" });
      loadNotifications(false);
    };
  }

  loadNotifications(true);
  startNotificationPolling();

  const logoutBtn = document.getElementById("logoutBtn");
  if (logoutBtn) {
    logoutBtn.onclick = async () => {
      // Restore Premium Modal for Logout
      const ok = await appConfirm({
        title: "Sign Out?",
        message: "Are you sure you want to end your session?",
        confirmText: "Logout",
        iconType: "info"
      });
      if (!ok) return;

      await fetch("/api/auth/logout/", { method: "POST" });
      localStorage.removeItem("currentUser");
      window.location.href = "../public/login.html";
    };
  }

  // Confirm Modal Mount
  if (!document.getElementById("appConfirmModal")) {
    const div = document.createElement("div");
    div.id = "confirmModalMount";
    document.body.appendChild(div);
    await loadPartial("#confirmModalMount", "../../partials/confirm_modal.html");
  }

  // Toast Container
  if (!document.getElementById("toast-container")) {
    const container = document.createElement("div");
    container.id = "toast-container";
    container.style.cssText = "position: fixed; top: 24px; right: 24px; z-index: 9999; display: flex; flex-direction: column; gap: 12px; pointer-events: none;";
    document.body.appendChild(container);
  }
}

window.initAppLayout = initAppLayout;
window.showToast = showToast;
window.appConfirm = appConfirm;
window.loadPartial = loadPartial;
window.playNotificationSound = playNotificationSound;
window.loadNotifications = loadNotifications;
window.startNotificationPolling = startNotificationPolling;

console.log("✅ CVevo app-layout.js logic initialized and exported.");
