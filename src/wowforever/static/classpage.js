// Class page: show only the updates since a chosen beta build, patch or hotfix, and copy a link to one update.
(() => {
  if (navigator.clipboard) {
    for (const entry of document.querySelectorAll(".class-update[id]")) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "copy-link";
      button.textContent = "Copy link";
      button.addEventListener("click", async () => {
        const url = new URL(location.href);
        url.hash = entry.id;
        try {
          await navigator.clipboard.writeText(url.href);
          button.textContent = "Link copied";
        } catch {
          location.hash = entry.id;  // at least put the link in the address bar
          button.textContent = "Link in address bar";
        }
        setTimeout(() => { button.textContent = "Copy link"; }, 2000);
      });
      entry.querySelector(".meta").append(button);
    }
  }

  const label = document.querySelector(".since");
  if (!label) return;
  const select = label.querySelector("select");
  const status = document.querySelector(".since-status");
  const entries = [...document.querySelectorAll(".class-update")];
  select.addEventListener("change", () => {
    const cutoff = select.value ? Date.parse(select.value) : -Infinity;
    let shown = 0;
    for (const entry of entries) {
      const time = entry.querySelector("time[datetime]");
      entry.hidden = Date.parse(time.dateTime) < cutoff;
      // The sidebar lists only the updates on show, so none of its links lead to a hidden update.
      const link = entry.id && document.querySelector(`.sidebar a[href="#${CSS.escape(entry.id)}"]`);
      if (link) link.closest("li").hidden = entry.hidden;
      if (!entry.hidden && !entry.classList.contains("class-dim")) shown++;
    }
    status.textContent = select.value
      ? `${shown} update${shown === 1 ? "" : "s"} with changes since ${select.selectedOptions[0].text}.`
      : "";
  });
  label.hidden = false;
})();
