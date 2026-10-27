// Macros page: a Copy button on each macro.
(() => {
  if (navigator.clipboard) {
    for (const macro of document.querySelectorAll(".macro")) {
      const code = macro.querySelector("code");
      const button = document.createElement("button");
      button.type = "button";
      button.className = "copy-link";
      button.textContent = "Copy";
      button.setAttribute("aria-label", `Copy macro: ${macro.querySelector("h3").textContent}`);
      button.addEventListener("click", async () => {
        try {
          await navigator.clipboard.writeText(code.textContent);
          button.textContent = "Copied";
        } catch {
          getSelection().selectAllChildren(code);  // at least select it for Ctrl+C
          button.textContent = "Press Ctrl+C";
        }
        setTimeout(() => { button.textContent = "Copy"; }, 2000);
      });
      macro.querySelector(".meta").append(button);
    }
  }
})();
