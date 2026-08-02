const form = document.getElementById("care-plan-form");
const statusEl = document.getElementById("status");
const outputEl = document.getElementById("output");
const submitBtn = document.getElementById("submit-btn");
const downloadLink = document.getElementById("download-link");
const searchInput = document.getElementById("search-input");
const searchBtn = document.getElementById("search-btn");
const searchStatus = document.getElementById("search-status");
const searchResults = document.getElementById("search-results");

function formDataToObject(formElement) {
  const formData = new FormData(formElement);
  return Object.fromEntries(formData.entries());
}

function renderCarePlan(data) {
  if (data.status !== "completed" || !data.care_plan) {
    outputEl.textContent = data.error ? `failed: ${data.error}` : "care plan not ready";
    downloadLink.style.display = "none";
    return;
  }

  const sections = [
    ["Problem list", data.care_plan.problem_list],
    ["Goals", data.care_plan.goals],
    ["Pharmacist interventions", data.care_plan.pharmacist_interventions],
    ["Monitoring plan", data.care_plan.monitoring_plan],
  ];

  outputEl.textContent = sections
    .map(([title, items]) => `${title}\n${items.map((item) => `- ${item}`).join("\n")}`)
    .join("\n\n");
  downloadLink.href = `/api/care-plans/${data.id}/download/`;
  downloadLink.style.display = "inline-block";
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
  submitBtn.disabled = true;
  statusEl.textContent = "submitting...";
  outputEl.textContent = "Submitting, please wait...";

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
      downloadLink.style.display = "none";
      return;
    }

    statusEl.textContent = `status: ${data.status}`;
    outputEl.textContent = `${data.message}\nCare Plan ID: ${data.careplan_id}`;
    downloadLink.style.display = "none";
  } catch (error) {
    statusEl.textContent = "failed";
    outputEl.textContent = String(error);
  } finally {
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
