async function loadPartial(selector, path) {
  const mount = document.querySelector(selector);
  if (!mount) {
    console.warn(`[CVevo] Mount point not found: ${selector}`);
    return;
  }

  console.log(`[CVevo] Loading partial: ${path} into ${selector}...`);
  try {
    const res = await fetch(path);
    if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
    }
    const html = await res.text();
    mount.innerHTML = html;
    console.log(`[CVevo] Partial loaded successfully: ${path}`);
  } catch (err) {
    console.error(`[CVevo] Failed to load partial: ${path}`, err);
    mount.innerHTML = `<div style="padding: 20px; color: red;">Error loading ${path}: ${err.message}</div>`;
  }
}

function setActiveSidebar(pageKey) {
  document.querySelectorAll(".nav-item[data-page]").forEach((item) => {
    if (item.dataset.page === pageKey) {
      item.classList.add("active");
    } else {
      item.classList.remove("active");
    }
  });
}

function setActiveStepper(stepKey) {
  document.querySelectorAll(".stepper-item[data-step]").forEach((item) => {
    if (item.dataset.step === stepKey) {
      item.classList.add("active");
    } else {
      item.classList.remove("active");
    }
  });
}

function setTopbar(title, subtitle) {
  const t = document.getElementById("topbarTitle");
  const s = document.getElementById("topbarSubtitle");

  if (t) t.textContent = title || "Dashboard";
  if (s) s.textContent = subtitle || "";
}

function getCurrentUser() {
  try {
    return JSON.parse(localStorage.getItem("currentUser") || "null");
  } catch (err) {
    return null;
  }
}

function setUserUI() {
  const user = getCurrentUser();
  const avatar = document.getElementById("topbarAvatar");
  const name = document.getElementById("topbarUserName");

  if (!user) return;

  let label = user.full_name || user.email || "User";

  if (user.role === "hr" && user.company) {
    label = user.company;
  }

  if (name) name.textContent = label.slice(0, 15);
  if (avatar) avatar.textContent = label.slice(0, 1).toUpperCase();
}

function hideAllRoleMenus() {
  const ids = ["jobseekerSections", "hrSections", "adminSections", "helpSection"];
  ids.forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.style.display = "none";
  });
}

function configureSidebarByRole() {
  const user = getCurrentUser();
  if (!user) return;

  hideAllRoleMenus();

  const brandLink = document.getElementById("sidebarBrandLink");
  const profileLink = document.getElementById("sidebarProfileLink");
  const helpLink = document.getElementById("sidebarHelpLink");

  if (user.role === "jobseeker") {
    const section = document.getElementById("jobseekerSections");
    const helpSec = document.getElementById("helpSection");
    if (section) section.style.display = "block";
    if (helpSec) helpSec.style.display = "block";
    if (brandLink) brandLink.href = "../jobseeker/jobseeker_dashboard.html";
    if (profileLink) profileLink.href = "../jobseeker/profile_settings.html";
    if (helpLink) helpLink.href = "../jobseeker/help_support.html";
  } 
  else if (user.role === "hr") {
    const section = document.getElementById("hrSections");
    const helpSec = document.getElementById("helpSection");
    if (section) section.style.display = "block";
    if (helpSec) helpSec.style.display = "block";
    if (brandLink) brandLink.href = "../hr/hr_dashboard.html";
    if (profileLink) profileLink.href = "../hr/hr_profile_settings.html";
    if (helpLink) helpLink.href = "../hr/hr_help_support.html";
  } 
  else if (user.role === "admin" || user.is_staff) {
    const section = document.getElementById("adminSections");
    if (section) section.style.display = "block";
    if (brandLink) brandLink.href = "../admin/super_admin_dashboard.html";
    if (profileLink) profileLink.href = "../admin/profile_settings.html";
  }
}

function highlightActiveSidebarLink(pageKey) {
  if (!pageKey) return;
  const links = document.querySelectorAll(".sidebar .nav-item");
  links.forEach(link => {
    if (link.getAttribute("data-page") === pageKey) {
      link.classList.add("active");
    } else {
      link.classList.remove("active");
    }
  });
}

