const techMeta = {
  cognee: { name: "Cognee", role: "Shared graph memory", flow: "flow-cognee" },
  brightdata: { name: "Bright Data", role: "Live public-web perception", flow: "flow-brightdata" },
  strands: { name: "AWS Strands", role: "Reasoning orchestration", flow: "flow-strands" },
  local_model: { name: "Qwen / vLLM", role: "Local or distributed inference", flow: "flow-local_model" },
  docker: { name: "Docker Sandbox", role: "Governed execution", flow: "flow-docker" },
  govern: { name: "Policy Gate", role: "Deterministic action control", flow: "flow-govern" },
  inneros_mcp: { name: "InnerOS / Ralphi", role: "External nervous system", flow: "flow-strands" },
  bridge: { name: "Curated Memory Bridge", role: "Safe seed with provenance", flow: "flow-learn" }
};

const fabricOrder = [
  "personal_brain",
  "cognee_mcp",
  "strands",
  "brightdata",
  "codex",
  "cursor",
  "antigravity",
  "ralphi",
  "gmail"
];

const surfaceLabels = {
  cognee_mcp: "Cognee MCP"
};

const stageTech = {
  input: "strands",
  remember: "cognee",
  inject: "cognee",
  observe: "brightdata",
  reason: "strands",
  audit: "strands",
  govern: "govern",
  act: "docker",
  learn: "cognee"
};

let statuses = {};
let seq = 0;
let activeRouteMode = "auto";
let stageQueue = [];
let stageTimer = null;
let cortex = null;

const cortexNodes = {
  inneros_mcp: { x: 0.19, y: 0.52, color: "#e7c268", label: "InnerOS" },
  local_model: { x: 0.31, y: 0.32, color: "#9c8cff", label: "Qwen" },
  govern: { x: 0.30, y: 0.70, color: "#e7c268", label: "Govern" },
  docker: { x: 0.43, y: 0.76, color: "#e98973", label: "Docker" },
  strands: { x: 0.50, y: 0.49, color: "#80c7ff", label: "Strands" },
  cognee: { x: 0.69, y: 0.52, color: "#67e6d2", label: "Cognee" },
  brightdata: { x: 0.84, y: 0.27, color: "#57c7ff", label: "Bright Data" },
  bridge: { x: 0.50, y: 0.88, color: "#8de6a5", label: "Bridge" },
};

const cortexFlows = {
  strands: ["strands", "cognee"],
  cognee: ["cognee", "strands"],
  brightdata: ["brightdata", "strands"],
  local_model: ["strands", "local_model"],
  govern: ["strands", "govern"],
  docker: ["govern", "docker"],
  bridge: ["cognee", "bridge"],
  inneros_mcp: ["inneros_mcp", "strands"],
};

function $(id) {
  return document.getElementById(id);
}

function escapeHtml(value) {
  const div = document.createElement("div");
  div.textContent = value ?? "";
  return div.innerHTML;
}

function normalizeState(state) {
  return String(state || "unknown").replaceAll("_", " ");
}

function stateClass(state) {
  if (["ready", "configured", "connected"].includes(state)) return "ready";
  if (["pending_auth", "partial", "on_demand"].includes(state)) return "pending";
  if (["blocked", "error", "missing"].includes(state)) return "blocked";
  return "optional";
}

function setupCortex() {
  const canvas = $("cortexCanvas");
  if (!canvas) return;
  cortex = {
    canvas,
    ctx: canvas.getContext("2d"),
    dpr: Math.max(1, Math.min(window.devicePixelRatio || 1, 2)),
    activeTech: "",
    activeStage: "",
    lastTech: "",
    particles: [],
    startedAt: performance.now(),
  };
  resizeCortex();
  window.addEventListener("resize", resizeCortex);
  requestAnimationFrame(drawCortex);
}

function resizeCortex() {
  if (!cortex) return;
  const rect = cortex.canvas.getBoundingClientRect();
  cortex.dpr = Math.max(1, Math.min(window.devicePixelRatio || 1, 2));
  cortex.canvas.width = Math.max(1, Math.floor(rect.width * cortex.dpr));
  cortex.canvas.height = Math.max(1, Math.floor(rect.height * cortex.dpr));
}

