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
  input: { x: 0.08, y: 0.16, color: "#f3f7fb", label: "Prompt" },
  inneros_mcp: { x: 0.20, y: 0.51, color: "#d6b46a", label: "InnerOS" },
  local_model: { x: 0.30, y: 0.34, color: "#aeb8c8", label: "Qwen" },
  govern: { x: 0.29, y: 0.67, color: "#8ba7bd", label: "Govern" },
  docker: { x: 0.40, y: 0.73, color: "#c58266", label: "Docker" },
  strands: { x: 0.50, y: 0.50, color: "#7bb7d8", label: "Strands" },
  cognee: { x: 0.70, y: 0.52, color: "#62c8b8", label: "Cognee" },
  brightdata: { x: 0.80, y: 0.31, color: "#66a9d6", label: "Bright Data" },
  bridge: { x: 0.50, y: 0.82, color: "#b7c48c", label: "Bridge" },
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

function stageLinks(stage, tech) {
  const target = tech || stageTech[stage] || "strands";
  const links = [["input", target]];
  if (stage === "remember") links.push(["cognee", "strands"]);
  else if (stage === "inject") links.push(["cognee", "strands"]);
  else if (stage === "observe") links.push(["brightdata", "strands"]);
  else if (stage === "reason" && target === "local_model") links.push(["strands", "local_model"]);
  else if (stage === "reason") links.push(["strands", "cognee"]);
  else if (stage === "audit") links.push(["strands", "cognee"]);
  else if (stage === "govern") links.push(["strands", "govern"]);
  else if (stage === "act") links.push(["govern", "docker"]);
  else if (stage === "learn") links.push(["strands", "cognee"], ["cognee", "bridge"]);
  else if (cortexFlows[target]) links.push(cortexFlows[target]);
  return links.filter(([from, to]) => cortexNodes[from] && cortexNodes[to]);
}