async function loadNotifications() {
  const body = document.getElementById("notificationsBody");
  const dot = document.getElementById("bell-dot");

  if (!body) return;

  try {
    const res = await fetch("/api/notifications/", {
      credentials: "include"
    });

    if (!res.ok) {
      throw new Error("Failed to fetch notifications");
    }

    const data = await res.json();
    const notifications = data.notifications || [];
    const unreadCount = data.unread_count || 0;

    if (dot) {
      dot.style.display = unreadCount > 0 ? "block" : "none";
    }

    if (!notifications.length) {
      body.innerHTML = `
        <div class="nd-empty">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:32px; height:32px; color:#cbd5e1; margin-bottom:0.5rem;">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 0 1-3.46 0"/>
          </svg>
          <p>No new notifications</p>
        </div>
      `;
      return;
    }

    body.innerHTML = notifications.map((notif) => `
      <div class="nd-item ${notif.type || ""} ${notif.is_read ? "" : "unread"}">
        <div class="nd-content">
          <p>${notif.message || ""}</p>
          <span class="nd-time">${notif.time_ago || ""}</span>
        </div>
      </div>
    `).join("");
  } catch (err) {
    console.error("Failed to load notifications", err);
  }
}

function setupNotificationsUI() {
  const bellBtn = document.getElementById("bell-btn");
  const dropdown = document.getElementById("notifications-dropdown");
  const markAllBtn = document.getElementById("markAllReadBtn");

  if (bellBtn && dropdown) {
    bellBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      dropdown.style.display = dropdown.style.display === "block" ? "none" : "block";
    });

    document.addEventListener("click", (e) => {
      if (!dropdown.contains(e.target) && !bellBtn.contains(e.target)) {
        dropdown.style.display = "none";
      }
    });
  }

  if (markAllBtn) {
    markAllBtn.addEventListener("click", async (e) => {
      e.preventDefault();

      try {
        await fetch("/api/notifications/read/", {
          method: "POST",
          credentials: "include"
        });
        loadNotifications();
      } catch (err) {
        console.error("Failed to mark notifications as read", err);
      }
    });
  }
}

function setupLogout() {
  const logoutBtn = document.getElementById("logoutBtn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async (e) => {
      e.preventDefault();
      try {
        await fetch("/api/auth/logout/", { method: "POST", credentials: "include" });
      } catch (err) {
        console.error("Server logout failed", err);
      }
      localStorage.removeItem("currentUser");
      window.location.href = "../public/login.html";
    });
  }
}

async function protectPage() {
  console.log("[CVevo] Checking authentication status...");
  let user = getCurrentUser();
  
  if (!user) {
    console.log("[CVevo] No user in localStorage, attempting to sync with session...");
    try {
      const res = await fetch("/api/users/me/", { credentials: "include" });
      if (res.ok) {
        user = await res.json();
        console.log("[CVevo] Session sync successful:", user.email);
        localStorage.setItem("currentUser", JSON.stringify(user));
        return true;
      } else {
        console.warn("[CVevo] Session sync failed, status:", res.status);
      }
    } catch (err) {
      console.error("[CVevo] Session sync API error:", err);
    }
    
    console.log("[CVevo] Redirecting to login...");
    window.location.href = "../public/login.html";
    return false;
  }
  console.log("[CVevo] Authenticated as:", user.email);
  return true;
}

async function initAppLayout({ pageKey, stepKey, title, subtitle }) {
  const isProtected = await protectPage();
  if (!isProtected) return;

  await loadPartial("#sidebarMount", "../../partials/sidebar.html");
  await loadPartial("#topbarMount", "../../partials/topbar.html");

  configureSidebarByRole();
  setActiveSidebar(pageKey);
  setTopbar(title, subtitle);
  setUserUI();
  setupLogout();
  setupNotificationsUI();
  loadNotifications();

  const stepperMount = document.getElementById("jobseekerStepperMount");
  const user = getCurrentUser();

  if (stepperMount && user && user.role === "jobseeker") {
    await loadPartial("#jobseekerStepperMount", "../../partials/jobseeker_stepper.html");
    setActiveStepper(stepKey);
  }

  highlightActiveSidebarLink(pageKey);

  // Inject confirm modal mount if not exists
  if (!document.getElementById("appConfirmModal")) {
    const div = document.createElement("div");
    div.id = "confirmModalMount";
    document.body.appendChild(div);
    await loadPartial("#confirmModalMount", "../../partials/confirm_modal.html");
  }
}

window.initAppLayout = initAppLayout;
