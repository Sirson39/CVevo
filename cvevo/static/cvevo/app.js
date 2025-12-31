(() => {
  const burger = document.getElementById("burgerBtn");
  const links = document.getElementById("navLinks");

  if (burger && links) {
    burger.addEventListener("click", () => {
      const open = links.classList.toggle("open");
      burger.setAttribute("aria-expanded", String(open));
    });

    links.querySelectorAll("a").forEach(a => {
      a.addEventListener("click", () => {
        links.classList.remove("open");
        burger.setAttribute("aria-expanded", "false");
      });
    });
  }
})();
