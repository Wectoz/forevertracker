// Gives each ability, talent, racial and item name in the notes (span.gl, marked by the server) its in-game tooltip.
(() => {
  const script = document.currentScript;
  const links = document.querySelectorAll(".gl[data-tip]");
  if (!links.length) return;
  const el = (tag, className, text) => {
    const node = document.createElement(tag);
    node.className = className;
    if (text) node.textContent = text;
    return node;
  };
  fetch(script.dataset.tips).then((response) => response.json()).then((tips) => {
    links.forEach((link, index) => {
      const tip = tips[link.dataset.tip];
      if (!tip) return;
      const box = el("span", "tip");
      box.role = "tooltip";
      box.id = `gl-${index}`;
      const head = el("span", "with-icon");
      if (tip.icon) {
        const img = el("img", "icon");
        Object.assign(img, { src: `${script.dataset.icons}${tip.icon}.jpg`, alt: "", width: 24, height: 24, loading: "lazy" });
        head.append(img);
      }
      head.append(el("span", tip.quality ? `spell q${tip.quality}` : "spell", tip.name));
      box.append(head, el("span", "tip-line", tip.kind));
      (tip.lines || []).forEach((line) => box.append(el("span", "tip-stat", line)));
      (tip.effects || []).forEach((line) => box.append(el("span", "tip-effect", line)));
      if (tip.desc) box.append(tip.lines ? el("span", "tip-flavor", `"${tip.desc}"`) : el("span", "desc", tip.desc));
      link.classList.add("has-tip");
      link.setAttribute("aria-describedby", box.id);
      link.append(box);
    });
  });
})();
