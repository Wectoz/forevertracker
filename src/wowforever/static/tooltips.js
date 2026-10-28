// Tooltips (.has-tip > .tip) show on hover and focus in CSS. This places them against the window (position: fixed),
// so scrolling tables and cards can't cut them off: beside the pointer as it moves (as on Wowhead), under the item
// when it has keyboard focus or was tapped, and always inside the window.
(() => {
  const GAP = 16;
  const MARGIN = 8;
  const place = (event) => {
    const host = event.target.closest?.(".has-tip");
    const tip = host?.querySelector(":scope > .tip");
    if (!tip) return;
    const area = host.getBoundingClientRect();
    const pointer = event.type === "mousemove";
    const put = (x, y) => Object.assign(tip.style, { position: "fixed", left: `${x}px`, top: `${y}px` });
    let x = pointer ? event.clientX + GAP : area.left;
    let y = pointer ? event.clientY + GAP : area.bottom + 4;
    put(x, y);
    const box = tip.getBoundingClientRect();
    if (box.right > innerWidth - MARGIN) x = pointer ? event.clientX - GAP - box.width : innerWidth - MARGIN - box.width;
    if (box.bottom > innerHeight - MARGIN) {  // no room below: above the pointer or the item, if that fits
      const above = (pointer ? event.clientY - GAP : area.top - 4) - box.height;
      y = above >= MARGIN ? above : Math.max(MARGIN, innerHeight - MARGIN - box.height);
    }
    put(Math.max(MARGIN, x), y);
  };
  addEventListener("mousemove", place);
  addEventListener("focusin", place);
  // touch screens: a tap focuses the item, which shows its tooltip
  addEventListener("click", (event) => event.target.closest?.(".has-tip[tabindex]")?.focus());
})();

// An ability, talent, racial or item tooltip built from its data (tooltips.json, items.json), for pages that add
// them in the browser.
window.gameTip = (tip, id, icons) => {
  const el = (tag, className, text) => {
    const node = document.createElement(tag);
    node.className = className;
    if (text) node.textContent = text;
    return node;
  };
  const box = el("span", "tip");
  box.role = "tooltip";
  box.id = id;
  const head = el("span", "with-icon");
  if (tip.icon) {
    const img = el("img", "icon");
    Object.assign(img, { src: `${icons}${tip.icon}.jpg`, alt: "", width: 24, height: 24, loading: "lazy" });
    head.append(img);
  }
  head.append(el("span", tip.quality ? `spell q${tip.quality}` : "spell", tip.name));
  box.append(head);
  if (tip.kind) box.append(el("span", "tip-line", tip.kind));
  (tip.lines || []).forEach((line) => box.append(el("span", "tip-stat", line)));
  (tip.effects || []).forEach((line) => box.append(el("span", "tip-effect", line)));
  const desc = tip.desc ?? tip.description;
  if (desc) box.append(tip.lines ? el("span", "tip-flavor", `"${desc}"`) : el("span", "desc", desc));
  return box;
};