function nodePoint(key) {
  const n = cortexNodes[key] || cortexNodes.strands;
  return {
    x: n.x * cortex.canvas.width,
    y: n.y * cortex.canvas.height,
    color: n.color,
  };
}

function spawnFlow(tech, count = 7) {
  if (!cortex) return;
  const flow = cortexFlows[tech] || cortexFlows.strands;
  for (let i = 0; i < count; i += 1) {
    cortex.particles.push({
      from: flow[0],
      to: flow[1],
      t: -i * 0.08,
      speed: 0.011 + Math.random() * 0.009,
      size: 2.2 + Math.random() * 2.4,
      color: cortexNodes[tech]?.color || "#80c7ff",
    });
  }
}

function drawBlob(ctx, cx, cy, rx, ry, palette, active, label) {
  ctx.save();
  const wobble = (performance.now() - cortex.startedAt) / 1000;
  const glow = active ? 0.95 : 0.34;
  const shell = ctx.createRadialGradient(cx - rx * 0.35, cy - ry * 0.45, 8, cx, cy, rx * 1.14);
  shell.addColorStop(0, palette.hot);
  shell.addColorStop(0.38, palette.mid);
  shell.addColorStop(1, palette.dark);
  ctx.shadowColor = palette.hot;
  ctx.shadowBlur = active ? 34 : 15;
  ctx.beginPath();
  for (let i = 0; i <= 96; i += 1) {
    const a = (Math.PI * 2 * i) / 96;
    const folded = 1 + Math.sin(a * 5 + wobble * 0.9) * 0.035 + Math.cos(a * 3 - wobble * 0.45) * 0.04;
    const x = cx + Math.cos(a) * rx * folded;
    const y = cy + Math.sin(a) * ry * (1 + Math.cos(a * 4) * 0.035);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.closePath();
  ctx.fillStyle = shell;
  ctx.globalAlpha = 0.9;
  ctx.fill();
  ctx.globalAlpha = 1;
  ctx.lineWidth = active ? 3.8 : 2.4;
  ctx.strokeStyle = palette.edge;
  ctx.stroke();

  ctx.shadowBlur = 0;
  ctx.globalAlpha = 0.46 + glow * 0.28;
  for (let i = -2; i <= 2; i += 1) {
    ctx.beginPath();
    ctx.ellipse(cx + i * rx * 0.18, cy + Math.sin(i + wobble) * 8, rx * (0.42 - Math.abs(i) * 0.035), ry * 0.72, i * 0.22, 0, Math.PI * 2);
    ctx.strokeStyle = palette.fold;
    ctx.lineWidth = 1.5;
    ctx.stroke();
  }
  ctx.globalAlpha = 1;
  if (cortex.canvas.width > 620) {
    ctx.fillStyle = "#dcecf1";
    ctx.font = `900 ${Math.max(12, Math.floor(rx * 0.08))}px Inter, system-ui, sans-serif`;
    ctx.textAlign = "center";
    ctx.fillText(label, cx, cy - ry - 22);
  }
  ctx.restore();
}

function drawConnection(ctx, fromKey, toKey, activeColor, active) {
  const from = nodePoint(fromKey);
  const to = nodePoint(toKey);
  const mx = (from.x + to.x) / 2;
  const my = (from.y + to.y) / 2 - cortex.canvas.height * 0.08;
  ctx.save();
  ctx.beginPath();
  ctx.moveTo(from.x, from.y);
  ctx.quadraticCurveTo(mx, my, to.x, to.y);
  ctx.strokeStyle = active ? activeColor : "rgba(196, 222, 231, 0.18)";
  ctx.lineWidth = active ? 3.2 : 1.3;
  ctx.setLineDash(active ? [10, 10] : [5, 11]);
  ctx.lineDashOffset = -((performance.now() - cortex.startedAt) / 24);
  ctx.stroke();
  ctx.restore();
}

function drawNode(ctx, key) {
  const p = nodePoint(key);
  const active = cortex.activeTech === key || cortex.lastTech === key;
  ctx.save();
  ctx.shadowColor = p.color;
  ctx.shadowBlur = active ? 24 : 10;
  ctx.beginPath();
  ctx.arc(p.x, p.y, active ? 12 : 8, 0, Math.PI * 2);
  ctx.fillStyle = p.color;
  ctx.fill();
  ctx.beginPath();
  ctx.arc(p.x, p.y, active ? 23 : 16, 0, Math.PI * 2);
  ctx.strokeStyle = active ? p.color : "rgba(210, 237, 246, 0.28)";
  ctx.lineWidth = active ? 2.5 : 1.2;
  ctx.stroke();
  ctx.restore();
}

function drawParticles(ctx) {
  cortex.particles = cortex.particles.filter((particle) => particle.t < 1.08);
  for (const particle of cortex.particles) {
    particle.t += particle.speed;
    if (particle.t < 0) continue;
    const from = nodePoint(particle.from);
    const to = nodePoint(particle.to);
    const t = Math.min(1, particle.t);
    const curve = Math.sin(t * Math.PI);
    const x = from.x + (to.x - from.x) * t;
    const y = from.y + (to.y - from.y) * t - curve * cortex.canvas.height * 0.08;
    ctx.save();
    ctx.shadowColor = particle.color;
    ctx.shadowBlur = 18;
    ctx.beginPath();
    ctx.arc(x, y, particle.size, 0, Math.PI * 2);
    ctx.fillStyle = particle.color;
    ctx.fill();
    ctx.restore();
  }
}

function drawCortex() {
  if (!cortex) return;
  const ctx = cortex.ctx;
  const w = cortex.canvas.width;
  const h = cortex.canvas.height;
  const time = (performance.now() - cortex.startedAt) / 1000;

  ctx.clearRect(0, 0, w, h);
  const bg = ctx.createLinearGradient(0, 0, w, h);
  bg.addColorStop(0, "#061018");
  bg.addColorStop(0.54, "#081723");
  bg.addColorStop(1, "#050c12");
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, w, h);

  ctx.save();
  ctx.globalAlpha = 0.18;
  ctx.strokeStyle = "#33576b";
  ctx.lineWidth = 1;
  const grid = Math.max(42, w / 24);
  for (let x = 0; x < w; x += grid) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, h);
    ctx.stroke();
  }
  for (let y = 0; y < h; y += grid) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(w, y);
    ctx.stroke();
  }
  ctx.restore();

  const localActive = ["inneros_mcp", "local_model", "govern", "docker"].includes(cortex.activeTech);
  const sharedActive = ["cognee", "brightdata", "bridge"].includes(cortex.activeTech);
  drawBlob(ctx, w * 0.30, h * 0.50 + Math.sin(time * 0.9) * 3, w * 0.18, h * 0.27, {
    hot: "rgba(255, 210, 106, 0.92)",
    mid: "rgba(255, 143, 111, 0.54)",
    dark: "rgba(19, 17, 28, 0.86)",
    edge: localActive ? "#ffd26a" : "rgba(231, 194, 104, 0.78)",
    fold: "rgba(255, 235, 177, 0.48)",
  }, localActive, "INNEROS LOCAL BRAIN");
  drawBlob(ctx, w * 0.72, h * 0.49 + Math.cos(time * 0.8) * 3, w * 0.20, h * 0.29, {
    hot: "rgba(103, 230, 210, 0.94)",
    mid: "rgba(68, 227, 189, 0.46)",
    dark: "rgba(8, 26, 37, 0.9)",
    edge: sharedActive ? "#67e6d2" : "rgba(103, 230, 210, 0.78)",
    fold: "rgba(194, 255, 245, 0.45)",
  }, sharedActive, "COGNEE SHARED MEMORY");

  const activeFlow = cortexFlows[cortex.activeTech] || [];
  Object.entries(cortexFlows).forEach(([tech, flow]) => {
    drawConnection(ctx, flow[0], flow[1], cortexNodes[tech]?.color || "#80c7ff", activeFlow[0] === flow[0] && activeFlow[1] === flow[1]);
  });
  Object.keys(cortexNodes).forEach((key) => drawNode(ctx, key));
  drawParticles(ctx);

  if (w > 620) {
    ctx.save();
    ctx.fillStyle = "rgba(236, 244, 248, 0.82)";
    ctx.font = `800 ${Math.max(11, Math.floor(w / 96))}px Inter, system-ui, sans-serif`;
    ctx.textAlign = "center";
    ctx.fillText(cortex.activeStage ? `LIVE STAGE: ${cortex.activeStage.toUpperCase()}` : "WAITING FOR LIVE ROUTE", w * 0.50, h * 0.16);
    ctx.restore();
  }
  requestAnimationFrame(drawCortex);
}

