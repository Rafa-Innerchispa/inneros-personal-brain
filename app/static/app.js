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

function setRegionState(key, state) {
  const region = $("region-" + key);
  if (!region) return;
  region.classList.remove("ready", "pending", "blocked", "active", "complete", "error");
  region.classList.add(stateClass(state));
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
  document.querySelectorAll(".brain-segment,.bridge-segment").forEach((item) => {
    item.classList.remove("active", "complete", "error");
  });
  document.querySelectorAll(".flow-rails path").forEach((item) => item.classList.remove("flowing"));
  document.querySelectorAll(".pipeline [data-step]").forEach((item) => item.classList.remove("active"));
}

function activateStage(stage, technology, state, message) {
  const tech = technology || stageTech[stage] || "strands";
  const meta = techMeta[tech] || { name: tech, role: "" };
  const region = $("region-" + tech) || $("region-" + stage);
  const flow = $(meta.flow || "flow-strands");
  const step = document.querySelector(`[data-step="${stage}"]`);

  document.querySelectorAll(".brain-segment,.bridge-segment").forEach((item) => {
    item.classList.remove("active", "error");
  });
  document.querySelectorAll(".flow-rails path").forEach((item) => item.classList.remove("flowing"));
  document.querySelectorAll(".pipeline [data-step]").forEach((item) => item.classList.remove("active"));

  if (region) {
    region.classList.add(state === "error" ? "error" : state === "complete" ? "complete" : "active");
  }
  if (flow) flow.classList.add("flowing");
  if (step) step.classList.add("active");

  $("cognitiveState").textContent = "COGNITIVE STATE · " + String(stage).toUpperCase();
  $("modePill").textContent = state === "active" ? "PROCESSING" : "STAGE COMPLETE";
  addEvent(meta.name, state, message || meta.role);
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
  $("eventStream").innerHTML = "";
  $("answer").textContent = "Live cognitive trace running...";
  $("metrics").innerHTML = "<span>MEM ...</span><span>WEB ...</span><span>ACTIONS ...</span>";
  $("evidenceSummary").textContent = "Backend stream is active.";
}

function renderResult(data) {
  const webHits = data.web_hits || [];
  const replay = webHits.some((item) => item.metadata && item.metadata.verified_replay);
  const route = data.route || {};
  const routeLines = [
    `ROUTE ${String(route.route_mode || activeRouteMode).toUpperCase()} · ${String(route.route_policy || "unknown").toUpperCase()}`,
    `ORCHESTRATOR ${route.orchestrator || "unknown"} · FINAL MODEL ${route.final_answer_model || "unknown"}`,
    `USED ${(route.sources_used || []).join(", ") || "none"} · SKIPPED ${(route.sources_not_used || []).join(", ") || "none"}`,
    route.fallback_active ? `FALLBACK ACTIVE ${route.fallback_reason || ""}` : "FALLBACK inactive"
  ].join("\n");
  $("answer").textContent = `${routeLines}\n\n${data.answer || "Completed without textual answer."}`;
  $("metrics").innerHTML = `
    <span>MEM ${(data.memory_hits || []).length}</span>
    <span>WEB ${webHits.length}${replay ? " REPLAY" : " LIVE"}</span>
    <span>ACTIONS ${(data.actions || []).length}</span>
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
      activateStage(data.stage, data.technology, data.state, data.message);
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

function proofText(result) {
  const evidence = (result.evidence || []).map((item) => {
    if (typeof item === "string") return "- " + item;
    return "- " + Object.entries(item).map(([key, value]) => `${key}: ${value}`).join(" · ");
  }).join("\n");
  return `${result.mode} · ${result.status}\n\n${result.summary || ""}\n\n${evidence}`;
}

async function runProof(mode) {
  resetRunUi();
  addEvent("Judge Mode", "active", `${mode.toUpperCase()} proof requested`);
  const button = document.querySelector(`[data-proof="${mode}"]`);
  if (button) button.disabled = true;

  try {
    const response = await fetch(`/api/proof/${mode}`, { method: "POST" });
    const result = await response.json();
    const stage = mode === "share" ? "learn" : mode;
    const technology = mode === "observe" ? "brightdata" : mode === "govern" ? "govern" : "cognee";
    activateStage(stage, technology, result.status === "PASS" ? "complete" : "active", result.summary);
    $("answer").textContent = proofText(result);
    $("metrics").innerHTML = `<span>${escapeHtml(result.mode)}</span><span>${escapeHtml(result.status)}</span>`;
    $("evidenceSummary").textContent = "Judge Mode uses backend proof endpoints.";
  } catch (error) {
    addEvent("Judge Mode", "error", String(error));
    $("answer").textContent = "Proof mode failed: " + String(error);
  } finally {
    if (button) button.disabled = false;
    setTimeout(clearAnimation, 1600);
    loadStatus();
  }
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
document.querySelectorAll("[data-prompt]").forEach((button) => {
  button.addEventListener("click", () => {
    $("prompt").value = button.dataset.prompt;
  });
});
document.querySelectorAll("[data-proof]").forEach((button) => {
  button.addEventListener("click", () => runProof(button.dataset.proof));
});

loadStatus();
setInterval(loadStatus, 15000);
