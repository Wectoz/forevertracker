// Items page: search and filter every item, each with its tooltip. The filters are kept in the address, to share.
(() => {
  const form = document.querySelector(".item-tools");
  if (!form) return;
  const body = document.querySelector(".items tbody");
  const status = document.querySelector(".it-status");
  const more = document.querySelector(".it-more");
  const fields = [...form.elements].filter((field) => field.name);
  const PAGE = 100;
  const SORTS = {
    level: (a, b) => b.level - a.level,
    required: (a, b) => b.required - a.required || b.level - a.level,
    name: (a, b) => a.name.localeCompare(b.name),
  };
  let items = [];
  let matches = [];
  let shown = 0;

  const cell = (text, className) => {
    const td = document.createElement("td");
    if (className) td.className = className;
    td.textContent = text ?? "";
    return td;
  };

  const row = (item) => {
    const tr = document.createElement("tr");
    const name = document.createElement("span");
    name.className = "with-icon has-tip";
    name.tabIndex = 0;
    const img = Object.assign(document.createElement("img"), {
      className: "icon", src: `${form.dataset.icons}${item.icon}.jpg`, alt: "", width: 24, height: 24, loading: "lazy" });
    const label = Object.assign(document.createElement("span"), { className: `spell q${item.quality}`, textContent: item.name });
    const tip = gameTip(item, `item-${item.id}`, form.dataset.icons);
    name.setAttribute("aria-describedby", tip.id);
    name.append(img, label, tip);
    const first = cell();
    first.append(name);
    const crafted = cell();
    if (item.crafted) {
      crafted.append(Object.assign(document.createElement("a"), {
        href: form.dataset.professions + item.crafted.toLowerCase().replaceAll(" ", "-"), textContent: item.crafted }));
    }
    tr.append(first, cell(item.slot), cell(item.type), cell(item.required || "", "num"), cell(item.level, "num"), crafted);
    return tr;
  };

  const showMore = () => {
    body.append(...matches.slice(shown, shown + PAGE).map(row));
    shown = Math.min(shown + PAGE, matches.length);
    more.hidden = shown >= matches.length;
  };

  const update = () => {
    const value = Object.fromEntries(fields.map((field) => [field.name, field.value.trim()]));
    const words = value.q.toLowerCase().split(/\s+/).filter(Boolean);
    const level = Number(value.level) || 0;
    matches = items.filter((item) => words.every((word) => item.name.toLowerCase().includes(word))
      && (!value.slot || item.slot === value.slot)
      && (!value.type || item.type === value.type)
      && (!value.quality || item.quality >= Number(value.quality))
      && (!level || item.required <= level)
      && (!value.crafted || item.crafted === value.crafted)).sort(SORTS[value.sort] || SORTS.level);
    body.replaceChildren();
    shown = 0;
    showMore();
    status.textContent = matches.length ? `${matches.length} item${matches.length === 1 ? "" : "s"}.` : "No items match.";
    const params = new URLSearchParams(Object.entries(value).filter(([key, v]) => v && !(key === "sort" && v === "level")));
    history.replaceState(null, "", params.size ? `?${params}` : location.pathname);
  };

  const params = new URLSearchParams(location.search);
  for (const field of fields) if (params.has(field.name)) field.value = params.get(field.name);
  fetch(form.dataset.items).then((response) => response.json()).then((data) => {
    items = data;
    update();
    for (const field of fields) field.addEventListener("input", update);
    more.addEventListener("click", showMore);
  }).catch(() => { status.textContent = "The item list could not be loaded. Try reloading the page."; });
})();
