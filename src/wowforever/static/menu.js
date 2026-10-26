// Close the Classes menu when clicking or tabbing elsewhere, or on Escape.
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
