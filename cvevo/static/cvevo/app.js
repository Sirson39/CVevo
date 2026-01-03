(() => {
  console.log("✅ CVevo app.js loaded");
  document.documentElement.classList.add("js");

  // Burger menu
  const burger = document.getElementById("burgerBtn");
  const links = document.getElementById("navLinks");

  if (burger && links) {
    burger.addEventListener("click", () => {
      const open = links.classList.toggle("open");
      burger.setAttribute("aria-expanded", String(open));
    });

    // Close mobile nav when clicking normal links
    links.querySelectorAll("a").forEach((a) => {
      a.addEventListener("click", () => {
        links.classList.remove("open");
        burger.setAttribute("aria-expanded", "false");
      });
    });
  }

  // Header scroll effect
  const header = document.querySelector(".site-header");
  const onScroll = () => {
    if (!header) return;
    header.classList.toggle("scrolled", window.scrollY > 10);
  };
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  // ✅ Resources dropdown (works on mobile click + keyboard)
  const dd = document.getElementById("resourcesDd");
  const ddBtn = dd ? dd.querySelector(".dd-btn") : null;
  const ddMenu = document.getElementById("resourcesMenu");

  const closeDropdown = () => {
    if (!dd || !ddBtn) return;
    dd.classList.remove("open");
    ddBtn.setAttribute("aria-expanded", "false");
  };

  if (dd && ddBtn) {
    ddBtn.addEventListener("click", (e) => {
      e.preventDefault();
      const isOpen = dd.classList.toggle("open");
      ddBtn.setAttribute("aria-expanded", String(isOpen));
    });

    // Close when clicking outside
    document.addEventListener("click", (e) => {
      if (!dd.contains(e.target)) closeDropdown();
    });

    // Close when clicking any dropdown link
    ddMenu?.querySelectorAll("a").forEach((a) => {
      a.addEventListener("click", () => closeDropdown());
    });

    // Escape closes
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closeDropdown();
    });
  }

    // ✅ Templates carousel (Prev/Next + Dots + Auto-slide)
  const strip = document.getElementById("templateStrip");
  const prevBtn = document.querySelector(".t-prev");
  const nextBtn = document.querySelector(".t-next");
  const dotsWrap = document.getElementById("templateDots");
  const shell = document.getElementById("templateShell");

  const scrollByCard = (dir) => {
    if (!strip) return;
    const card = strip.querySelector(".template-card");
    const gap = 18;
    const step = card ? card.getBoundingClientRect().width + gap : 360;
    strip.scrollBy({ left: dir * step, behavior: "smooth" });
  };

  prevBtn?.addEventListener("click", () => scrollByCard(-1));
  nextBtn?.addEventListener("click", () => scrollByCard(1));

  const buildDots = () => {
    if (!strip || !dotsWrap) return;
    const cards = [...strip.querySelectorAll(".template-card")];
    dotsWrap.innerHTML = "";
    cards.forEach((_, i) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "dot";
      b.setAttribute("aria-label", `Go to template ${i + 1}`);
      b.addEventListener("click", () => {
        const card = strip.querySelectorAll(".template-card")[i];
        card?.scrollIntoView({ behavior: "smooth", inline: "center", block: "nearest" });
      });
      dotsWrap.appendChild(b);
    });
  };

  const updateActiveDot = () => {
    if (!strip || !dotsWrap) return;
    const cards = [...strip.querySelectorAll(".template-card")];
    const dots = [...dotsWrap.querySelectorAll(".dot")];
    if (!cards.length || !dots.length) return;

    const stripRect = strip.getBoundingClientRect();
    const centerX = stripRect.left + stripRect.width / 2;

    let bestIdx = 0, bestDist = Infinity;
    cards.forEach((c, i) => {
      const r = c.getBoundingClientRect();
      const cCenter = r.left + r.width / 2;
      const dist = Math.abs(centerX - cCenter);
      if (dist < bestDist) { bestDist = dist; bestIdx = i; }
    });

    dots.forEach((d, i) => d.classList.toggle("active", i === bestIdx));
  };

  let autoTimer = null;
  const startAuto = () => {
    if (!strip) return;
    stopAuto();
    autoTimer = setInterval(() => {
      const nearEnd = strip.scrollLeft + strip.clientWidth >= strip.scrollWidth - 10;
      if (nearEnd) strip.scrollTo({ left: 0, behavior: "smooth" });
      else scrollByCard(1);
    }, 3500);
  };
  const stopAuto = () => {
    if (autoTimer) clearInterval(autoTimer);
    autoTimer = null;
  };

  if (strip && dotsWrap) {
    buildDots();
    updateActiveDot();

    strip.addEventListener("scroll", () => window.requestAnimationFrame(updateActiveDot));
    window.addEventListener("resize", () => updateActiveDot());

    // pause auto on user interaction
    shell?.addEventListener("mouseenter", stopAuto);
    shell?.addEventListener("mouseleave", startAuto);
    shell?.addEventListener("focusin", stopAuto);
    shell?.addEventListener("focusout", startAuto);

    startAuto();
  }


  // Reveal on scroll
  const els = Array.from(document.querySelectorAll(".reveal"));
  console.log("🔎 reveal elements:", els.length);

  if (!els.length) return;

  const revealNow = () => els.forEach((el) => el.classList.add("in"));

  if (!("IntersectionObserver" in window)) {
    revealNow();
    return;
  }

  const io = new IntersectionObserver(
    (entries, obs) => {
      entries.forEach((e) => {
        if (e.isIntersecting) {
          e.target.classList.add("in");
          obs.unobserve(e.target);
        }
      });
    },
    { threshold: 0.08, rootMargin: "0px 0px -5% 0px" }
  );

  els.forEach((el) => io.observe(el));
})();
