// ---- interactive rally timeline (mock) ----
(function () {
  const track = document.getElementById("track");
  if (!track) return;

  const num = document.getElementById("rallyNum");
  const who = document.getElementById("rallyWho");
  const meta = document.getElementById("rallyMeta");

  const breaks = [31, 63]; // % positions of set breaks
  breaks.forEach((p) => {
    const b = document.createElement("div");
    b.className = "mock__break";
    b.style.left = p + "%";
    track.appendChild(b);
  });

  let rally = 1;
  let set = 1;
  let active = null;
  const serves = [];

  for (let p = 2; p < 97; p += 1.6 + Math.random() * 2.2) {
    if (breaks.some((b) => Math.abs(p - b) < 2.5)) {
      set = Math.min(set + 1, 3);
      continue;
    }
    serves.push({ p, rally: rally++, set, home: Math.random() > 0.5 });
  }

  serves.forEach((s) => {
    const el = document.createElement("div");
    el.className = "mock__serve" + (s.home ? "" : " opp");
    el.style.left = s.p + "%";
    el.title = "Rally " + s.rally;
    el.addEventListener("click", () => {
      if (active) active.classList.remove("active");
      el.classList.add("active");
      active = el;
      num.textContent = "Rally " + s.rally;
      who.textContent = s.home ? "Home serve" : "Opponent serve";
      who.style.color = s.home ? "var(--serve)" : "var(--net)";
      meta.textContent = "SET " + s.set + " · TAP ANY MARK BELOW";
    });
    track.appendChild(el);
  });

  // pre-select one so the screen never looks empty
  const marks = track.querySelectorAll(".mock__serve");
  const mid = marks[Math.floor(marks.length / 2)];
  if (mid) mid.click();
})();

// Entrance reveal is CSS-only (.reveal keyframes) — no JS gate, so a slow
// or failed script can never leave a section stuck invisible.
