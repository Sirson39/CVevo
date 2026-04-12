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

  function init() {
    setupBurgerMenu();
    setupHeaderScroll();
    setupResourcesDropdown();
    setupTemplateCarousel();
    setupRevealAnimations();
  }

  document.addEventListener("DOMContentLoaded", init);
})();
