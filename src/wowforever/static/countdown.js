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

  // The launch time in the reader's own time zone, unless that is Pacific time anyway.
  const local = plate.querySelector(".plate-local");
  const when = { weekday: "short", month: "short", day: "numeric", hour: "numeric", minute: "2-digit" };
  const inZone = (timeZone) => new Intl.DateTimeFormat(undefined, { ...when, timeZone }).format(launch);
  if (local && inZone(undefined) !== inZone("America/Los_Angeles")) {
    local.textContent = `Your time: ${new Intl.DateTimeFormat(undefined, { ...when, timeZoneName: "short" }).format(launch)}`;
    local.hidden = false;
  }
  const pad = (n) => String(n).padStart(2, "0");
  const tick = () => {
    const minutes = Math.max(0, Math.floor((launch - Date.now()) / 60000));
    units.days.textContent = pad(Math.floor(minutes / 1440));
    units.hours.textContent = pad(Math.floor((minutes % 1440) / 60));
    units.minutes.textContent = pad(minutes % 60);
    if (minutes === 0) {
      // Launched: the static page may be up to an hour old, so switch the plate here.
      plate.querySelector(".plate-label").textContent = "Live now · Day 1";
      plate.querySelector(".digits").remove();
      if (local) local.remove();
      plate.setAttribute("aria-label", "Live now · Day 1");
      return false;
    }
    return true;
  };
  if (tick()) {
    const timer = setInterval(() => tick() || clearInterval(timer), 15000);
  }
})();
