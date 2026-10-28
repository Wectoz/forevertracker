// Gives each ability, talent, racial and item name in the notes (span.gl, marked by the server) its in-game tooltip.
(() => {
  const script = document.currentScript;
  const links = document.querySelectorAll(".gl[data-tip]");
  if (!links.length) return;
  fetch(script.dataset.tips).then((response) => response.json()).then((tips) => {
    links.forEach((link, index) => {
      const tip = tips[link.dataset.tip];
      if (!tip) return;
      const box = gameTip(tip, `gl-${index}`, script.dataset.icons);
      link.classList.add("has-tip");
      link.setAttribute("aria-describedby", box.id);
      link.append(box);
    });
  });
})();
