// Tooltips (.has-tip > .tip) show on hover and focus in CSS; this keeps them inside the window and lets a tap show one.
(() => {
  const place = (event) => {
    const tip = event.target.closest?.(".has-tip")?.querySelector(":scope > .tip");
    if (!tip) return;
    tip.style.translate = "";
    const box = tip.getBoundingClientRect();
    const margin = 8;
    let dx = 0;
    if (box.right > innerWidth - margin) dx = innerWidth - margin - box.right;
    if (box.left + dx < margin) dx = margin - box.left;
    // open above when there is no room below
    const dy = box.bottom > innerHeight - margin && box.height + margin < box.top ? -(box.height + tip.parentElement.offsetHeight + 8) : 0;
    tip.style.translate = `${dx}px ${dy}px`;
  };
  addEventListener("mouseover", place);
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
