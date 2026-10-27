// Tabbed pages (Macros, class pages): one section at a time, picked from the tabs, and a Copy button on each macro.
(() => {
  const sections = [...document.querySelectorAll(".tab-panel")];
  const tabs = [...document.querySelectorAll(".class-tabs a")];
  const show = () => {
    // a link into a section (e.g. one class update) opens the section that holds it
    const target = location.hash.length > 1 && document.getElementById(location.hash.slice(1));
    const shown = sections.find((section) => target && section.contains(target)) ?? sections[0];
    for (const section of sections) section.hidden = section !== shown;
    for (const tab of tabs) {
      if (tab.hash === `#${shown.id}`) tab.setAttribute("aria-current", "page");
      else tab.removeAttribute("aria-current");
    }
  };
  for (const tab of tabs) {
    tab.addEventListener("click", (event) => {
      event.preventDefault();  // switch section without jumping down the page
      history.replaceState(null, "", tab.hash);
      show();
    });
  }
  addEventListener("hashchange", show);
  show();

  if (!navigator.clipboard) return;
  for (const macro of document.querySelectorAll(".macro")) {
    const code = macro.querySelector("code");
    const button = document.createElement("button");
    button.type = "button";
    button.className = "copy-link";
    button.textContent = "Copy";
    button.setAttribute("aria-label", `Copy macro: ${macro.querySelector("h3").textContent}`);
    button.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(code.textContent);
        button.textContent = "Copied";
      } catch {
        getSelection().selectAllChildren(code);  // at least select it for Ctrl+C
        button.textContent = "Press Ctrl+C";
      }
      setTimeout(() => { button.textContent = "Copy"; }, 2000);
    });
    macro.querySelector(".macro-head").append(button);
  }
})();
