// Reader v0 (KICKOFF.md, T6). Reads data/<law>.json (contract 4). All state lives in the URL hash, so
// every view is a permanent link: #/<law>/<file>@<date> to read, @<from>..<to> to diff, ?view=blame,
// and ?published for "as published" instead of "as in force".

export function versionAt(law, file, date, mode = "in_force") {
  let hit = null;
  for (const v of file.versions) {
    const d = law.commits[v.commit][mode];
    if (d && d <= date) hit = v; // export.py guarantees in-force dates run in commit order
  }
  return hit;
}

export function parseRoute(hash) {
  const [path, query = ""] = decodeURIComponent(hash).replace(/^#\/?/, "").split("?");
  const [law = "", ...rest] = path.split("/");
  const [file = "", dates = ""] = rest.join("/").split("@");
  const day = (d) => (/^\d{4}-\d{2}-\d{2}$/.test(d) ? d : null); // anything else could carry markup
  const [from, date] = dates.includes("..") ? dates.split("..").map(day) : [null, day(dates)];
  const q = new URLSearchParams(query);
  const view = from ? "diff" : q.get("view") === "blame" ? "blame" : "read";
  return { law, file, date, from, view, mode: q.has("published") ? "enacted" : "in_force" };
}

export function route({ law, file, date, from, view, mode }) {
  let h = `#/${law}`;
  if (file) h += `/${file}`;
  if (view === "diff") h += `@${from}..${date}`;
  else if (date && view !== "blame") h += `@${date}`;
  const q = [view === "blame" && "view=blame", mode === "enacted" && "published"].filter(Boolean);
  return q.length ? `${h}?${q.join("&")}` : h;
}

const TODAY = new Date(Date.now() + 5.5 * 36e5).toISOString().slice(0, 10); // the date in India (UTC+5:30)
const $ = (s) => document.querySelector(s);
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
const fmt = (d) => d
  ? new Date(d + "T00:00:00Z").toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" })
  : "not yet notified or unknown";
const label = (c) => c.act.replace(/^The Constitution \((.+)\) Act, \d{4}$/, "$1") + (c.section ? `, s. ${c.section}` : "");
const id = (f) => f.path.slice(0, -3);
const latest = (f) => [...f.versions].reverse().find((v) => v.text)?.text ?? "";
const heading = (f) => {
  const first = latest(f).split("\n")[0];
  const name = id(f).split("/").pop().replace(/-/g, " ");
  return first.startsWith("# ") ? first.slice(2) : name[0].toUpperCase() + name.slice(1);
};

// The law files use a small Markdown subset: "# heading", nested "- " lists for depth, "*emphasis*".
const inline = (s) => esc(s).replace(/\*(.+?)\*/g, "<em>$1</em>");
function lineHtml(line) {
  if (line.startsWith("# ")) return `<h2>${inline(line.slice(2))}</h2>`;
  const m = line.match(/^( *)- (.*)$/);
  if (m) return `<p style="--depth:${m[1].length / 2}">${inline(m[2])}</p>`;
  return line.trim() ? `<p>${inline(line)}</p>` : "";
}
const plain = (text) => (text ?? "").split("\n").filter((l) => l.trim())
  .map((l) => l.replace(/^# /, "").replace(/^( *)- /, (_, s) => " ".repeat(s.length / 2)).replace(/\*/g, ""))
  .join("\n");

const cache = {};
const load = (law) => (cache[law] ??= fetch(`data/${law}.json`).then((r) => {
  if (!r.ok) throw new Error(`No data for "${law}".`);
  return r.json();
}).catch((e) => { delete cache[law]; throw e; }));

async function home(app) {
  const r = await fetch("data/laws.json");
  if (!r.ok) throw new Error("No laws exported yet. Run publish/export.py.");
  const laws = await r.json();
  app.innerHTML = `<h1>Indian law, with its history</h1>
    <p class="lede">Every amendment is a commit. Read any provision as it stood on any date, see which amendment wrote each clause, and compare any two dates.</p>
    <ul class="toc">${laws.map((l) => `<li><a href="#/${esc(l.law)}">${esc(l.title)}</a></li>`).join("")}</ul>`;
}

function toc(app, law) {
  const groups = new Map(), titles = {};
  for (const f of law.files) {
    const folder = f.path.includes("/") ? f.path.slice(0, f.path.lastIndexOf("/"))
      : f.path.startsWith("schedule") ? "Schedules" : "";
    if (!groups.has(folder)) groups.set(folder, []);
    if (f.path.endsWith("/README.md")) {  // a folder's heading, e.g. "CHAPTER III — THE CENTRAL INFORMATION COMMISSION"
      titles[folder] = latest(f).split("\n").filter((l) => l.trim()).map((l) => l.replace(/^# /, "")).join(" — ");
      continue;
    }
    groups.get(folder).push(f);
  }
  const touched = {};
  law.files.forEach((f) => f.versions.forEach((v) => (touched[v.commit] ??= []).push(f)));
  const fileLink = (f, extra = {}) => esc(route({ law: law.law, file: id(f), ...extra }));
  app.innerHTML = `<h1>${esc(law.title)}</h1>
    ${[...groups].sort(([a], [b]) => (a === "" ? -1 : b === "" ? 1 : 0)).map(([folder, files]) => `
      ${folder ? `<h2 class="sub">${esc(titles[folder] || folder)}</h2>` : ""}
      <ul class="toc">${files.map((f) => `<li><a href="${fileLink(f)}">${esc(heading(f))}<small>${esc(f.path)}</small></a></li>`).join("")}</ul>`).join("")}
    <h2 class="sub">Amendments, in order of enactment</h2>
    <ol class="timeline">${law.commits.map((c, i) => `<li>
      <time datetime="${esc(c.enacted)}">${fmt(c.enacted)}</time>
      <span><b>${esc(label(c))}</b>. In force ${fmt(c.in_force)}${c.retrospective ? " (retrospective)" : ""}.</span>
      <span class="files">${(touched[i] || []).map((f) => `<a href="${fileLink(f, c.in_force ? { date: c.in_force } : { date: c.enacted, mode: "enacted" })}">${esc(f.path)}</a>`).join("")}</span>
    </li>`).join("")}</ol>`;
}

function shell(law, file, r, body) {
  const first = law.commits[file.versions[0].commit];
  const tab = (view, text, extra) =>
    `<a href="${esc(route({ ...r, file: id(file), view, ...extra }))}"${r.view === view ? ' aria-current="page"' : ""}>${text}</a>`;
  return `<p class="crumb"><a href="#/${esc(law.law)}">${esc(law.title)}</a> / ${esc(file.path)}</p>
    <h1>${esc(heading(file))}</h1>
    <nav class="tabs" aria-label="Views">${tab("read", "Read", { from: null })}${tab("blame", "Blame", { from: null })}${
      tab("diff", "Diff", { from: r.from || first.in_force || first.enacted, date: r.date || TODAY })}</nav>
    ${body}`;
}

function read(app, law, file, r) {
  const date = r.date || TODAY;
  const dates = [...new Set([...file.versions.map((v) => law.commits[v.commit][r.mode]).filter(Boolean), TODAY])].sort();
  const at = Math.max(0, dates.findLastIndex((d) => d <= date));
  const v = versionAt(law, file, date, r.mode);
  const c = v && law.commits[v.commit];
  const status = v?.text
    ? `${c.act === law.commits[0].act ? "Original text" : `Text as amended by <b>${esc(label(c))}</b>`}: enacted ${fmt(c.enacted)}, in force ${fmt(c.in_force)}.`
    : v ? `Omitted by ${esc(label(c))}.`
    : r.mode === "in_force" && versionAt(law, file, date, "enacted")
      ? `Enacted but not in force on ${fmt(date)}. <a href="${esc(route({ ...r, date, mode: "enacted" }))}">Read it as published</a>.`
      : `Not yet enacted on ${fmt(date)}.`;
  const to = (d, mode = r.mode) => route({ ...r, view: "read", from: null, date: d, mode });
  app.innerHTML = shell(law, file, r, `
    <div class="controls">
      <label for="date">As <select id="mode" aria-label="Timeline">
        <option value="in_force">in force</option><option value="enacted"${r.mode === "enacted" ? " selected" : ""}>published</option>
      </select> on</label>
      <input type="date" id="date" value="${esc(date)}" max="${TODAY}">
      <input type="range" id="slider" min="0" max="${dates.length - 1}" value="${at}" aria-label="Amendment dates">
    </div>
    <div class="ticks">${dates.map((d, i) => `<a href="${esc(to(d))}"${i === at && d === date ? ' aria-current="true"' : ""}>${d === TODAY ? "today" : esc(d.slice(0, 4))}</a>`).join("")}</div>
    ${v?.text ? `<article class="law">${v.text.split("\n").map(lineHtml).join("")}</article>` : ""}
    <p class="status">${status}</p>
    <p class="status"><button id="cite">Copy a link to this version</button></p>`);
  $("#date").onchange = (e) => e.target.value && go(to(e.target.value));
  $("#slider").onchange = (e) => go(to(dates[e.target.value]));
  $("#mode").onchange = (e) => go(to(date, e.target.value));
  $("#cite").onclick = (e) => navigator.clipboard.writeText(location.href.split("#")[0] + to(date))
    .then(() => { e.target.textContent = "Copied"; });
}

function blame(app, law, file, r) {
  const text = file.versions.at(-1).text;
  if (!text) {
    app.innerHTML = shell(law, file, r, `<p class="status">Not in the current text.</p>`);
    return;
  }
  const lines = text.split("\n");
  if (lines.at(-1) === "") lines.pop();
  const eras = file.versions.map((v) => v.commit);
  const colour = (i) => `var(--era${(eras.indexOf(i) % 8) + 1})`; // ponytail: 8 colours, cycles beyond that
  const blocks = [];
  lines.forEach((l, n) => {
    const c = file.blame[n];
    if (blocks.at(-1)?.c === c) blocks.at(-1).lines.push(l);
    else blocks.push({ c, lines: [l] });
  });
  app.innerHTML = shell(law, file, r, `
    <p class="status">The current text, as published. Each block shows the amendment that last changed it.</p>
    <div class="blame-wrap">
      <div class="blame">${blocks.map((b) => {
        const c = law.commits[b.c];
        return `<div class="blk" tabindex="0" data-c="${b.c}" style="--c:${colour(b.c)}">
          <div class="gut"><code>${esc(c.sha.slice(0, 7))}</code><span>${esc(label(c))}</span><span>in force ${fmt(c.in_force)}</span></div>
          <div class="lines">${b.lines.map(lineHtml).join("")}</div></div>`;
      }).join("")}</div>
      <aside class="card" id="card" aria-live="polite"></aside>
    </div>`);
  const show = (i) => {
    const c = law.commits[i];
    const card = $("#card");
    card.style.setProperty("--c", colour(i));
    card.innerHTML = `<h3>${esc(label(c))}</h3>
      <dl><dt>Act</dt><dd>${esc(c.act)}</dd>
        <dt>Enacted</dt><dd>${fmt(c.enacted)}</dd>
        <dt>In force</dt><dd>${fmt(c.in_force)}${c.retrospective ? " (retrospective)" : ""}</dd>
        ${c.gazette ? `<dt>Gazette</dt><dd>${esc(c.gazette)}</dd>` : ""}
        <dt>Commit</dt><dd><code>${esc(c.sha.slice(0, 12))}</code></dd></dl>
      ${c.text ? `<p class="amending">${esc(c.text)}</p>` : ""}
      <a href="${esc(c.source)}">Source</a>`;
    app.querySelectorAll(".blk").forEach((el) => el.classList.toggle("on", +el.dataset.c === i));
  };
  app.querySelectorAll(".blk").forEach((el) => {
    el.onmouseenter = el.onfocus = el.onclick = () => show(+el.dataset.c);
  });
  show(eras.at(-1));
}

function diff(app, law, file, r) {
  r = { ...r, date: r.date || TODAY }; // "@1950-01-26.." compares with today
  const at = (d) => versionAt(law, file, d, r.mode)?.text;
  const parts = Diff.diffWords(plain(at(r.from)), plain(at(r.date)));
  app.innerHTML = shell(law, file, r, `
    <div class="controls">
      <label>From <input type="date" id="from" value="${esc(r.from)}" max="${TODAY}"></label>
      <label>to <input type="date" id="to" value="${esc(r.date)}" max="${TODAY}"></label>
      <span>as ${r.mode === "enacted" ? "published" : "in force"}</span>
    </div>
    <article class="law diff">${parts.map((p) => p.added ? `<ins>${esc(p.value)}</ins>` : p.removed ? `<del>${esc(p.value)}</del>` : esc(p.value)).join("") || "No text on either date."}</article>
    <p class="status">Green was added between the two dates and red was removed.</p>`);
  $("#from").onchange = (e) => e.target.value && go(route({ ...r, from: e.target.value }));
  $("#to").onchange = (e) => e.target.value && go(route({ ...r, date: e.target.value }));
}

async function render() {
  const app = $("#app");
  const focused = document.activeElement?.id;
  try {
    const r = parseRoute(location.hash); // throws on a malformed escape such as "%E0"
    if (!r.law) {
      document.title = "git blame the Constitution";
      $("#official").href = "https://www.indiacode.gov.in";
      return await home(app);
    }
    const law = await load(r.law);
    $("#official").href = law.official;
    if (!r.file) {
      document.title = law.title;
      return toc(app, law);
    }
    const file = law.files.find((f) => id(f) === r.file);
    if (!file) throw new Error(`${law.title} has no ${r.file}.`);
    document.title = `${heading(file)} · ${law.title}`;
    ({ read, blame, diff })[r.view](app, law, file, r);
  } catch (e) {
    app.innerHTML = `<p class="error">${esc(e.message)}</p>`;
  } finally {
    if (focused) document.getElementById(focused)?.focus();
  }
}

function go(hash) {
  history.replaceState(null, "", hash);
  render();
}

if (typeof document !== "undefined") {
  addEventListener("hashchange", render);
  render();
}
