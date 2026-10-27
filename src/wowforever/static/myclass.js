// Remembers the reader's class: set from a class page, then highlighted in the menu, on the Home call
// to action, and on forum notes posts that have changes for it. The Macros page opens at its macros.
(() => {
  const KEY = "wf-my-class";
  const read = () => { try { return localStorage.getItem(KEY); } catch { return null; } };
  const write = (value) => {
    try { value ? localStorage.setItem(KEY, value) : localStorage.removeItem(KEY); } catch { /* not remembered */ }
  };
  const menuLink = (cls) => cls && document.querySelector(`.class-menu a[href$="/classes/${CSS.escape(cls)}"]`);

  const toggle = document.querySelector(".my-class-toggle");
  if (toggle) {
    const name = toggle.dataset.name;
    const render = () => {
      const mine = read() === toggle.dataset.class;
      toggle.setAttribute("aria-pressed", String(mine));
      toggle.textContent = mine ? `★ ${name} is my class` : `☆ Make ${name} my class`;
    };
    toggle.addEventListener("click", () => {
      write(read() === toggle.dataset.class ? null : toggle.dataset.class);
      render();
    });
    render();
    toggle.hidden = false;
  }

  const mine = read();
  const macros = mine && !location.hash && document.querySelector(`.macro-class#${CSS.escape(mine)}`);
  if (macros) macros.scrollIntoView();
  const link = menuLink(mine);
  if (!link) return;
  const name = link.textContent.trim();
  link.classList.add("my-class");

  const cta = document.querySelector(".cta [data-open-classes]");
  if (cta) {
    cta.removeAttribute("data-open-classes");
    cta.href = link.href;
    cta.textContent = `Your ${name} patch notes →`;
  }

  for (const entry of document.querySelectorAll(".entry[data-classes]")) {
    if (!entry.dataset.classes.split(" ").includes(mine)) continue;
    const badge = document.createElement("a");
    badge.className = "my-class-tag";
    badge.href = link.href;
    badge.style.color = link.style.color;
    badge.textContent = `${name} changes →`;
    entry.querySelector(".entry-body").append(badge);
    entry.classList.add("has-my-class");
    entry.style.setProperty("--my-class", link.style.color);
  }
})();