function setRegionState(key, state) {
  document.querySelectorAll(`#region-${key}, [data-tech="${key}"]`).forEach((region) => {
    region.classList.remove("ready", "pending", "blocked", "active", "complete", "error");
    region.classList.add(stateClass(state));
  });
}

function renderFabric(fabric) {
  if (!fabric) return;
  $("fabricDataset").textContent = fabric.dataset || "dataset";

  const surfaces = fabric.surfaces || [];
  const byKey = Object.fromEntries(surfaces.map((item) => [item.key, item]));
  const ordered = fabricOrder.map((key) => byKey[key]).filter(Boolean);

  $("fabricMatrix").innerHTML = ordered.map((surface) => {
    const cls = stateClass(surface.state);
    const required = surface.required_for_core ? "core" : "optional";
    return `
      <button class="fabric-row ${cls}" data-detail="${escapeHtml(surface.key)}">
        <span>${escapeHtml(surfaceLabels[surface.key] || surface.label)}</span>
        <b>${escapeHtml(normalizeState(surface.state))}</b>
        <small>${escapeHtml(surface.transport)} · ${required}</small>
      </button>
    `;
  }).join("");
}

function renderRoutes(fabric) {
  const routes = fabric?.route_status || [];
  $("routeMatrix").innerHTML = routes.map((route) => {
    const cls = stateClass(route.state);
    return `
      <button class="route-row ${cls}" data-detail="${escapeHtml(route.key)}">
        <span>${escapeHtml(route.label)}</span>
        <b>${escapeHtml(normalizeState(route.state))}</b>
        <small>${escapeHtml(route.route_class)} · ${escapeHtml(route.evidence)}</small>
      </button>
    `;
  }).join("");
}

