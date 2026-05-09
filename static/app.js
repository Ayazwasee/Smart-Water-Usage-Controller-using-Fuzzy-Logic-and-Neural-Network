/* ── CANVAS BACKGROUND ─────────────────────────────────────── */
(function () {
  const canvas = document.getElementById("bg-canvas");
  const ctx = canvas.getContext("2d");

  let W, H, particles;

  const COLORS = ["#00d4b4", "#1a8fff", "#32e8a0", "#ffffff"];

  function resize() {
    W = canvas.width = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }

  function makeParticle() {
    return {
      x: Math.random() * W,
      y: Math.random() * H,
      r: Math.random() * 1.2 + 0.3,
      vx: (Math.random() - 0.5) * 0.22,
      vy: (Math.random() - 0.5) * 0.22,
      color: COLORS[Math.floor(Math.random() * COLORS.length)],
      alpha: Math.random() * 0.45 + 0.05,
    };
  }

  function initParticles() {
    const count = Math.min(Math.floor((W * H) / 9000), 140);
    particles = Array.from({ length: count }, makeParticle);
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);

    // Draw connections
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 120) {
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(0, 212, 180, ${0.07 * (1 - dist / 120)})`;
          ctx.lineWidth = 0.6;
          ctx.stroke();
        }
      }
    }

    // Draw particles
    particles.forEach((p) => {
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = p.color;
      ctx.globalAlpha = p.alpha;
      ctx.fill();
      ctx.globalAlpha = 1;
    });
  }

  function tick() {
    particles.forEach((p) => {
      p.x += p.vx;
      p.y += p.vy;
      if (p.x < 0) p.x = W;
      if (p.x > W) p.x = 0;
      if (p.y < 0) p.y = H;
      if (p.y > H) p.y = 0;
    });
    draw();
    requestAnimationFrame(tick);
  }

  resize();
  initParticles();
  tick();
  window.addEventListener("resize", () => { resize(); initParticles(); });
})();


/* ── MOUSE RADIAL ON CARDS ─────────────────────────────────── */
document.querySelectorAll(".card").forEach((card) => {
  card.addEventListener("mousemove", (e) => {
    const rect = card.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    card.style.setProperty("--mx", x + "%");
    card.style.setProperty("--my", y + "%");
  });
});


/* ── DOM REFS ──────────────────────────────────────────────── */
const usageRange        = document.getElementById("usage");
const availabilityRange = document.getElementById("availability");
const usageValueEl      = document.getElementById("usageValue");
const availabilityValueEl = document.getElementById("availabilityValue");

const overallLabel  = document.getElementById("overallLabel");
const overallSummary = document.getElementById("overallSummary");
const overallHarmony = document.getElementById("overallHarmony");
const resultPanel   = document.getElementById("resultPanel");

const fuzzyLabel      = document.getElementById("fuzzyLabel");
const fuzzyExplanation = document.getElementById("fuzzyExplanation");
const nnLabel         = document.getElementById("nnLabel");
const nnConfidence    = document.getElementById("nnConfidence");
const confBar         = document.getElementById("confBar");
const usageText       = document.getElementById("usageText");
const availabilityText = document.getElementById("availabilityText");

const analyzeBtn   = document.getElementById("analyzeBtn");
const uploadBtn    = document.getElementById("uploadBtn");
const datasetFile  = document.getElementById("datasetFile");
const uploadMsg    = document.getElementById("uploadMsg");

const statSamples  = document.getElementById("statSamples");
const statAccuracy = document.getElementById("statAccuracy");


/* ── SLIDER FILL ───────────────────────────────────────────── */
function updateSliderFill(input) {
  const pct = ((input.value - input.min) / (input.max - input.min)) * 100;
  input.style.setProperty("--pct", pct + "%");
}

function usageDesc(v) {
  v = Number(v);
  if (v < 50) return "Low water usage";
  if (v < 100) return "Moderate water usage";
  return "High water usage";
}

function availabilityDesc(v) {
  v = Number(v);
  if (v < 40) return "Scarce water availability";
  if (v < 70) return "Moderate water availability";
  return "Abundant water availability";
}

function updateSliderLabels() {
  usageValueEl.textContent = usageRange.value;
  availabilityValueEl.textContent = availabilityRange.value;
  usageText.textContent = usageDesc(usageRange.value);
  availabilityText.textContent = availabilityDesc(availabilityRange.value);
  updateSliderFill(usageRange);
  updateSliderFill(availabilityRange);
}


/* ── LABEL CLASS MAPPING ───────────────────────────────────── */
const LBL_CLASSES = ["lbl-critical", "lbl-high", "lbl-balanced", "lbl-moderate", "lbl-normal"];

function applyLabelClass(labelText) {
  overallLabel.classList.remove(...LBL_CLASSES);
  resultPanel.classList.remove(...LBL_CLASSES);

  let cls = "lbl-normal";
  if (labelText.includes("Critical")) cls = "lbl-critical";
  else if (labelText.includes("High"))     cls = "lbl-high";
  else if (labelText.includes("Balanced")) cls = "lbl-balanced";
  else if (labelText.includes("Moderate")) cls = "lbl-moderate";

  overallLabel.classList.add(cls);
  resultPanel.classList.add(cls);
}


/* ── SCROLL ────────────────────────────────────────────────── */
document.querySelectorAll("[data-scroll]").forEach((btn) => {
  btn.addEventListener("click", () => {
    const el = document.getElementById(btn.getAttribute("data-scroll"));
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  });
});


/* ── REVEAL ANIMATION ──────────────────────────────────────── */
const revealObserver = new IntersectionObserver(
  (entries) => entries.forEach((e) => { if (e.isIntersecting) e.target.classList.add("visible"); }),
  { threshold: 0.12 }
);
document.querySelectorAll(".reveal").forEach((el) => revealObserver.observe(el));


/* ── ANALYZE ───────────────────────────────────────────────── */
async function analyze() {
  updateSliderLabels();

  analyzeBtn.classList.add("loading");
  analyzeBtn.disabled = true;

  try {
    const res = await fetch("/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        usage: Number(usageRange.value),
        availability: Number(availabilityRange.value),
      }),
    });

    const data = await res.json();

    overallLabel.textContent  = data.overall_label;
    overallSummary.textContent = data.overall_summary;
    overallHarmony.textContent = data.harmony;

    fuzzyLabel.textContent       = data.fuzzy_label;
    fuzzyExplanation.textContent = data.fuzzy_explanation;

    nnLabel.textContent     = data.nn_label;
    nnConfidence.textContent = `Confidence: ${data.nn_confidence}%`;
    confBar.style.width      = data.nn_confidence + "%";

    applyLabelClass(data.overall_label);

    // Update dataset pills if present
    if (statSamples) statSamples.innerHTML = `<strong>${data.dataset_samples}</strong> samples`;
    if (statAccuracy) statAccuracy.innerHTML = `<strong>${data.dataset_accuracy}</strong> accuracy`;

  } catch (err) {
    overallLabel.textContent  = "Error";
    overallSummary.textContent = "Something went wrong while analyzing the inputs.";
    overallHarmony.textContent = "";
    console.error(err);
  } finally {
    analyzeBtn.classList.remove("loading");
    analyzeBtn.disabled = false;
  }
}


/* ── UPLOAD ────────────────────────────────────────────────── */
async function uploadDataset() {
  if (!datasetFile.files.length) {
    uploadMsg.textContent = "Please choose a CSV file first.";
    return;
  }

  const form = new FormData();
  form.append("dataset", datasetFile.files[0]);
  uploadMsg.textContent = "Training model from your dataset…";

  try {
    const res = await fetch("/upload-dataset", { method: "POST", body: form });
    const data = await res.json();

    if (data.ok) {
      uploadMsg.textContent = `✓ ${data.message}`;
      if (statSamples) statSamples.innerHTML = `<strong>${data.samples}</strong> samples`;
      if (statAccuracy) statAccuracy.innerHTML = `<strong>${data.accuracy}</strong> accuracy`;
      const srcEl = document.getElementById("datasetSourceText");
      if (srcEl) srcEl.textContent = data.source;
      await analyze();
    } else {
      uploadMsg.textContent = `✗ ${data.message}`;
    }
  } catch (err) {
    uploadMsg.textContent = "Upload failed. Please try again.";
    console.error(err);
  }
}


/* ── EVENTS ────────────────────────────────────────────────── */
usageRange.addEventListener("input", updateSliderLabels);
availabilityRange.addEventListener("input", updateSliderLabels);
analyzeBtn.addEventListener("click", analyze);
uploadBtn.addEventListener("click", uploadDataset);

/* init */
updateSliderLabels();
analyze();