// Profession pages: search and filter recipes across every skill range, and colour them by "my skill" as in game.
(() => {
  const form = document.querySelector(".recipe-tools");
  if (!form) return;
  form.hidden = false;
  const search = form.querySelector(".rt-search");
  const source = form.querySelector(".rt-source");
  const slot = form.querySelector(".rt-slot");
  const skill = form.querySelector(".rt-skill");
  const status = document.querySelector(".rt-status");
  const sections = [...document.querySelectorAll(".tab-panel")];
  const tabs = document.querySelector(".class-tabs");
  const rows = [...document.querySelectorAll(".recipes tbody tr")];
  const COLORS = ["sc-orange", "sc-yellow", "sc-green", "sc-grey"];

  // the game's colours: orange below yellow, green from halfway to grey, grey from grey up
  const color = (mine, row) => {
    const yellow = Number(row.dataset.yellow);
    const grey = Number(row.dataset.grey);
    if (mine < yellow) return "sc-orange";
    if (mine < (yellow + grey) / 2) return "sc-yellow";
    return mine < grey ? "sc-green" : "sc-grey";
  };

  const update = () => {
    const words = search.value.trim().toLowerCase().split(/\s+/).filter(Boolean);
    const filtering = words.length || source.value || slot?.value;
    const mine = Number(skill.value) || 0;
    let shown = 0;
    for (const row of rows) {
      const match = words.every((word) => row.dataset.search.includes(word))
        && (!source.value || row.dataset.source === source.value)
        && (!slot?.value || row.dataset.slot === slot.value);
      row.hidden = !match;
      shown += match;
      row.classList.remove(...COLORS, "too-high");
      if (mine) row.classList.add(color(mine, row), ...(Number(row.dataset.skill) > mine ? ["too-high"] : []));
    }
    if (filtering) {
      // results from every skill range at once; the tabs come back when the filters are cleared
      tabs.hidden = true;
      for (const section of sections) section.hidden = !section.querySelector("tbody tr:not([hidden])");
      status.textContent = shown ? `${shown} recipe${shown === 1 ? "" : "s"} found.` : "No recipes match.";
    } else {
      tabs.hidden = false;
      status.textContent = "";
      dispatchEvent(new HashChangeEvent("hashchange"));  // tabs.js shows the picked range again
    }
    if (mine) status.textContent += " Orange always gives a point, yellow usually, green rarely, grey never; faded recipes need more skill to learn.";
  };
  for (const input of [search, source, slot, skill]) input?.addEventListener("input", update);
  // a search result links here with the recipe's name
  const query = new URLSearchParams(location.search).get("q");
  if (query) {
    search.value = query;
    update();
  }
})();
