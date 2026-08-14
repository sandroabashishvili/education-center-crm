document.addEventListener("DOMContentLoaded", () => {
  const header = document.querySelector(".topbar");
  const button = document.querySelector("[data-nav-toggle]");
  const menu = document.querySelector("[data-mobile-nav]");
  if (!header || !button || !menu) return;

  const closeMenu = () => {
    button.setAttribute("aria-expanded", "false");
    button.querySelector("[aria-hidden]")?.replaceChildren("☰");
    menu.dataset.open = "false";
    header.dataset.menuOpen = "false";
  };

  button.addEventListener("click", () => {
    const opens = button.getAttribute("aria-expanded") !== "true";
    button.setAttribute("aria-expanded", String(opens));
    button.querySelector("[aria-hidden]")?.replaceChildren(opens ? "✕" : "☰");
    menu.dataset.open = String(opens);
    header.dataset.menuOpen = String(opens);
  });

  menu.addEventListener("click", (event) => {
    if (event.target.closest("a")) closeMenu();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeMenu();
  });
  window.addEventListener("resize", () => {
    if (window.innerWidth > 900) closeMenu();
  });
});
