// Talent calculator on class pages: learn and unlearn ranks by Classic's rules, and share the build as ?talents=.
(() => {
  const calc = document.querySelector(".talent-calc");
  if (!calc) return;
  const trees = JSON.parse(calc.querySelector(".talent-data").textContent);
  const MAX_POINTS = 51;  // level 60: one point per level from 10
  const PER_ROW = 5;  // points spent in a tree that open its next row
  const points = trees.map((tree) => tree.talents.map(() => 0));
  const sections = [...calc.querySelectorAll(".talent-tree")];

  const sum = (list) => list.reduce((a, b) => a + b, 0);
  const total = () => sum(points.map(sum));
  const spentBelow = (t, tier) => sum(trees[t].talents.map((talent, i) => (talent.tier < tier ? points[t][i] : 0)));
  const rowOpen = (t, talent) => spentBelow(t, talent.tier) >= PER_ROW * talent.tier;
  const prereqMet = (t, talent) => !talent.requires || points[t][talent.requires[0]] >= talent.requires[1];

  const canLearn = (t, i) => {
    const talent = trees[t].talents[i];
    return points[t][i] < talent.ranks.length && total() < MAX_POINTS && rowOpen(t, talent) && prereqMet(t, talent);
  };
  const canUnlearn = (t, i) => {
    if (!points[t][i]) return false;
    points[t][i] -= 1;  // try it: every learned talent must still be allowed
    const ok = trees[t].talents.every((talent, j) => !points[t][j] || (rowOpen(t, talent) && prereqMet(t, talent)));
    points[t][i] += 1;
    return ok;
  };

  const line = (text, className) => {
    const span = document.createElement("span");
    span.className = className;
    span.textContent = text;
    return span;
  };
  const tooltip = (t, i) => {
    const talent = trees[t].talents[i];
    const rank = points[t][i];
    const max = talent.ranks.length;
    const parts = [line(talent.name, "spell"), line(`Rank ${rank}/${max}`, "tip-line")];
    if (!rowOpen(t, talent)) parts.push(line(`Needs ${PER_ROW * talent.tier} points in ${trees[t].name}`, "tip-line unmet"));
    if (!prereqMet(t, talent)) {
      const [from, needed] = talent.requires;
      parts.push(line(`Needs ${needed} ${needed > 1 ? "points" : "point"} in ${trees[t].talents[from].name}`, "tip-line unmet"));
    }
    const current = talent.ranks[Math.max(rank - 1, 0)];
    if (current) parts.push(line(current, "desc"));
    else if (talent.ranks[0]) {
      // the client only ships some talents' first rank before launch; the rest come from the servers
      parts.push(line(talent.ranks[0], "desc"),
        line("Only one rank of this talent is in the game files so far; its numbers may be for 1 point or for all.", "tip-line"));
    }
    if (rank && rank < max && talent.ranks[rank]) parts.push(line("Next rank:", "tip-line"), line(talent.ranks[rank], "desc next"));
    return parts;
  };

  const code = () => points.map((tree) => tree.join("").replace(/0+$/, "")).join("-").replace(/-+$/, "");

  const render = (share = true) => {
    sections.forEach((section, t) => {
      section.querySelector(".tree-points").textContent = sum(points[t]);
      for (const button of section.querySelectorAll(".talent")) {
        const i = Number(button.dataset.index);
        const talent = trees[t].talents[i];
        const rank = points[t][i];
        button.classList.toggle("learned", rank > 0);
        button.classList.toggle("maxed", rank === talent.ranks.length);
        button.classList.toggle("open", rank < talent.ranks.length && canLearn(t, i));
        button.querySelector(".talent-rank").textContent = `${rank}/${talent.ranks.length}`;
        button.setAttribute("aria-label", `${talent.name}, ${rank} of ${talent.ranks.length}`);
        button.querySelector(".tip").replaceChildren(...tooltip(t, i));
      }
      for (const arrow of section.querySelectorAll(".talent-arrow")) {
        arrow.classList.toggle("met", prereqMet(t, trees[t].talents[Number(arrow.dataset.to)]));
      }
    });
    const spent = total();
    calc.querySelector(".tc-left").textContent = MAX_POINTS - spent;
    calc.querySelector(".tc-level").textContent = spent ? 9 + spent : 10;
    const url = spent ? `?talents=${code()}#talents` : `${location.pathname}#talents`;
    calc.querySelector(".tc-link").href = url;
    if (share) history.replaceState(null, "", url);
  };

  const change = (event, learn) => {
    const button = event.target.closest(".talent");
    if (!button) return;
    event.preventDefault();
    const t = sections.indexOf(button.closest(".talent-tree"));
    const i = Number(button.dataset.index);
    if (learn && canLearn(t, i)) points[t][i] += 1;
    else if (!learn && canUnlearn(t, i)) points[t][i] -= 1;
    else return;
    render();
  };
  calc.addEventListener("click", (event) => change(event, !event.shiftKey));
  calc.addEventListener("contextmenu", (event) => change(event, false));
  calc.addEventListener("keydown", (event) => {
    if (event.key === "Delete" || event.key === "Backspace") change(event, false);
  });
  calc.querySelector(".tc-reset").addEventListener("click", () => {
    for (const tree of points) tree.fill(0);
    render();
  });

  // a shared build: learn it point by point, so a hand-edited link can't break the rules
  const shared = (new URLSearchParams(location.search).get("talents") ?? "").split("-");
  let added = true;
  while (added) {
    added = false;
    shared.forEach((ranks, t) => {
      if (!trees[t]) return;
      [...ranks].forEach((wanted, i) => {
        while (i < trees[t].talents.length && points[t][i] < Number(wanted) && canLearn(t, i)) {
          points[t][i] += 1;
          added = true;
        }
      });
    });
  }
  // only rewrite the address once someone uses the calculator or opened a shared build
  render(total() > 0);
})();
