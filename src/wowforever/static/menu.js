// Open the Classes menu from the Home page's call to action; close it when clicking or
// tabbing elsewhere, or on Escape.
document.addEventListener("click", (event) => {
  const opener = event.target.closest("[data-open-classes]");
  const menu = document.getElementById("classes");
  if (!opener || !menu) return;
  event.preventDefault();
  event.stopImmediatePropagation();  // the outside-click handler below would close it again
  menu.open = true;
  menu.querySelector("ul a").focus();
});

const openMenus = () => document.querySelectorAll("details.class-menu[open]");

document.addEventListener("click", (event) => {
  for (const menu of openMenus()) {
    if (!menu.contains(event.target)) menu.open = false;
  }
});
document.addEventListener("focusin", (event) => {
  for (const menu of openMenus()) {
    if (!menu.contains(event.target)) menu.open = false;
  }
});
document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape") return;
  for (const menu of openMenus()) {
    const hadFocus = menu.contains(document.activeElement);
    menu.open = false;
    if (hadFocus) menu.querySelector("summary").focus();
  }
});
