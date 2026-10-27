// Marks posts published since the reader's previous visit with a "New" badge. The previous visit is
// fixed for the whole browsing session, so the badges stay put while moving between pages.
(() => {
  let since = null;
  try {
    since = sessionStorage.getItem("wf-since");
    if (since === null) {
      since = localStorage.getItem("wf-last-visit") || "";
      sessionStorage.setItem("wf-since", since);
    }
    localStorage.setItem("wf-last-visit", new Date().toISOString());
  } catch {
    return;  // storage blocked: no badges
  }
  const cutoff = Date.parse(since);
  if (Number.isNaN(cutoff)) return;  // first visit
  for (const time of document.querySelectorAll(".entry .meta time[datetime]")) {
    if (Date.parse(time.dateTime) <= cutoff) continue;
    const badge = document.createElement("span");
    badge.className = "new-tag";
    badge.textContent = "New";
    time.closest(".meta").append(badge);
    time.closest(".entry").classList.add("is-new");
  }
})();
