// Close the Classes menu when clicking elsewhere or pressing Escape.
document.addEventListener("click", (event) => {
  for (const menu of document.querySelectorAll("details.class-menu[open]")) {
    if (!menu.contains(event.target)) menu.open = false;
  }
});
document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape") return;
  for (const menu of document.querySelectorAll("details.class-menu[open]")) {
    menu.open = false;
    menu.querySelector("summary").focus();
  }
});