function renderStatus(status) {
  statuses = status || {};
  const fabric = statuses.memory_fabric || {};
  const surfaces = Object.fromEntries((fabric.surfaces || []).map((item) => [item.key, item]));

  const cogneeState = surfaces.cognee_mcp?.state || statuses.cognee?.state;
  const brightDataState = surfaces.brightdata?.state || statuses.brightdata?.state;
  const strandsState = surfaces.strands?.state || statuses.strands?.state;
  const qwenState = statuses.local_model?.state || "on_demand";
  const dockerState = statuses.docker?.state || "unknown";
  const ralphiState = surfaces.ralphi?.state || statuses.inneros_mcp?.state;

  setRegionState("cognee", cogneeState);
  setRegionState("brightdata", brightDataState);
  setRegionState("strands", strandsState);
  setRegionState("local_model", qwenState);
  setRegionState("docker", dockerState);
  setRegionState("inneros_mcp", ralphiState);
  setRegionState("bridge", "ready");

  const coreReady = ["ready", "configured", "connected"].includes(cogneeState)
    && ["ready", "configured", "connected"].includes(brightDataState)
    && ["ready", "configured", "connected"].includes(strandsState);

  $("coreBadge").textContent = coreReady ? "CORE READY" : "CHECK SYSTEMS";
  $("coreBadge").className = coreReady ? "ready" : "";
  $("systemSummary").textContent = coreReady ? "Cognee + Bright Data + Strands ready" : "partial readiness, see routes";

  renderFabric(fabric);
  renderRoutes(fabric);
}

async function loadStatus() {
  try {
    const response = await fetch("/api/status", { cache: "no-store" });
    renderStatus(await response.json());
  } catch (error) {
    $("systemSummary").textContent = "status endpoint unavailable";
  }
}

