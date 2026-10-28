// Site search shared by the search page and the menu's search box. findInSearch filters the search index; names that
// match come first, so "Charge" finds the ability before the notes. The menu box shows the top few as suggestions,
// loading the index only once someone starts to search.
window.findInSearch = (items, query) => {
  const words = query.toLowerCase().split(/\s+/).filter(Boolean);
  const phrase = words.join(" ");
  const rank = (item) => {
    const title = item.title.toLowerCase();
    return title === phrase ? 0 : title.startsWith(phrase) ? 1 : words.every((word) => title.includes(word)) ? 2 : 3;
  };
  return items.filter((item) => {
    const haystack = `${item.title} ${item.label} ${item.text}`.toLowerCase();
    return words.every((word) => haystack.includes(word));
  }).map((item) => [rank(item), item]).sort((a, b) => a[0] - b[0]).map(([, item]) => item);  // stable: newest first within a rank
};

(() => {
  const form = document.querySelector("form.nav-search");
  if (!form) return;
  const input = form.querySelector("input");
  const list = document.createElement("ul");
  list.className = "suggestions";
  list.id = "nav-suggestions";
  list.setAttribute("role", "listbox");
  list.hidden = true;
  form.append(list);
  input.setAttribute("role", "combobox");
  input.setAttribute("aria-controls", list.id);
  input.setAttribute("aria-autocomplete", "list");
  input.setAttribute("aria-expanded", "false");

  const LIMIT = 8;
  let items = null;
  let loading = null;
  let active = -1;

  const load = () => loading ??= fetch(form.dataset.index)
    .then((response) => {
      if (!response.ok) throw new Error(response.status);
      return response.json();
    })
    .then((data) => { items = data; show(); })
    .catch(() => { loading = null; });  // the box still submits to the search page

  const options = () => [...list.querySelectorAll("[role=option]")];
  const close = () => {
    list.hidden = true;
    input.setAttribute("aria-expanded", "false");
    input.removeAttribute("aria-activedescendant");
    active = -1;
  };
  const highlight = (index) => {
    const all = options();
    active = (index + all.length) % all.length;
    all.forEach((option, i) => option.setAttribute("aria-selected", String(i === active)));
    input.setAttribute("aria-activedescendant", all[active].id);
  };

  const option = (href, i) => {
    const link = document.createElement("a");
    link.href = href;
    link.id = `suggestion-${i}`;
    link.setAttribute("role", "option");
    link.setAttribute("aria-selected", "false");
    link.tabIndex = -1;
    const li = document.createElement("li");
    li.setAttribute("role", "presentation");
    li.append(link);
    list.append(li);
    return link;
  };

  const show = () => {
    const query = input.value.trim();
    list.replaceChildren();
    if (query.length < 2 || !items) return close();
    window.findInSearch(items, query).slice(0, LIMIT).forEach((item, i) => {
      const link = option(item.url, i);
      if (item.external) {
        link.target = "_blank";
        link.rel = "noopener";
      }
      const label = document.createElement("small");
      label.textContent = item.label;
      link.append(item.title, label);
    });
    const all = option(`${form.action}?q=${encodeURIComponent(query)}`, LIMIT);
    all.className = "see-all";
    all.textContent = `See all results for “${query}”`;
    list.hidden = false;
    input.setAttribute("aria-expanded", "true");
    active = -1;
  };

  input.addEventListener("focus", load);
  input.addEventListener("input", () => { load(); show(); });
  input.addEventListener("keydown", (event) => {
    if (list.hidden) return;
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      highlight(active + (event.key === "ArrowDown" ? 1 : -1));
    } else if (event.key === "Enter" && active >= 0) {
      event.preventDefault();
      options()[active].click();
    } else if (event.key === "Escape") {
      close();
    }
  });
  list.addEventListener("mousedown", (event) => event.preventDefault());  // keep focus in the box so a click lands
  form.addEventListener("focusout", (event) => {
    if (!form.contains(event.relatedTarget)) close();
  });
})();
