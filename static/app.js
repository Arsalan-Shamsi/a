// Fetches the dashboard payload and renders it. No frameworks, no CDN — just
// enough plain JavaScript to turn the JSON from /api/dashboard into the page.

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

// Parse an ISO date by its parts so the displayed day never shifts by timezone.
function fmtDate(iso) {
  if (!iso) return "—";
  const [y, m, d] = iso.split("T")[0].split("-").map(Number);
  return `${MONTHS[m - 1]} ${d}, ${y}`;
}

function trendView(trend, label) {
  if (!trend) return { arrow: "", cls: "stable", label: "" };
  const arrow = trend === "rising" ? "↑" : trend === "falling" ? "↓" : "→";
  return { arrow, cls: trend, label: label || trend };
}

function levelClass(category) {
  if (!category) return "muted";
  return "level-pill level-" + category.toLowerCase().replace(/\s+/g, "");
}

// Build a small inline-SVG sparkline from the series points.
function sparkline(points, trend) {
  const w = 240, h = 44, pad = 4;
  const vals = points.map(p => p.value).filter(v => v !== null && v !== undefined);
  if (vals.length < 2) return "";
  const min = Math.min(...vals), max = Math.max(...vals);
  const span = max - min || 1;
  const n = points.length;
  const coords = points.map((p, i) => {
    const x = pad + (i * (w - 2 * pad)) / (n - 1);
    const v = (p.value === null || p.value === undefined) ? min : p.value;
    const y = h - pad - ((v - min) / span) * (h - 2 * pad);
    return [x, y];
  });
  const path = coords.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
  const stroke = getComputedStyle(document.documentElement)
    .getPropertyValue("--" + (trend || "stable")).trim() || "#7a8896";
  const [lx, ly] = coords[coords.length - 1];
  return `<svg class="spark" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}"
            role="img" aria-label="Trend over the last ${n} weeks">
            <polyline fill="none" stroke="${stroke}" stroke-width="2"
              stroke-linejoin="round" stroke-linecap="round" points="${path}" />
            <circle cx="${lx.toFixed(1)}" cy="${ly.toFixed(1)}" r="3" fill="${stroke}" />
          </svg>`;
}

function signalHtml(s) {
  const t = trendView(s.trend, s.trend_label);
  const prov = s.provenance;
  const tag = prov.is_sample
    ? '<span class="tag-sample">sample</span>'
    : '<span class="tag-live">live</span>';
  const valueStr = s.current_value === null || s.current_value === undefined
    ? "—" : s.current_value;
  const pill = s.level_category
    ? `<span class="chip ${levelClass(s.level_category)}">${s.level_category}</span>`
    : "";
  return `
    <div class="signal">
      <div class="signal-top">
        <span class="signal-label" title="${s.description || ""}">${s.signal_label}</span>
        <span class="signal-source"><a href="${prov.source_url}" target="_blank" rel="noopener">${prov.source_short} ↗</a></span>
      </div>
      <div class="signal-main">
        <span class="value">${valueStr}</span>
        <span class="unit">${s.unit}</span>
        ${pill}
        <span class="trend ${t.cls}">${t.arrow} ${t.label}</span>
      </div>
      ${sparkline(s.points, s.trend)}
      <div class="through">${prov.geography} · through ${fmtDate(s.current_date)} · ${tag}</div>
    </div>`;
}

function cardHtml(block) {
  // Use the % of ER visits series (our primary "spine") as the headline trend.
  const spine = block.series.find(s => s.signal === "ed_visits_pct");
  const t = spine ? trendView(spine.trend, spine.trend_label) : trendView(null);
  const chip = t.label
    ? `<span class="chip ${t.cls === "rising" ? "level-pill level-high" : t.cls === "falling" ? "level-pill level-minimal" : "muted"}">${t.arrow} ${t.label}</span>`
    : "";
  const signals = block.series.map(signalHtml).join("");
  return `
    <article class="card">
      <div class="card-head"><h2>${block.virus}</h2>${chip}</div>
      ${signals || '<p class="through">No data available.</p>'}
    </article>`;
}

function sourcesHtml(sources) {
  const item = (p) => `
    <div class="source-item ${p.role === "reference" ? "role-reference" : ""}">
      <a href="${p.source_url}" target="_blank" rel="noopener">${p.source_name} ↗</a>
      <div class="source-meta">
        ${p.geography} · ${p.role === "reference" ? "reference link" : "data source"}
        ${p.data_through ? " · through " + fmtDate(p.data_through) : ""}
        · ${p.access}
      </div>
    </div>`;
  return `<h2>Sources &amp; methods</h2>
    <p class="source-meta">Every number above comes from one of these official, public sources.</p>
    ${sources.map(item).join("")}`;
}

function render(d) {
  document.getElementById("status").classList.add("hidden");

  document.getElementById("meta").textContent =
    `${d.location} · generated ${fmtDate(d.generated_at)}`;

  const banner = document.getElementById("sample-banner");
  if (d.is_sample) {
    banner.textContent = "⚠ Showing built-in SAMPLE data so the app runs offline. " +
      "Set ILLNESS_LIVE=1 to pull live data from CDC.";
    banner.classList.remove("hidden");
  }

  document.getElementById("cards").innerHTML = d.viruses.map(cardHtml).join("");
  document.getElementById("sources").innerHTML = sourcesHtml(d.sources);
  document.getElementById("disclaimers").innerHTML =
    "<h2>Good to know</h2><ul>" +
    d.disclaimers.map(x => `<li>${x}</li>`).join("") + "</ul>";
}

fetch("/api/dashboard")
  .then(r => { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
  .then(render)
  .catch(err => {
    document.getElementById("status").textContent =
      "Could not load the dashboard data: " + err.message;
  });
