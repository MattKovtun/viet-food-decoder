"use strict";

/* ---------- constants (mirror src/models.py Taxonomy) ---------- */

const CATS = [
  ["noodle-soup", "Noodle soup"], ["noodle-dry", "Noodle dry"], ["rice", "Rice"],
  ["roll", "Roll"], ["cake", "Cake"], ["main", "Main"], ["snack", "Snack"],
  ["sweet", "Sweet"], ["drink", "Drink"],
];

/* label / matcher pairs for the spice segmented control */
const SPICE_OPTS = [
  ["any", "any", () => true],
  ["0",   "0",   v => v === 0],
  ["le1", "≤1",  v => v <= 1],
  ["ge2", "≥2",  v => v >= 2],
];

function spiceNote(d) {
  const base = [
    "not spicy as served — the chili on the table is yours to add",
    "gently warm as served",
    "noticeably spicy as served",
    "properly hot — this dish is meant to be spicy",
  ][d.spice];
  return d.spice_varies
    ? base + "; heat varies a lot from stall to stall — check before ordering"
    : base;
}

const ING_GROUPS = [
  ["Bases", ["rice-noodle","wheat-noodle","glass-noodle","tapioca-noodle","rice",
             "broken-rice","sticky-rice","rice-paper","rice-cracker","baguette"]],
  ["Proteins", ["pork","beef","veal","chicken","duck","fish","fish-cake","shrimp",
                "crab","clam","snail","squid","frog","eel","offal","blood","balut",
                "egg","quail-egg","tofu"]],
  ["Plants & extras", ["jackfruit","papaya","green-banana","banana","corn","avocado",
                       "mung-bean","peanut","sesame","coconut","herbs","lemongrass",
                       "turmeric","ginger","dill","chili","tomato","pineapple",
                       "carrot","bamboo-shoot","tamarind","bitter-melon","yam","soybean",
                       "plum","durian","lotus-seed","longan","birds-nest","cassava",
                       "peach","artichoke"]],
  ["Sweet & drink", ["condensed-milk","yogurt","coffee","tea","sugarcane","jelly"]],
  ["Defining sauces", ["fish-sauce","fermented-fish","shrimp-paste","pate"]],
];

/* ---------- text helpers (mirror src/utils.py TextNormalizer) ---------- */

function norm(s) {
  return s.replace(/[đĐ]/g, "d")
    .normalize("NFD").replace(/\p{M}+/gu, "")
    .toLowerCase().replace(/[^a-z0-9 ]+/g, " ")
    .replace(/\s+/g, " ").trim();
}

