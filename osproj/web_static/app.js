const state = {
  autoplay: false,
  timer: null,
  logEntries: [],
};

const cpuValue = document.getElementById("cpuValue");
const memoryValue = document.getElementById("memoryValue");
const cycleValue = document.getElementById("cycleValue");
const runningValue = document.getElementById("runningValue");
const processTableBody = document.getElementById("processTableBody");
const scheduleList = document.getElementById("scheduleList");
const actionLog = document.getElementById("actionLog");
const swapCount = document.getElementById("swapCount");
const completedCount = document.getElementById("completedCount");
const startPauseBtn = document.getElementById("startPauseBtn");
const stepBtn = document.getElementById("stepBtn");
const resetBtn = document.getElementById("resetBtn");
const historyCanvas = document.getElementById("historyCanvas");

async function fetchJSON(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

function setAutoplay(enabled) {
  state.autoplay = enabled;
  startPauseBtn.textContent = enabled ? "Pause" : "Start";
  if (enabled) {
    tick();
  } else if (state.timer) {
    clearTimeout(state.timer);
    state.timer = null;
  }
}

async function tick() {
  if (!state.autoplay) {
    return;
  }
  const data = await fetchJSON("/api/step", { method: "POST" });
  render(data, true);
  if (state.autoplay && data.hasWork && data.cycleNumber < data.maxCycles) {
    state.timer = setTimeout(tick, 700);
  } else {
    setAutoplay(false);
  }
}

function render(snapshot, prependLog = false) {
  cpuValue.textContent = `${snapshot.cpuUsage.toFixed(1)}%`;
  memoryValue.textContent = `${snapshot.memoryUsage.toFixed(1)}%`;
  cycleValue.textContent = String(snapshot.cycleNumber);
  runningValue.textContent = snapshot.runningProcessPid === null ? "Idle" : `PID ${snapshot.runningProcessPid}`;

  processTableBody.innerHTML = "";
  snapshot.activeProcesses.forEach((process) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${process.pid}</td>
      <td>${process.burstTime}</td>
      <td>${process.priority}</td>
      <td>${process.memory} MB</td>
      <td><span class="state-pill ${process.state}">${process.state}</span></td>
    `;
    processTableBody.appendChild(row);
  });

  scheduleList.innerHTML = "";
  if (snapshot.schedulingOrder.length === 0) {
    const item = document.createElement("li");
    item.textContent = "No active processes remain in the queue.";
    scheduleList.appendChild(item);
  } else {
    snapshot.schedulingOrder.forEach((process, index) => {
      const item = document.createElement("li");
      item.textContent = `${index + 1}. PID ${process.pid} | Priority ${process.priority} | Burst ${process.burstTime}`;
      scheduleList.appendChild(item);
    });
  }

  if (prependLog) {
    state.logEntries.unshift({
      cycle: snapshot.cycleNumber,
      actions: snapshot.adaptiveActions,
    });
    state.logEntries = state.logEntries.slice(0, 12);
  } else if (state.logEntries.length === 0) {
    state.logEntries = [{ cycle: snapshot.cycleNumber, actions: snapshot.adaptiveActions }];
  }

  actionLog.innerHTML = "";
  state.logEntries.forEach((entry) => {
    const wrapper = document.createElement("div");
    wrapper.className = "log-item";
    wrapper.innerHTML = `
      <strong>Cycle ${entry.cycle}</strong>
      <div>${entry.actions.join(" | ")}</div>
    `;
    actionLog.appendChild(wrapper);
  });

  swapCount.textContent = `Swapped: ${snapshot.swappedProcesses.length}`;
  completedCount.textContent = `Completed: ${snapshot.completedProcesses}`;
  drawHistory(snapshot.cpuHistory, snapshot.memoryHistory);
}

function drawHistory(cpuHistory, memoryHistory) {
  const ctx = historyCanvas.getContext("2d");
  const width = historyCanvas.width;
  const height = historyCanvas.height;

  ctx.clearRect(0, 0, width, height);

  const left = 40;
  const top = 18;
  const right = width - 16;
  const bottom = height - 30;

  ctx.strokeStyle = "rgba(154, 178, 226, 0.18)";
  ctx.lineWidth = 1;
  ctx.strokeRect(left, top, right - left, bottom - top);

  for (let level = 0; level <= 100; level += 25) {
    const y = bottom - ((bottom - top) * level) / 100;
    ctx.setLineDash([4, 6]);
    ctx.beginPath();
    ctx.moveTo(left, y);
    ctx.lineTo(right, y);
    ctx.strokeStyle = "rgba(154, 178, 226, 0.16)";
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = "#90a6d8";
    ctx.font = '11px "Avenir Next", sans-serif';
    ctx.fillText(String(level), 8, y + 4);
  }

  drawLine(cpuHistory, "#52c7ff", left, top, right, bottom, ctx);
  drawLine(memoryHistory, "#6ce4a0", left, top, right, bottom, ctx);

  ctx.fillStyle = "#52c7ff";
  ctx.fillText("CPU", right - 68, 18);
  ctx.fillStyle = "#6ce4a0";
  ctx.fillText("MEM", right - 28, 18);
}

function drawLine(history, color, left, top, right, bottom, ctx) {
  if (!history.length) {
    return;
  }

  ctx.beginPath();
  ctx.lineWidth = 3;
  ctx.strokeStyle = color;

  history.forEach((value, index) => {
    const x = history.length === 1
      ? (left + right) / 2
      : left + ((right - left) * index) / (history.length - 1);
    const y = bottom - ((bottom - top) * value) / 100;
    if (index === 0) {
      ctx.moveTo(x, y);
    } else {
      ctx.lineTo(x, y);
    }
  });

  ctx.stroke();
}

startPauseBtn.addEventListener("click", () => {
  setAutoplay(!state.autoplay);
});

stepBtn.addEventListener("click", async () => {
  setAutoplay(false);
  const data = await fetchJSON("/api/step", { method: "POST" });
  render(data, true);
});

resetBtn.addEventListener("click", async () => {
  setAutoplay(false);
  state.logEntries = [];
  const data = await fetchJSON("/api/reset", { method: "POST" });
  render(data, false);
});

fetchJSON("/api/status").then((data) => render(data, false));