function clearAnimation() {
  document.querySelectorAll(".brain-segment,.bridge-segment,.cortex-chip").forEach((item) => {
    item.classList.remove("active", "complete", "error");
  });
  document.querySelectorAll(".flow-rails path").forEach((item) => item.classList.remove("flowing"));
  document.querySelectorAll(".pipeline [data-step]").forEach((item) => item.classList.remove("active"));
  if (cortex) {
    cortex.activeTech = "";
    cortex.activeStage = "";
    cortex.lastTech = "";
  }
}

function activateStage(stage, technology, state, message) {
  const tech = technology || stageTech[stage] || "strands";
  const meta = techMeta[tech] || { name: tech, role: "" };
  const regions = document.querySelectorAll(`#region-${tech}, #region-${stage}, [data-tech="${tech}"]`);
  const flow = $(meta.flow || "flow-strands");
  const step = document.querySelector(`[data-step="${stage}"]`);

  document.querySelectorAll(".brain-segment,.bridge-segment,.cortex-chip").forEach((item) => {
    item.classList.remove("active", "error");
  });
  document.querySelectorAll(".flow-rails path").forEach((item) => item.classList.remove("flowing"));
  document.querySelectorAll(".pipeline [data-step]").forEach((item) => item.classList.remove("active"));

  regions.forEach((region) => {
    region.classList.add(state === "error" ? "error" : state === "complete" ? "complete" : "active");
  });
  if (flow) flow.classList.add("flowing");
  if (step) step.classList.add("active");
  if (cortex) {
    cortex.activeTech = tech;
    cortex.activeStage = stage;
    cortex.lastTech = tech;
    if (state === "active") spawnFlow(tech, stage === "reason" ? 11 : 7);
  }

  $("cognitiveState").textContent = "COGNITIVE STATE · " + String(stage).toUpperCase();
  $("modePill").textContent = state === "active" ? "PROCESSING" : "STAGE COMPLETE";
  addEvent(meta.name, state, message || meta.role);
}

function enqueueStage(event) {
  stageQueue.push(event);
  if (stageTimer) return;
  const pump = () => {
    const next = stageQueue.shift();
    if (next) {
      activateStage(next.stage, next.technology, next.state, next.message);
      stageTimer = setTimeout(pump, next.state === "active" ? 720 : 520);
      return;
    }
    stageTimer = null;
  };
  pump();
}

function addEvent(title, state, message) {
  seq += 1;
  const article = document.createElement("article");
  article.className = "event " + (state || "active");
  article.innerHTML = `<span>${String(seq).padStart(2, "0")}</span><div><b>${escapeHtml(title)}</b><small>${escapeHtml(message)}</small></div>`;
  $("eventStream").prepend(article);
  while ($("eventStream").children.length > 12) {
    $("eventStream").lastElementChild.remove();
  }
}

function resetRunUi() {
  seq = 0;
  stageQueue = [];
  if (stageTimer) {
    clearTimeout(stageTimer);
    stageTimer = null;
  }
  $("eventStream").innerHTML = "";
  $("answer").textContent = "Live cognitive trace running...";
  $("metrics").innerHTML = "<span>MEM ...</span><span>WEB ...</span><span>ACTIONS ...</span>";
  $("evidenceSummary").textContent = "Backend stream is active.";
  if (cortex) {
    cortex.activeTech = "strands";
    cortex.activeStage = "input";
    spawnFlow("strands", 9);
  }
}

