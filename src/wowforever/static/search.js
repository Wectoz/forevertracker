// Search page: filters the site's search index (posts, class changes, abilities, talents, racials, recipes, items,
// macros and addons) in the browser, with findInSearch from suggest.js.
(() => {
  const form = document.querySelector("form.search");
  if (!form) return;
  const input = form.querySelector("input");
  const status = document.querySelector(".search-status");
  const list = document.querySelector(".results");
  const LIMIT = 50;
  let items = null;

  const snippet = (text, word) => {
    const at = text.toLowerCase().indexOf(word);
    if (at < 0) return text.slice(0, 200) + (text.length > 200 ? "…" : "");
    const start = Math.max(0, at - 80);
    return (start > 0 ? "…" : "") + text.slice(start, start + 220) + (start + 220 < text.length ? "…" : "");
  };

  const show = () => {
    const query = input.value.trim();
    list.replaceChildren();
    if (!items || !query) {
      status.textContent = query ? "Loading…" : "";
      return;
    }
    const words = query.toLowerCase().split(/\s+/);
    const hits = window.findInSearch(items, query);
    status.textContent = hits.length
      ? `${hits.length} result${hits.length === 1 ? "" : "s"}${hits.length > LIMIT ? `, showing the first ${LIMIT}` : ""}.`
      : `No results for “${query}”.`;
    for (const item of hits.slice(0, LIMIT)) {
      const li = document.createElement("li");
      li.className = "entry";
      const meta = document.createElement("p");
      meta.className = "meta";
      meta.textContent = item.date ? `${item.label} · ${item.date}` : item.label;
      const title = document.createElement("h2");
      const link = document.createElement("a");
      link.href = item.url;
      link.textContent = item.title;
      if (item.external) {
        link.target = "_blank";
        link.rel = "noopener";
      }
      title.append(link);
      li.append(meta, title);
      if (item.text) {
        const text = document.createElement("p");
        text.className = "summary";
        text.textContent = snippet(item.text, words[0]);
        li.append(text);
      }
      list.append(li);
    }
  };

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const url = new URL(location.href);
    url.searchParams.set("q", input.value.trim());
    history.replaceState(null, "", url);
    show();
  });
  input.addEventListener("input", show);
  input.value = new URLSearchParams(location.search).get("q") || "";

  fetch(form.dataset.index)
    .then((response) => {
      if (!response.ok) throw new Error(response.status);
      return response.json();
    })
    .then((data) => { items = data; show(); })
    .catch(() => {
      for (const control of form.elements) control.disabled = true;
      list.replaceChildren();
      status.textContent = "Search is unavailable right now. Please try again later.";
    });
  show();
})();
