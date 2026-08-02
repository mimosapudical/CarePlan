const form = document.getElementById("care-plan-form");
const statusEl = document.getElementById("status");
const outputEl = document.getElementById("output");
const submitBtn = document.getElementById("submit-btn");
const downloadLink = document.getElementById("download-link");
const searchInput = document.getElementById("search-input");
const searchBtn = document.getElementById("search-btn");
const searchStatus = document.getElementById("search-status");
const searchResults = document.getElementById("search-results");

const POLL_INTERVAL_MS = 3000;
let pollTimerId = null;

function formDataToObject(formElement) {
  const formData = new FormData(formElement);
  return Object.fromEntries(formData.entries());
}

function stopPolling() {
  if (pollTimerId !== null) {
    clearInterval(pollTimerId);
    pollTimerId = null;
  }
}

function renderCarePlan(data) {
  const carePlan = data.care_plan || data.content;
  if (data.status !== "completed" || !carePlan) {
    outputEl.textContent = data.error ? `failed: ${data.error}` : "care plan not ready";
    downloadLink.style.display = "none";
    return;
  }

  const sections = [
    ["Problem list", carePlan.problem_list],
    ["Goals", carePlan.goals],
    ["Pharmacist interventions", carePlan.pharmacist_interventions],
    ["Monitoring plan", carePlan.monitoring_plan],
  ];

  outputEl.textContent = sections
    .map(([title, items]) => `${title}\n${(items || []).map((item) => `- ${item}`).join("\n")}`)
    .join("\n\n");
  downloadLink.href = `/api/care-plans/${data.id}/download/`;
  downloadLink.style.display = "inline-block";
}

async function pollCarePlanStatus(careplanId) {
  try {
    const response = await fetch(`/api/care-plans/${careplanId}/status/`);
    const data = await response.json();

    if (!response.ok) {
      stopPolling();
      statusEl.textContent = "failed";
      outputEl.textContent = data.error || "failed to fetch status";
      downloadLink.style.display = "none";
      submitBtn.disabled = false;
      return;
    }

    statusEl.textContent = `status: ${data.status}`;

    if (data.status === "completed") {
      stopPolling();
      renderCarePlan(data);
      submitBtn.disabled = false;
      return;
    }

    if (data.status === "failed") {
      stopPolling();
      outputEl.textContent = data.error ? `failed: ${data.error}` : "care plan generation failed";
      downloadLink.style.display = "none";
      submitBtn.disabled = false;
      return;
    }

    outputEl.textContent = `Generating care plan...\nCare Plan ID: ${careplanId}\nCurrent status: ${data.status}`;
  } catch (error) {
    stopPolling();
    statusEl.textContent = "failed";
    outputEl.textContent = String(error);
    downloadLink.style.display = "none";
    submitBtn.disabled = false;
  }
}

function startPolling(careplanId) {
  stopPolling();
  statusEl.textContent = "status: pending";
  outputEl.textContent = `Generating care plan...\nCare Plan ID: ${careplanId}\nCurrent status: pending`;
  downloadLink.style.display = "none";

  // Immediate first check, then every 3 seconds
  pollCarePlanStatus(careplanId);
  pollTimerId = setInterval(() => pollCarePlanStatus(careplanId), POLL_INTERVAL_MS);
}

function renderSearchResults(results) {
  searchResults.innerHTML = results
    .map((item) => {
      const patient = [item.payload.patient_first_name, item.payload.patient_last_name].filter(Boolean).join(" ");
      const download = item.status === "completed"
        ? `<a class="mini-link" href="/api/care-plans/${item.id}/download/">Download</a>`
        : "";
      return `
        <article class="result-card">
          <div class="result-head">
            <strong>${item.id}</strong>
            <span>${item.status}</span>
          </div>
          <div class="result-meta">${patient} | ${item.payload.patient_mrn} | ${item.payload.medication_name}</div>
          <div class="result-actions">
            <a class="mini-link" href="/api/care-plans/${item.id}/">View</a>
            ${download}
          </div>
        </article>
      `;
    })
    .join("");
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  stopPolling();
  submitBtn.disabled = true;
  statusEl.textContent = "submitting...";
  outputEl.textContent = "Submitting, please wait...";
  downloadLink.style.display = "none";

  try {
    const response = await fetch("/api/care-plans/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(formDataToObject(form)),
    });
    const data = await response.json();
    if (!response.ok) {
      statusEl.textContent = `failed: ${data.status || response.status}`;
      outputEl.textContent = data.error || "request failed";
      submitBtn.disabled = false;
      return;
    }

    startPolling(data.careplan_id);
  } catch (error) {
    statusEl.textContent = "failed";
    outputEl.textContent = String(error);
    submitBtn.disabled = false;
  }
});

searchBtn.addEventListener("click", async () => {
  const q = searchInput.value.trim();
  searchStatus.textContent = `searching: ${q}`;
  searchResults.innerHTML = "";

  const response = await fetch(`/api/care-plans/search/?q=${encodeURIComponent(q)}`);
  const data = await response.json();
  searchStatus.textContent = `found: ${data.results.length}`;
  renderSearchResults(data.results);
});
