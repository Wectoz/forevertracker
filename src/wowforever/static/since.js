// Class page: show only the updates since a chosen beta build, patch or hotfix.
(() => {
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
      if (!entry.hidden && !entry.classList.contains("class-dim")) shown++;
    }
    status.textContent = select.value
      ? `${shown} update${shown === 1 ? "" : "s"} with changes since ${select.selectedOptions[0].text}.`
      : "";
  });
  label.hidden = false;
})();