const cortexPieces = {
  local: [
    {
      key: "local_model",
      label: ["QWEN", "VLLM"],
      fill: ["rgba(174, 184, 200, 0.92)", "rgba(88, 104, 126, 0.74)"],
      text: "#f4f7f8",
      points: [[-0.70, -0.60], [-0.12, -0.76], [0.18, -0.38], [0.00, -0.02], [-0.52, 0.04], [-0.82, -0.24]],
      labelAt: [-0.36, -0.33],
    },
    {
      key: "inneros_mcp",
      label: ["INNEROS", "RALPHI"],
      fill: ["rgba(205, 173, 106, 0.94)", "rgba(115, 87, 54, 0.76)"],
      text: "#fff7dc",
      points: [[-0.86, -0.15], [-0.50, 0.02], [0.02, 0.02], [0.12, 0.48], [-0.42, 0.62], [-0.86, 0.36]],
      labelAt: [-0.43, 0.25],
    },
    {
      key: "govern",
      label: ["GOVERN", "POLICY"],
      fill: ["rgba(139, 167, 189, 0.90)", "rgba(48, 67, 86, 0.78)"],
      text: "#ecf6ff",
      points: [[0.03, 0.04], [0.46, 0.10], [0.57, 0.48], [0.18, 0.76], [-0.20, 0.56], [-0.08, 0.18]],
      labelAt: [0.18, 0.42],
    },
    {
      key: "docker",
      label: ["DOCKER", "ACTION"],
      fill: ["rgba(197, 130, 102, 0.92)", "rgba(90, 58, 52, 0.78)"],
      text: "#fff0e8",
      points: [[0.20, -0.06], [0.70, -0.04], [0.83, 0.34], [0.62, 0.64], [0.22, 0.72], [0.52, 0.24]],
      labelAt: [0.53, 0.31],
    },
  ],
  shared: [
    {
      key: "brightdata",
      label: ["BRIGHT", "DATA"],
      fill: ["rgba(102, 169, 214, 0.92)", "rgba(42, 86, 118, 0.76)"],
      text: "#edf8ff",
      points: [[-0.62, -0.62], [-0.05, -0.82], [0.48, -0.54], [0.38, -0.12], [-0.10, 0.04], [-0.70, -0.16]],
      labelAt: [-0.12, -0.36],
    },
    {
      key: "cognee",
      label: ["COGNEE", "GRAPH"],
      fill: ["rgba(98, 200, 184, 0.94)", "rgba(34, 102, 94, 0.78)"],
      text: "#e9fffb",
      points: [[-0.72, -0.10], [-0.08, 0.06], [0.12, 0.54], [-0.30, 0.82], [-0.82, 0.46], [-0.88, 0.10]],
      labelAt: [-0.39, 0.27],
    },
    {
      key: "strands",
      label: ["STRANDS", "ROUTER"],
      fill: ["rgba(123, 183, 216, 0.92)", "rgba(45, 86, 110, 0.78)"],
      text: "#f0fbff",
      points: [[0.00, 0.02], [0.44, -0.08], [0.78, 0.18], [0.66, 0.58], [0.16, 0.70], [0.00, 0.46]],
      labelAt: [0.35, 0.30],
    },
    {
      key: "bridge",
      label: ["SYNC", "BRIDGE"],
      fill: ["rgba(183, 196, 140, 0.90)", "rgba(76, 88, 62, 0.72)"],
      text: "#fbffe9",
      points: [[0.38, -0.44], [0.82, -0.18], [0.88, 0.18], [0.68, 0.48], [0.46, 0.08]],
      labelAt: [0.63, -0.03],
    },
  ],
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
    activeLinks: [],
    completedLinks: [],
    completedTech: new Set(),
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

function spawnLink(fromKey, toKey, color, count = 7) {
  if (!cortex) return;
  for (let i = 0; i < count; i += 1) {
    cortex.particles.push({
      from: fromKey,
      to: toKey,
      t: -i * 0.08,
      speed: 0.011 + Math.random() * 0.009,
      size: 2.2 + Math.random() * 2.4,
      color: color || cortexNodes[toKey]?.color || "#80c7ff",
    });
  }
}

function spawnFlow(tech, count = 7, stage = "") {
  if (!cortex) return;
  stageLinks(stage, tech).forEach(([from, to], index) => {
    spawnLink(from, to, cortexNodes[to]?.color || cortexNodes[tech]?.color || "#80c7ff", Math.max(4, count - index * 2));
  });
}

function brainPath(ctx, cx, cy, rx, ry) {
  ctx.beginPath();
  ctx.moveTo(cx - rx * 0.86, cy + ry * 0.18);
  ctx.bezierCurveTo(cx - rx * 1.00, cy - ry * 0.22, cx - rx * 0.72, cy - ry * 0.58, cx - rx * 0.43, cy - ry * 0.54);
  ctx.bezierCurveTo(cx - rx * 0.30, cy - ry * 0.88, cx + rx * 0.18, cy - ry * 0.88, cx + rx * 0.34, cy - ry * 0.58);
  ctx.bezierCurveTo(cx + rx * 0.74, cy - ry * 0.64, cx + rx * 0.98, cy - ry * 0.28, cx + rx * 0.88, cy + ry * 0.06);
  ctx.bezierCurveTo(cx + rx * 1.05, cy + ry * 0.28, cx + rx * 0.82, cy + ry * 0.72, cx + rx * 0.42, cy + ry * 0.70);
  ctx.bezierCurveTo(cx + rx * 0.18, cy + ry * 0.94, cx - rx * 0.26, cy + ry * 0.86, cx - rx * 0.42, cy + ry * 0.62);
  ctx.bezierCurveTo(cx - rx * 0.76, cy + ry * 0.70, cx - rx * 1.02, cy + ry * 0.48, cx - rx * 0.86, cy + ry * 0.18);
  ctx.closePath();
}

function piecePath(ctx, brain, points, time) {
  const { cx, cy, rx, ry } = brain;
  const scale = (point, index) => {
    const jitter = Math.sin(time * 0.7 + index * 1.9) * 0.01;
    return {
      x: cx + (point[0] + jitter) * rx,
      y: cy + (point[1] + jitter * 0.6) * ry,
    };
  };
  const first = scale(points[0], 0);
  ctx.beginPath();
  ctx.moveTo(first.x, first.y);
  points.forEach((point, index) => {
    const current = scale(point, index);
    const next = scale(points[(index + 1) % points.length], index + 1);
    const midX = (current.x + next.x) / 2;
    const midY = (current.y + next.y) / 2;
    const bend = index % 2 === 0 ? 0.045 : -0.035;
    const controlX = midX + (cy - midY) * bend;
    const controlY = midY + (midX - cx) * bend;
    ctx.quadraticCurveTo(controlX, controlY, next.x, next.y);
  });
  ctx.closePath();
}

function drawBrainShell(ctx, brain, palette, active) {
  const { cx, cy, rx, ry, title } = brain;
  const glow = active ? 34 : 18;
  const fill = ctx.createRadialGradient(cx - rx * 0.28, cy - ry * 0.42, 4, cx, cy, rx * 1.08);
  fill.addColorStop(0, palette.inner);
  fill.addColorStop(0.56, palette.mid);
  fill.addColorStop(1, palette.outer);
  ctx.save();
  ctx.shadowColor = palette.edge;
  ctx.shadowBlur = glow;
  brainPath(ctx, cx, cy, rx, ry);
  ctx.fillStyle = fill;
  ctx.fill();
  ctx.lineWidth = active ? 3.8 : 2.4;
  ctx.strokeStyle = active ? palette.activeEdge : palette.edge;
  ctx.stroke();
  ctx.restore();

  if (cortex.canvas.width > 620) {
    ctx.save();
    ctx.fillStyle = "rgba(235, 243, 246, 0.9)";
    ctx.font = `900 ${Math.max(12, Math.floor(rx * 0.082))}px Inter, system-ui, sans-serif`;
    ctx.textAlign = "center";
    ctx.fillText(title, cx, cy - ry * 0.95);
    ctx.restore();
  }
}

function drawPiece(ctx, brain, piece, active, time) {
  const { cx, cy, rx, ry } = brain;
  ctx.save();
  brainPath(ctx, cx, cy, rx, ry);
  ctx.clip();
  piecePath(ctx, brain, piece.points, time);
  const fill = ctx.createLinearGradient(cx - rx, cy - ry, cx + rx, cy + ry);
  fill.addColorStop(0, piece.fill[0]);
  fill.addColorStop(1, piece.fill[1]);
  ctx.shadowColor = cortexNodes[piece.key]?.color || "#9fb4c0";
  ctx.shadowBlur = active ? 28 : 8;
  ctx.fillStyle = fill;
  ctx.fill();
  ctx.lineWidth = active ? 3.2 : 1.45;
  ctx.strokeStyle = active ? (cortexNodes[piece.key]?.color || "#dfe7eb") : "rgba(226, 238, 242, 0.34)";
  ctx.stroke();

  ctx.globalAlpha = active ? 0.42 : 0.24;
  ctx.lineWidth = 1.1;
  ctx.strokeStyle = "rgba(255, 255, 255, 0.62)";
  for (let i = 0; i < 4; i += 1) {
    const y = cy + (piece.labelAt[1] - 0.22 + i * 0.13) * ry;
    ctx.beginPath();
    ctx.moveTo(cx + (piece.labelAt[0] - 0.26) * rx, y);
    ctx.bezierCurveTo(
      cx + (piece.labelAt[0] - 0.08) * rx,
      y - ry * 0.06,
      cx + (piece.labelAt[0] + 0.10) * rx,
      y + ry * 0.06,
      cx + (piece.labelAt[0] + 0.28) * rx,
      y,
    );
    ctx.stroke();
  }
  ctx.globalAlpha = 1;

  if (cortex.canvas.width > 620) {
    const tx = cx + piece.labelAt[0] * rx;
    const ty = cy + piece.labelAt[1] * ry;
    ctx.shadowBlur = 0;
    ctx.textAlign = "center";
    ctx.fillStyle = piece.text;
    ctx.font = `900 ${Math.max(10, Math.floor(rx * 0.07))}px Inter, system-ui, sans-serif`;
    ctx.fillText(piece.label[0], tx, ty - 3);
    ctx.fillStyle = "rgba(235, 244, 248, 0.78)";
    ctx.font = `800 ${Math.max(8, Math.floor(rx * 0.045))}px Inter, system-ui, sans-serif`;
    ctx.fillText(piece.label[1], tx, ty + Math.max(12, Math.floor(rx * 0.07)));
  }
  ctx.restore();
}

function drawBrainPieces(ctx, brain, pieces, activeKeys, time) {
  drawBrainShell(ctx, brain, brain.palette, activeKeys.some((key) => pieces.some((piece) => piece.key === key)));
  pieces.forEach((piece) => {
    drawPiece(ctx, brain, piece, activeKeys.includes(piece.key), time);
  });
  ctx.save();
  ctx.globalAlpha = 0.38;
  ctx.lineWidth = 1.4;
  ctx.strokeStyle = "rgba(236, 244, 248, 0.22)";
  brainPath(ctx, brain.cx, brain.cy, brain.rx, brain.ry);
  ctx.clip();
  for (let i = -3; i <= 3; i += 1) {
    ctx.beginPath();
    ctx.ellipse(brain.cx + i * brain.rx * 0.15, brain.cy + Math.sin(time + i) * brain.ry * 0.02, brain.rx * 0.32, brain.ry * 0.62, i * 0.18, 0, Math.PI * 2);
    ctx.stroke();
  }
  ctx.restore();
}

function linkKey(fromKey, toKey) {
  return `${fromKey}->${toKey}`;
}

function drawConnection(ctx, fromKey, toKey, activeColor, state) {
  const from = nodePoint(fromKey);
  const to = nodePoint(toKey);
  const mx = (from.x + to.x) / 2;
  const my = (from.y + to.y) / 2 - cortex.canvas.height * 0.08;
  ctx.save();
  const pulse = (performance.now() - cortex.startedAt) / 1000;
  const active = state === "active";
  const complete = state === "complete";
  for (let i = 0; i < 3; i += 1) {
    const offset = (i - 1) * 11;
    ctx.beginPath();
    ctx.moveTo(from.x, from.y + offset);
    ctx.bezierCurveTo(mx, my + offset * 0.2, mx, my + offset * -0.2, to.x, to.y - offset);
    ctx.strokeStyle = active || complete ? activeColor : "rgba(196, 222, 231, 0.13)";
    ctx.globalAlpha = active ? 0.82 - i * 0.12 : complete ? 0.42 - i * 0.07 : 0.22 - i * 0.04;
    ctx.lineWidth = active ? 2.8 : complete ? 1.8 : 1.0;
    ctx.setLineDash(active ? [2, 9] : complete ? [5, 11] : [1, 13]);
    ctx.lineDashOffset = active ? -(pulse * 54 + i * 9) : -(pulse * 12 + i * 4);
    ctx.stroke();
  }
  ctx.restore();
}

function drawNode(ctx, key) {
  const p = nodePoint(key);
  const active = cortex.activeTech === key;
  const complete = cortex.completedTech?.has(key) || cortex.lastTech === key;
  ctx.save();
  ctx.shadowColor = p.color;
  ctx.shadowBlur = active ? 30 : complete ? 16 : 6;
  ctx.beginPath();
  ctx.arc(p.x, p.y, active ? 8 : complete ? 6 : 4.5, 0, Math.PI * 2);
  ctx.fillStyle = p.color;
  ctx.fill();
  ctx.beginPath();
  ctx.arc(p.x, p.y, active ? 20 : complete ? 15 : 11, 0, Math.PI * 2);
  ctx.strokeStyle = active || complete ? p.color : "rgba(210, 237, 246, 0.24)";
  ctx.lineWidth = active ? 2.2 : complete ? 1.4 : 1.0;
  ctx.stroke();
  if (key === "input") {
    ctx.fillStyle = "rgba(236, 244, 248, 0.82)";
    ctx.font = `800 ${Math.max(9, Math.floor(cortex.canvas.width / 130))}px Inter, system-ui, sans-serif`;
    ctx.textAlign = "center";
    ctx.fillText("PROMPT", p.x, p.y - 17);
  }
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

  const drift = h > 430 ? Math.sin(time * 0.75) * 2.5 : 0;
  const localBrain = {
    cx: w * 0.29,
    cy: h * 0.51 + drift,
    rx: w * 0.21,
    ry: h * 0.30,
    title: "INNEROS LOCAL BRAIN",
    palette: {
      inner: "rgba(235, 207, 139, 0.28)",
      mid: "rgba(74, 70, 78, 0.86)",
      outer: "rgba(6, 11, 18, 0.94)",
      edge: "rgba(187, 160, 103, 0.88)",
      activeEdge: "#e0c276",
    },
  };
  const sharedBrain = {
    cx: w * 0.72,
    cy: h * 0.50 - drift,
    rx: w * 0.22,
    ry: h * 0.31,
    title: "COGNEE SHARED MEMORY",
    palette: {
      inner: "rgba(128, 219, 207, 0.26)",
      mid: "rgba(46, 86, 94, 0.84)",
      outer: "rgba(6, 15, 21, 0.95)",
      edge: "rgba(110, 207, 196, 0.86)",
      activeEdge: "#80e0d4",
    },
  };
  const completedKeys = cortex.completedTech ? Array.from(cortex.completedTech) : [];
  const activeKeys = [cortex.activeTech, ...completedKeys.slice(-4)].filter(Boolean);
  drawBrainPieces(ctx, localBrain, cortexPieces.local, activeKeys, time);
  drawBrainPieces(ctx, sharedBrain, cortexPieces.shared, activeKeys, time);

  const activeLinkKeys = new Set((cortex.activeLinks || []).map(([from, to]) => linkKey(from, to)));
  const completeLinkKeys = new Set((cortex.completedLinks || []).map(([from, to]) => linkKey(from, to)));
  const allLinks = new Map();
  Object.entries(cortexFlows).forEach(([tech, flow]) => {
    allLinks.set(linkKey(flow[0], flow[1]), { tech, flow });
  });
  (cortex.activeLinks || []).forEach((flow) => {
    allLinks.set(linkKey(flow[0], flow[1]), { tech: flow[1], flow });
  });
  (cortex.completedLinks || []).forEach((flow) => {
    allLinks.set(linkKey(flow[0], flow[1]), { tech: flow[1], flow });
  });
  allLinks.forEach(({ tech, flow }, key) => {
    const state = activeLinkKeys.has(key) ? "active" : completeLinkKeys.has(key) ? "complete" : "idle";
    drawConnection(ctx, flow[0], flow[1], cortexNodes[tech]?.color || cortexNodes[flow[1]]?.color || "#80c7ff", state);
  });
  Object.keys(cortexNodes).forEach((key) => drawNode(ctx, key));
  drawParticles(ctx);

  if (w > 620) {
    ctx.save();
    ctx.fillStyle = "rgba(236, 244, 248, 0.82)";
    ctx.font = `800 ${Math.max(11, Math.floor(w / 96))}px Inter, system-ui, sans-serif`;
    ctx.textAlign = "center";
    ctx.fillText(cortex.activeStage ? `LIVE STAGE: ${cortex.activeStage.toUpperCase()}` : "REAL ROUTE MAP: MEMORY + WEB + LOCAL ACTION", w * 0.50, h * 0.15);
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
  document.querySelectorAll(".flow-rails path").forEach((item) => item.classList.remove("flowing", "complete-flow"));
  document.querySelectorAll(".pipeline [data-step]").forEach((item) => item.classList.remove("active", "complete"));
  if (cortex) {
    cortex.activeTech = "";
    cortex.activeStage = "";
    cortex.lastTech = "";
    cortex.activeLinks = [];
    cortex.completedLinks = [];
    cortex.completedTech = new Set();
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
  if (flow) flow.classList.add(state === "complete" ? "complete-flow" : "flowing");
  if (step) {
    if (state === "complete") step.classList.add("complete");
    else step.classList.add("active");
  }
  if (cortex) {
    cortex.activeTech = tech;
    cortex.activeStage = stage;
    cortex.lastTech = tech;
    const links = stageLinks(stage, tech);
    cortex.activeLinks = state === "complete" ? [] : links;
    if (state === "complete") {
      cortex.completedTech.add(tech);
      links.forEach((link) => cortex.completedLinks.push(link));
      cortex.completedLinks = cortex.completedLinks.slice(-10);
    }
    if (state === "active") spawnFlow(tech, stage === "reason" ? 12 : 8, stage);
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
    cortex.activeLinks = stageLinks("input", "strands");
    spawnFlow("strands", 9, "input");
  }
}

function renderResult(data) {
  const webHits = data.web_hits || [];
  const memoryHits = data.memory_hits || [];
  const availableMemoryHits = memoryHits.filter((item) => !(item.metadata || {}).unavailable);
  const unavailableMemory = memoryHits.some((item) => (item.metadata || {}).unavailable);
  const actions = data.actions || [];
  const replay = webHits.some((item) => item.metadata && item.metadata.verified_replay);
  const route = data.route || {};
  const compact = (value, max = 180) => {
    const text = String(value || "").replace(/\s+/g, " ").trim();
    return text.length > max ? text.slice(0, max - 1) + "..." : text;
  };
  const memoryEvidence = availableMemoryHits.slice(0, 3).map((item, index) => {
    return `${index + 1}. ${compact(item.summary, 220)}`;
  });
  const webEvidence = webHits.slice(0, 5).map((item, index) => {
    const meta = item.metadata || {};
    const title = meta.title || compact(item.summary, 120);
    const url = meta.url ? ` — ${meta.url}` : "";
    return `${index + 1}. ${compact(title, 140)}${url}`;
  });
  const action = actions[actions.length - 1] || null;
  const actionLine = action
    ? `Docker Sandbox: ${action.status || "unknown"}${action.artifact ? ` · ${action.artifact}` : ""}`
    : "Docker Sandbox: not requested. Use Think + Act to create a bounded sandbox artifact/proof.";
  const degraded = route.degraded_sources || [];
  const healthLines = degraded.length
    ? degraded.map((item) => `- ${item.source}: ${item.message || item.reason}`).join("\n")
    : "- No degraded providers reported.";
  const modelLine = route.fallback_active
    ? `Qwen / Strands: degraded (${route.fallback_reason}); deterministic evidence summary used.`
    : `Qwen / vLLM: ${route.final_answer_model || "local model"} synthesized the final answer.`;
  const whoAnswered = [
    `Route: ${String(route.route_policy || "unknown").toUpperCase()} · ${route.routing_reason || "Selected route."}`,
    `Strands Router: selected tools and ordered the flow.`,
    unavailableMemory
      ? `Cognee Memory: temporarily unavailable for recall; the run continued.`
      : `Cognee Memory: ${availableMemoryHits.length ? `${availableMemoryHits.length} recalled item(s) from ${route.evidence_refs?.cognee_dataset || "dataset"}.` : "not used or no matching memory."}`,
    `Bright Data: ${webHits.length ? `${webHits.length} ${replay ? "verified replay" : "live"} result(s).` : "not used or no public results."}`,
    modelLine,
    actionLine,
  ].join("\n");
  const routeLines = [
    `ROUTE ${String(route.route_mode || activeRouteMode).toUpperCase()} · ${String(route.route_policy || "unknown").toUpperCase()}`,
    `USED ${(route.sources_used || []).join(", ") || "none"} · SKIPPED ${(route.sources_not_used || []).join(", ") || "none"}`,
    `STAGES ${(route.stages_executed || []).join(" -> ") || "not reported"}`
  ].join("\n");
  const evidenceLines = [
    "SOURCE EVIDENCE",
    memoryEvidence.length ? `COGNEE\n${memoryEvidence.join("\n")}` : `COGNEE\n${unavailableMemory ? "Temporarily unavailable for this run." : "No memory evidence returned."}`,
    webEvidence.length ? `BRIGHT DATA\n${webEvidence.join("\n")}` : "BRIGHT DATA\nNo web evidence returned.",
  ].join("\n\n");
  const finalAnswer = String(data.answer || "Completed without textual answer.")
    .replace(/\n?\[Strands fallback:[^\]]+\]\s*$/g, "")
    .trim();
  const actionSection = action
    ? `\n\nACTION RESULT\n${actionLine}${action.stderr ? `\nDetail: ${compact(action.stderr, 260)}` : ""}`
    : "";
  $("answer").textContent = `RUN SUMMARY\n${whoAnswered}\n\nDEGRADED PROVIDERS\n${healthLines}\n\n${routeLines}\n\n${evidenceLines}\n\nFINAL ANSWER\n${finalAnswer}${actionSection}`;
  $("metrics").innerHTML = `
    <span>MEM ${availableMemoryHits.length}${unavailableMemory ? " DEGRADED" : ""}</span>
    <span>WEB ${webHits.length}${replay ? " REPLAY" : " LIVE"}</span>
    <span>ACTIONS ${actions.length}</span>
  `;
  $("evidenceSummary").textContent = degraded.length
    ? "Trace completed with provider degradations clearly labeled."
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
