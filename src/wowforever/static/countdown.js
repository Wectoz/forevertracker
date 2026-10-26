// Ticks the bronze countdown plate once a minute; the server already rendered the starting values.
(() => {
  const plate = document.querySelector(".plate[data-launch]");
  const launch = plate && Date.parse(plate.dataset.launch);
  if (!plate || Number.isNaN(launch)) return;
  const units = {
    days: plate.querySelector('[data-unit="days"]'),
    hours: plate.querySelector('[data-unit="hours"]'),
    minutes: plate.querySelector('[data-unit="minutes"]'),
  };
  if (!units.days) return;
  const pad = (n) => String(n).padStart(2, "0");
  const tick = () => {
    const minutes = Math.max(0, Math.floor((launch - Date.now()) / 60000));
    units.days.textContent = pad(Math.floor(minutes / 1440));
    units.hours.textContent = pad(Math.floor((minutes % 1440) / 60));
    units.minutes.textContent = pad(minutes % 60);
    if (minutes === 0) {
      // Launched: the static page may be up to an hour old, so switch the plate here.
      plate.querySelector(".plate-label").textContent = "Live since Nov 4";
      plate.querySelector(".digits").remove();
      plate.setAttribute("aria-label", "Live since Nov 4");
      return false;
    }
    return true;
  };
  if (tick()) {
    const timer = setInterval(() => tick() || clearInterval(timer), 15000);
  }
})();