function renderResult(data) {
  const webHits = data.web_hits || [];
  const memoryHits = data.memory_hits || [];
  const actions = data.actions || [];
  const replay = webHits.some((item) => item.metadata && item.metadata.verified_replay);
  const route = data.route || {};
  const compact = (value, max = 180) => {
    const text = String(value || "").replace(/\s+/g, " ").trim();
    return text.length > max ? text.slice(0, max - 1) + "..." : text;
  };
  const memoryEvidence = memoryHits.slice(0, 3).map((item, index) => {
    return `${index + 1}. ${compact(item.summary, 220)}`;
  });
  const webEvidence = webHits.slice(0, 5).map((item, index) => {
    const meta = item.metadata || {};
    const title = meta.title || compact(item.summary, 120);
    const url = meta.url ? ` — ${meta.url}` : "";
    return `${index + 1}. ${compact(title, 140)}${url}`;
  });
  const whoAnswered = [
    `STRANDS ROUTER: ${route.routing_reason || "Selected the route and ordered the tools."}`,
    `COGNEE MEMORY: ${memoryHits.length ? `${memoryHits.length} recalled item(s) from ${route.evidence_refs?.cognee_dataset || "dataset"}.` : "not used for this route."}`,
    `BRIGHT DATA: ${webHits.length ? `${webHits.length} ${replay ? "verified replay" : "live"} result(s).` : "not used for this route."}`,
    `RALPHI IA / INNEROS: local sovereign fabric is the runtime and coordination layer for this demo.`,
    `QWEN / VLLM: ${route.final_answer_model || "local model"} synthesized the final answer.`,
    `DOCKER: ${actions.length ? `${actions.length} action(s), latest ${actions[actions.length - 1]?.status || "unknown"}.` : "no action requested."}`,
    route.fallback_active ? `FALLBACK: ACTIVE ${route.fallback_reason || ""}` : "FALLBACK: inactive"
  ].join("\n");
  const routeLines = [
    `ROUTE ${String(route.route_mode || activeRouteMode).toUpperCase()} · ${String(route.route_policy || "unknown").toUpperCase()}`,
    `USED ${(route.sources_used || []).join(", ") || "none"} · SKIPPED ${(route.sources_not_used || []).join(", ") || "none"}`,
    `STAGES ${(route.stages_executed || []).join(" -> ") || "not reported"}`
  ].join("\n");
  const evidenceLines = [
    "SOURCE EVIDENCE",
    memoryEvidence.length ? `COGNEE\n${memoryEvidence.join("\n")}` : "COGNEE\nNo memory evidence returned.",
    webEvidence.length ? `BRIGHT DATA\n${webEvidence.join("\n")}` : "BRIGHT DATA\nNo web evidence returned.",
  ].join("\n\n");
  $("answer").textContent = `${whoAnswered}\n\n${routeLines}\n\n${evidenceLines}\n\nFINAL ANSWER\n${data.answer || "Completed without textual answer."}`;
  $("metrics").innerHTML = `
    <span>MEM ${memoryHits.length}</span>
    <span>WEB ${webHits.length}${replay ? " REPLAY" : " LIVE"}</span>
    <span>ACTIONS ${actions.length}</span>
  `;
  $("evidenceSummary").textContent = replay
    ? "Bright Data fallback is clearly labeled as verified replay."
    : "Trace completed with live backend evidence.";
}

async function runBrain(act) {
  const prompt = $("prompt").value.trim();
  if (!prompt) return;

  $("thinkBtn").disabled = true;
  $("actBtn").disabled = true;
  resetRunUi();

  const stream = new EventSource(`/api/brain/stream?prompt=${encodeURIComponent(prompt)}&act=${act ? "true" : "false"}&route_mode=${encodeURIComponent(activeRouteMode)}`);
  stream.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === "stage") {
      enqueueStage(data);
    } else if (data.type === "result") {
      renderResult(data);
    } else if (data.type === "error") {
      addEvent("Backend", "error", data.message);
      $("answer").textContent = "ERROR: " + data.message;
    } else if (data.type === "done") {
      stream.close();
      $("thinkBtn").disabled = false;
      $("actBtn").disabled = false;
      setTimeout(clearAnimation, 1600);
      loadStatus();
    }
  };
  stream.onerror = () => {
    stream.close();
    $("thinkBtn").disabled = false;
    $("actBtn").disabled = false;
    addEvent("Stream", "error", "Connection interrupted");
    $("answer").textContent = "Stream interrupted. Retry once after checking status.";
  };
}

$("thinkBtn").addEventListener("click", () => runBrain(false));
$("actBtn").addEventListener("click", () => runBrain(true));
document.querySelectorAll("[data-route]").forEach((button) => {
  button.addEventListener("click", () => {
    activeRouteMode = button.dataset.route || "auto";
    document.querySelectorAll("[data-route]").forEach((item) => item.classList.toggle("selected", item === button));
    $("modePill").textContent = "ROUTE " + activeRouteMode.replace("_", " ").toUpperCase();
  });
});

setupCortex();
loadStatus();
setInterval(loadStatus, 15000);
