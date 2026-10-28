// Items page: search and filter every item, each with its tooltip, a page at a time. The filters are kept in the
// address, to share.
(() => {
  const form = document.querySelector(".item-tools");
  if (!form) return;
  const body = document.querySelector(".items tbody");
  const status = document.querySelector(".it-status");
  const pagers = [...document.querySelectorAll(".it-pager")];  // above and below the table
  const fields = [...form.elements].filter((field) => field.name);
  const PAGE = 50;
  const SORTS = {
    level: (a, b) => b.level - a.level,
    required: (a, b) => b.required - a.required || b.level - a.level,
    name: (a, b) => a.name.localeCompare(b.name),
  };
  let items = [];
  let matches = [];
  let page = 0;

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

  const show = (number) => {
    const pages = Math.max(1, Math.ceil(matches.length / PAGE));
    page = Math.min(Math.max(number, 0), pages - 1);
    body.replaceChildren(...matches.slice(page * PAGE, (page + 1) * PAGE).map(row));
    for (const pager of pagers) {
      pager.hidden = pages === 1;
      pager.querySelector(".it-page").textContent = `Page ${page + 1} of ${pages}`;
      pager.querySelector(".it-prev").disabled = page === 0;
      pager.querySelector(".it-next").disabled = page === pages - 1;
    }
    const first = page * PAGE + 1;
    status.textContent = matches.length
      ? `${matches.length} item${matches.length === 1 ? "" : "s"}${pages > 1 ? `, showing ${first}–${first + body.children.length - 1}` : ""}.`
      : "No items match.";
  };
  const turn = (step) => {
    show(page + step);
    document.querySelector(".items").scrollIntoView({ block: "start" });
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
    show(0);
    const params = new URLSearchParams(Object.entries(value).filter(([key, v]) => v && !(key === "sort" && v === "level")));
    history.replaceState(null, "", params.size ? `?${params}` : location.pathname);
  };

  const params = new URLSearchParams(location.search);
  for (const field of fields) if (params.has(field.name)) field.value = params.get(field.name);
  fetch(form.dataset.items).then((response) => response.json()).then((data) => {
    items = data;
    update();
    for (const field of fields) field.addEventListener("input", update);
    for (const pager of pagers) {
      pager.querySelector(".it-prev").addEventListener("click", () => turn(-1));
      pager.querySelector(".it-next").addEventListener("click", () => turn(1));
    }
  }).catch(() => { status.textContent = "The item list could not be loaded. Try reloading the page."; });
})();