function esc(s) {
  return String(s).replace(/[&<>"']/g, c =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function tagLabel(tag) { return tag.replace(/-/g, " "); }

/* Commons original URL -> resized thumb URL (photos only; leaves thumb URLs alone).
   Wikimedia only serves fixed widths to anonymous clients (https://w.wiki/GHai):
   120, 250, 330, 500, 960, 1280 — px must be one of these. */
function thumbUrl(url, px) {
  const m = url.match(/^(https:\/\/upload\.wikimedia\.org\/wikipedia\/commons)\/([0-9a-f])\/([0-9a-f]{2})\/([^/]+)$/);
  if (!m) return url;
  return `${m[1]}/thumb/${m[2]}/${m[3]}/${m[4]}/${px}px-${m[4]}`;
}

function imgSearchUrl(dish) {
  const q = dish.img_query || dish.name + " vietnam food";
  return "https://www.google.com/search?tbm=isch&q=" + encodeURIComponent(q);
}

/* history is markdown-lite: blank-line paragraphs + [text](https://url) links */
function historyHtml(text) {
  return text.split(/\n\n+/).map(p => {
    const h = esc(p.trim()).replace(
      /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
      '<a href="$2" target="_blank" rel="noopener">$1</a>'
    );
    return `<p>${h}</p>`;
  }).join("");
}

function readMinutes(text) {
  return Math.max(1, Math.round(text.split(/\s+/).length / 200));
}

/* ---------- pronunciation audio ---------- */

let player = null;

function say(id, voice) {
  const d = dishes.find(x => x.id === id);
  if (!d) return;
  const clip = voice === "m" ? (d.audio_m || d.audio) : d.audio;
  if (clip) {
    if (!player) player = new Audio();
    player.src = clip;
    player.play().catch(() => speak(d));
  } else {
    speak(d);
  }
}

/* fallback: browser speech synthesis with a Vietnamese voice if available */
function speak(d) {
  if (!("speechSynthesis" in window)) return;
  const u = new SpeechSynthesisUtterance(d.name.split("/")[0].trim());
  u.lang = "vi-VN";
  const v = speechSynthesis.getVoices().find(v => v.lang.startsWith("vi"));
  if (v) u.voice = v;
  speechSynthesis.cancel();
  speechSynthesis.speak(u);
}

/* advance an <img> through its data-fallbacks list; hide when exhausted */
function imgErr(el) {
  const rest = (el.dataset.fallbacks || "").split("|").filter(Boolean);
  if (!rest.length) { el.style.display = "none"; return; }
  el.src = rest.shift();
  el.dataset.fallbacks = rest.join("|");
}

/* ---------- state ---------- */

const state = {
  q: "",
  cat: null,            // null = all
  inc: new Set(),       // required ingredient tags
  exc: new Set(),       // excluded ingredient tags
  spice: "any",         // SPICE_OPTS key
};

let dishes = [];
let searchIndex = new Map();   // id -> normalized haystack

const $ = id => document.getElementById(id);

/* ---------- filtering ---------- */

function activeAdvancedCount() {
  return state.inc.size + state.exc.size + (state.spice !== "any" ? 1 : 0);
}

function matches(d) {
  if (state.cat && d.cat !== state.cat) return false;
  for (const t of state.inc) if (!d.ingredients.includes(t)) return false;
  for (const t of state.exc) if (d.ingredients.includes(t)) return false;
  if (!SPICE_OPTS.find(o => o[0] === state.spice)[2](d.spice)) return false;
  if (state.q) {
    const hay = searchIndex.get(d.id);
    for (const tok of state.q.split(" ")) if (!hay.includes(tok)) return false;
  }
  return true;
}

/* ---------- rendering ---------- */

function partsHtml(d) {
  return d.parts.map(([text, kind]) => `<span class="k-${kind}">${esc(text)}</span>`).join(" ");
}

function spiceBadge(d) {
  if (d.spice_varies) return `<span class="badge flav">🌶 varies</span>`;
  if (d.spice === 0) return "";
  return `<span class="badge flav">${"🌶".repeat(d.spice)}</span>`;
}

function cardHtml(d) {
  const aka = (d.aka || []).length
    ? `<div class="aka">also: ${d.aka.map(esc).join(" · ")}</div>` : "";
  const ings = d.ingredients.map(t => `<span class="badge ing">${esc(tagLabel(t))}</span>`).join("");
  return `<div class="card" data-id="${esc(d.id)}">
    <div class="name">${d.img_verified ? '<span class="vstar" title="verified photo">★</span> ' : ""}${partsHtml(d)}<span class="pron">${esc(d.pron)}</span><button class="say" data-say="${esc(d.id)}" aria-label="hear pronunciation">🔊</button></div>
    <div class="lit">${esc(d.lit)}</div>
    ${aka}<div class="desc">${esc(d.desc)}</div>
    <div class="meta">${spiceBadge(d)}${
      (d.variants || []).length ? `<span class="badge">${d.variants.length} ways to order</span>` : ""
    }${ings}</div>
  </div>`;
}

function render() {
  const hits = dishes.filter(matches);
  $("cards").innerHTML = hits.map(cardHtml).join("");
  $("empty").style.display = hits.length ? "none" : "block";
  $("count").textContent = `${hits.length} of ${dishes.length} dishes`;

  // header chip states
  document.querySelectorAll("#catRow .chip").forEach(el =>
    el.classList.toggle("on", el.dataset.cat === String(state.cat)));
  $("mildChip").classList.toggle("on", state.spice === "le1");
  const n = activeAdvancedCount();
  $("filtersBtn").textContent = n ? `Filters (${n})` : "Filters";
  $("filtersBtn").classList.toggle("active", n > 0);

  // drawer states
  document.querySelectorAll("#ingGroups .tag").forEach(el => {
    el.classList.toggle("inc", state.inc.has(el.dataset.tag));
    el.classList.toggle("exc", state.exc.has(el.dataset.tag));
  });
  document.querySelectorAll("#spiceRow .seg button").forEach(el =>
    el.classList.toggle("on", state.spice === el.dataset.opt));
}

/* ---------- detail overlay ---------- */

function overlayHtml(d) {
  const cells = [1, 2, 3].map(i => `<span class="cell${i <= d.spice ? " fill" : ""}"></span>`).join("");
  const spiceRow = `
    <div class="fbar"><span class="fname">🌶 Spice</span><span class="cells">${cells}</span><span class="fval">${d.spice}/3${d.spice_varies ? " · varies" : ""}</span></div>
    <p class="spice-note">${esc(spiceNote(d))}</p>`;

  const ings = d.ingredients.map(t => `<span class="badge">${esc(tagLabel(t))}</span>`).join(" ");

  const srcs = [
    d.img_local,
    d.img && thumbUrl(d.img, 960),
    d.img,
  ].filter(Boolean);
  const img = srcs.length
    ? `<div class="ov-img-wrap">
         <img class="ov-img" src="${esc(srcs[0])}" alt="${esc(d.name)}" loading="lazy"
              data-fallbacks="${esc(srcs.slice(1).join("|"))}" onerror="imgErr(this)">
       </div>`
    : `<a class="ov-search" href="${esc(imgSearchUrl(d))}" target="_blank" rel="noopener">🔍 search images for “${esc(d.name)}”</a>`;

  return `
    ${img}
    <div class="ov-name">${d.img_verified ? '<span class="vstar" title="verified photo">★</span> ' : ""}${partsHtml(d)}</div>
    <div class="ov-pron">${esc(d.pron)}
      <button class="say say-lg" data-say="${esc(d.id)}" aria-label="hear pronunciation, voice 1">🔊 Voice 1</button>
      ${d.audio_m ? `<button class="say say-lg" data-say="${esc(d.id)}" data-voice="m" aria-label="hear pronunciation, voice 2">🔊 Voice 2</button>` : ""}
    </div>
    ${(d.aka || []).length ? `<div class="aka">also: ${d.aka.map(esc).join(" · ")}</div>` : ""}
    <div class="ov-lit">“${esc(d.lit)}”</div>
    <div class="ov-desc">${esc(d.desc)}</div>
    <div class="ov-sec"><h4>Where & how</h4>
      ${d.central ? '<span class="badge">central VN specialty</span>' : ""}
      <span class="badge">${esc(d.region)}</span>
      <span class="badge">${esc(d.cat)}</span>
      <span class="badge">eats as: ${esc(d.form)}</span>
    </div>
    ${(d.variants || []).length ? `<div class="ov-sec"><h4>Variants — how to order</h4>${
      d.variants.map(v => {
        const lvl = v.spice ?? d.spice;   // per-variant override, else the dish's heat
        const chilis = lvl > 0 ? "🌶".repeat(lvl) : "no 🌶";
        return `<div class="vrow"><span class="vname">${esc(v.name)}<span class="vspice">${chilis}</span></span><span class="vnote">${esc(v.note)}</span></div>`;
      }).join("")}</div>` : ""}
    <div class="ov-sec"><h4>Spice</h4>${spiceRow}</div>
    <div class="ov-sec"><h4>Ingredients</h4><div class="tags">${ings}</div></div>
    ${d.history ? `<details class="ov-hist"><summary>History & impact<span class="read-time">${readMinutes(d.history)} min read</span></summary><div class="hist-body">${historyHtml(d.history)}</div></details>` : ""}
    <div class="ov-sec"><h4>Sources</h4><span class="badge">${d.srcs.map(esc).join("</span> <span class=\"badge\">")}</span></div>`;
}

function openDish(id) {
  const d = dishes.find(x => x.id === id);
  if (!d) return;
  $("ovBody").innerHTML = overlayHtml(d);
  $("overlay").classList.add("open");
  document.body.style.overflow = "hidden";
  history.pushState({ dish: id }, "", "#" + id);
}

function closeOverlay(viaHistory) {
  if (!$("overlay").classList.contains("open")) return;
  $("overlay").classList.remove("open");
  document.body.style.overflow = "";
  if (!viaHistory && history.state && history.state.dish) history.back();
}

/* ---------- UI construction ---------- */

function buildHeader() {
  $("catRow").innerHTML =
    `<button class="chip" data-cat="null">All</button>` +
    CATS.map(([k, label]) => {
      const n = dishes.filter(d => d.cat === k).length;
      return `<button class="chip" data-cat="${k}">${label}<span class="n">${n}</span></button>`;
    }).join("");
}

function buildDrawer() {
  const used = new Set(dishes.flatMap(d => d.ingredients));
  $("ingGroups").innerHTML = ING_GROUPS.map(([title, tags]) => {
    const present = tags.filter(t => used.has(t));
    if (!present.length) return "";
    const chips = present.map(t => `<span class="tag" data-tag="${t}">${tagLabel(t)}</span>`).join("");
    return `<h3>${title}</h3><div class="tags">${chips}</div>`;
  }).join("");

  $("spiceRow").innerHTML = (() => {
    const btns = SPICE_OPTS.map(([opt, text]) =>
      `<button data-opt="${opt}">${text}</button>`).join("");
    return `<div class="frow"><span class="fname">🌶 Spice</span><div class="seg">${btns}</div></div>`;
  })();
}

function bindEvents() {
  let qTimer;
  $("q").addEventListener("input", e => {
    clearTimeout(qTimer);
    qTimer = setTimeout(() => { state.q = norm(e.target.value); render(); }, 120);
  });

  $("catRow").addEventListener("click", e => {
    const chip = e.target.closest(".chip");
    if (!chip) return;
    const c = chip.dataset.cat === "null" ? null : chip.dataset.cat;
    state.cat = (state.cat === c) ? null : c;
    render();
  });

  $("mildChip").addEventListener("click", () => {
    state.spice = state.spice === "le1" ? "any" : "le1"; render();
  });
  $("filtersBtn").addEventListener("click", () => $("drawer").classList.toggle("open"));
  $("applyBtn").addEventListener("click", () => $("drawer").classList.remove("open"));
  $("resetBtn").addEventListener("click", () => {
    state.cat = null; state.q = ""; $("q").value = "";
    state.inc.clear(); state.exc.clear();
    state.spice = "any";
    render();
  });

  $("ingGroups").addEventListener("click", e => {
    const t = e.target.closest(".tag");
    if (!t) return;
    const tag = t.dataset.tag;
    if (state.inc.has(tag)) { state.inc.delete(tag); state.exc.add(tag); }
    else if (state.exc.has(tag)) { state.exc.delete(tag); }
    else { state.inc.add(tag); }
    render();
  });

  $("spiceRow").addEventListener("click", e => {
    const b = e.target.closest("button");
    if (!b) return;
    state.spice = b.dataset.opt;
    render();
  });

  $("cards").addEventListener("click", e => {
    const btn = e.target.closest(".say");
    if (btn) { say(btn.dataset.say, btn.dataset.voice); return; }
    const card = e.target.closest(".card");
    if (card) openDish(card.dataset.id);
  });

  $("ovBody").addEventListener("click", e => {
    const btn = e.target.closest(".say");
    if (btn) say(btn.dataset.say, btn.dataset.voice);
  });

  $("ovClose").addEventListener("click", () => closeOverlay(false));
  window.addEventListener("popstate", () => closeOverlay(true));
  window.addEventListener("keydown", e => { if (e.key === "Escape") closeOverlay(false); });
}

/* ---------- boot ---------- */

async function boot() {
  let data;
  try {
    const res = await fetch("data/dishes.json");
    if (!res.ok) throw new Error(res.status);
    data = await res.json();
  } catch (err) {
    $("error").style.display = "block";
    return;
  }
  dishes = data.dishes;
  searchIndex = new Map(dishes.map(d => [d.id, norm(
    [d.name, (d.aka || []).join(" "),
     (d.variants || []).map(v => v.name + " " + v.note).join(" "),
     d.id, d.pron, d.lit, d.desc, d.region, d.cat,
     d.ingredients.join(" ")].join(" ")
  )]));
  buildHeader();
  buildDrawer();
  bindEvents();
  render();
  // deep link: index.html#mi-quang opens the dish directly
  const hash = location.hash.slice(1);
  if (hash && dishes.some(d => d.id === hash)) {
    history.replaceState(null, "", location.pathname);
    openDish(hash);
  }
}

boot();
