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
