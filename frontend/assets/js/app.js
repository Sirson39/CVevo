(() => {
  console.log("✅ CVevo app.js loaded");

  document.documentElement.classList.add("js");

  function setupBurgerMenu() {
    const burger = document.getElementById("burgerBtn");
    const links = document.getElementById("navLinks");

    if (!burger || !links) return;

    burger.addEventListener("click", () => {
      const open = links.classList.toggle("open");
      burger.setAttribute("aria-expanded", String(open));
    });

    links.querySelectorAll("a").forEach((a) => {
      a.addEventListener("click", () => {
        links.classList.remove("open");
        burger.setAttribute("aria-expanded", "false");
      });
    });
  }

  function setupHeaderScroll() {
    const header = document.querySelector(".site-header");
    if (!header) return;

    const onScroll = () => {
      header.classList.toggle("scrolled", window.scrollY > 10);
    };

    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  function setupResourcesDropdown() {
    const dd = document.getElementById("resourcesDd");
    const ddBtn = dd ? dd.querySelector(".dd-btn") : null;
    const ddMenu = document.getElementById("resourcesMenu");

    if (!dd || !ddBtn) return;

    const closeDropdown = () => {
      dd.classList.remove("open");
      ddBtn.setAttribute("aria-expanded", "false");
    };

    ddBtn.addEventListener("click", (e) => {
      e.preventDefault();
      const isOpen = dd.classList.toggle("open");
      ddBtn.setAttribute("aria-expanded", String(isOpen));
    });

    document.addEventListener("click", (e) => {
      if (!dd.contains(e.target)) closeDropdown();
    });

    ddMenu?.querySelectorAll("a").forEach((a) => {
      a.addEventListener("click", () => closeDropdown());
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closeDropdown();
    });
  }

  function setupTemplateCarousel() {
    const strip = document.getElementById("templateStrip");
    const prevBtn = document.querySelector(".t-prev");
    const nextBtn = document.querySelector(".t-next");
    const dotsWrap = document.getElementById("templateDots");
    const shell = document.getElementById("templateShell");

    if (!strip || !dotsWrap) return;

    let autoTimer = null;

    const getStepWidth = () => {
      const card = strip.querySelector(".template-card");
      if (!card) return 360;

      const cardWidth = card.getBoundingClientRect().width;
      const styles = window.getComputedStyle(strip);
      const gap = parseFloat(styles.columnGap || styles.gap || 18);
      return cardWidth + gap;
    };

    const scrollByCard = (dir) => {
      strip.scrollBy({
        left: dir * getStepWidth(),
        behavior: "smooth"
      });
    };

    const buildDots = () => {
      const cards = [...strip.querySelectorAll(".template-card")];
      dotsWrap.innerHTML = "";

      cards.forEach((_, i) => {
        const b = document.createElement("button");
        b.type = "button";
        b.className = "dot";
        b.setAttribute("aria-label", `Go to template ${i + 1}`);

        b.addEventListener("click", () => {
          const card = strip.querySelectorAll(".template-card")[i];
          card?.scrollIntoView({
            behavior: "smooth",
            inline: "center",
            block: "nearest"
          });
        });

        dotsWrap.appendChild(b);
      });
    };

    const updateActiveDot = () => {
      const cards = [...strip.querySelectorAll(".template-card")];
      const dots = [...dotsWrap.querySelectorAll(".dot")];

      if (!cards.length || !dots.length) return;

      const stripRect = strip.getBoundingClientRect();
      const centerX = stripRect.left + stripRect.width / 2;

      let bestIdx = 0;
      let bestDist = Infinity;

      cards.forEach((c, i) => {
        const r = c.getBoundingClientRect();
        const cCenter = r.left + r.width / 2;
        const dist = Math.abs(centerX - cCenter);

        if (dist < bestDist) {
          bestDist = dist;
          bestIdx = i;
        }
      });

      dots.forEach((d, i) => {
        d.classList.toggle("active", i === bestIdx);
      });
    };

    const stopAuto = () => {
      if (autoTimer) clearInterval(autoTimer);
      autoTimer = null;
    };

    const startAuto = () => {
      stopAuto();

      autoTimer = setInterval(() => {
        const nearEnd = strip.scrollLeft + strip.clientWidth >= strip.scrollWidth - 10;

        if (nearEnd) {
          strip.scrollTo({ left: 0, behavior: "smooth" });
        } else {
          scrollByCard(1);
        }
      }, 3500);
    };

    prevBtn?.addEventListener("click", () => scrollByCard(-1));
    nextBtn?.addEventListener("click", () => scrollByCard(1));

    buildDots();
    updateActiveDot();

    strip.addEventListener("scroll", () => {
      window.requestAnimationFrame(updateActiveDot);
    });

    window.addEventListener("resize", updateActiveDot);

    shell?.addEventListener("mouseenter", stopAuto);
    shell?.addEventListener("mouseleave", startAuto);
    shell?.addEventListener("focusin", stopAuto);
    shell?.addEventListener("focusout", startAuto);

    startAuto();
  }

  function setupRevealAnimations() {
    const els = Array.from(document.querySelectorAll(".reveal"));
    if (!els.length) return;

    const revealNow = () => {
      els.forEach((el) => el.classList.add("in"));
    };

    if (!("IntersectionObserver" in window)) {
      revealNow();
      return;
    }

    const io = new IntersectionObserver(
      (entries, obs) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("in");
            obs.unobserve(entry.target);
          }
        });
      },
      {
        threshold: 0.08,
        rootMargin: "0px 0px -5% 0px"
      }
    );

    els.forEach((el) => io.observe(el));
  }

  function setupConfirmModal() {
    window.appConfirm = (title, message, callback, isDestructive = true, confirmText = "Yes, Delete") => {
      const modal = document.getElementById("appConfirmModal");

      if (!modal) {
        const ok = window.confirm(message || "Are you sure?");
        if (callback) callback(ok);
        return;
      }

      const h3 = modal.querySelector(".confirm-h3");
      const p = modal.querySelector(".confirm-p");
      const confirmBtn = modal.querySelector(".c-btn-confirm");
      const cancelBtn = modal.querySelector(".c-btn-cancel");
      const icoBox = modal.querySelector(".confirm-ico");

      if (!h3 || !p || !confirmBtn || !cancelBtn || !icoBox) {
        const ok = window.confirm(message || "Are you sure?");
        if (callback) callback(ok);
        return;
      }

      h3.textContent = title || "Are you sure?";
      p.textContent = message || "This action cannot be undone.";
      confirmBtn.textContent = confirmText;

      if (isDestructive) {
        modal.classList.remove("is-success");
        icoBox.innerHTML = `
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        `;
      } else {
        modal.classList.add("is-success");
        icoBox.innerHTML = `
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke-linecap="round" stroke-linejoin="round"></path>
            <polyline points="22 4 12 14.01 9 11.01" stroke-linecap="round" stroke-linejoin="round"></polyline>
          </svg>
        `;
      }

      modal.style.display = "flex";
      setTimeout(() => modal.classList.add("is-active"), 10);

      const closeModal = () => {
        modal.classList.remove("is-active");
        setTimeout(() => {
          if (!modal.classList.contains("is-active")) {
            modal.style.display = "none";
          }
        }, 300);
      };

      const newConfirm = confirmBtn.cloneNode(true);
      const newCancel = cancelBtn.cloneNode(true);

      confirmBtn.parentNode.replaceChild(newConfirm, confirmBtn);
      cancelBtn.parentNode.replaceChild(newCancel, cancelBtn);

      newConfirm.addEventListener("click", () => {
        closeModal();
        if (callback) callback(true);
      });

      newCancel.addEventListener("click", () => {
        closeModal();
        if (callback) callback(false);
      });

      modal.onclick = (e) => {
        if (e.target === modal) {
          closeModal();
          if (callback) callback(false);
        }
      };
    };
  }

  function init() {
    setupBurgerMenu();
    setupHeaderScroll();
    setupResourcesDropdown();
    setupTemplateCarousel();
    setupRevealAnimations();
    setupConfirmModal();
  }

  document.addEventListener("DOMContentLoaded", init);
})();