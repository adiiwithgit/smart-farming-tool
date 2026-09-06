// Change this to your deployed Render backend URL when you go live
const API_BASE = "http://localhost:8000";

let activeTab = "disease"; // disease | pest | nutrient
let selectedFile = null;
let userLat = null;
let userLon = null;

// ---------- Tab switching ----------
document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    activeTab = btn.dataset.tab;
    document.getElementById("diagnose-result").classList.add("hidden");
  });
});

// ---------- Image preview ----------
document.getElementById("image-input").addEventListener("change", (e) => {
  const file = e.target.files[0];
  if (!file) return;
  selectedFile = file;
  const preview = document.getElementById("image-preview");
  preview.src = URL.createObjectURL(file);
  preview.classList.remove("hidden");
});

// ---------- Diagnose ----------
document.getElementById("diagnose-btn").addEventListener("click", async () => {
  const resultBox = document.getElementById("diagnose-result");
  resultBox.className = "result-box";

  if (!selectedFile) {
    resultBox.classList.remove("hidden");
    resultBox.innerHTML = "Please choose an image first.";
    return;
  }

  resultBox.classList.remove("hidden");
  resultBox.innerHTML = "Analyzing image...";

  const formData = new FormData();
  formData.append("image", selectedFile);

  const endpointMap = {
    disease: "/api/diagnose/disease",
    pest: "/api/diagnose/pest",
    nutrient: "/api/diagnose/nutrient",
  };

  try {
    const res = await fetch(`${API_BASE}${endpointMap[activeTab]}`, {
      method: "POST",
      body: formData,
    });
    const data = await res.json();

    if (data.status === "error") {
      resultBox.classList.add("danger");
      resultBox.innerHTML = `⚠️ ${data.message}`;
    } else if (data.status === "loading") {
      resultBox.classList.add("warn");
      resultBox.innerHTML = `⏳ ${data.message}`;
    } else if (data.status === "not_implemented") {
      resultBox.classList.add("warn");
      resultBox.innerHTML = `
        <strong>⚙️ ${data.message}</strong><br/>
        <em>Placeholder tip:</em> ${data.tip}
      `;
    } else {
      resultBox.innerHTML = `
        <strong>Detected:</strong> ${data.label}<br/>
        <strong>Confidence:</strong> ${data.confidence}%<br/>
        <strong>Recommended action:</strong> ${data.tip}
      `;
    }
  } catch (err) {
    resultBox.classList.add("danger");
    resultBox.innerHTML = `⚠️ Could not reach backend. Is it running on ${API_BASE}? (${err.message})`;
  }
});

// ---------- Get user location once, reuse for irrigation + climate risk ----------
function getLocation() {
  return new Promise((resolve, reject) => {
    if (userLat !== null && userLon !== null) {
      resolve({ lat: userLat, lon: userLon });
      return;
    }
    if (!navigator.geolocation) {
      reject(new Error("Geolocation not supported by this browser."));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        userLat = pos.coords.latitude;
        userLon = pos.coords.longitude;
        resolve({ lat: userLat, lon: userLon });
      },
      () => reject(new Error("Location permission denied."))
    );
  });
}

// ---------- Irrigation advice ----------
document.getElementById("irrigation-btn").addEventListener("click", async () => {
  const resultBox = document.getElementById("irrigation-result");
  resultBox.className = "result-box";
  resultBox.classList.remove("hidden");
  resultBox.innerHTML = "Fetching location and weather...";

  const soilMoisture = parseFloat(document.getElementById("soil-moisture").value);

  try {
    const { lat, lon } = await getLocation();
    const res = await fetch(`${API_BASE}/api/irrigation-advice`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ soil_moisture_pct: soilMoisture, lat, lon }),
    });
    if (!res.ok) throw new Error(`Server error: ${res.status}`);
    const data = await res.json();

    if (data.urgency === "high") resultBox.classList.add("danger");
    else if (data.urgency === "medium") resultBox.classList.add("warn");

    resultBox.innerHTML = `
      <strong>Urgency:</strong> ${data.urgency.toUpperCase()}<br/>
      <strong>Action:</strong> ${data.action}<br/>
      <ul>${data.reasons.map((r) => `<li>${r}</li>`).join("")}</ul>
    `;
  } catch (err) {
    resultBox.classList.add("danger");
    resultBox.innerHTML = `⚠️ ${err.message}`;
  }
});

// ---------- Climate risk ----------
document.getElementById("climate-btn").addEventListener("click", async () => {
  const resultBox = document.getElementById("climate-result");
  resultBox.className = "result-box";
  resultBox.classList.remove("hidden");
  resultBox.innerHTML = "Fetching location and forecast data...";

  try {
    const { lat, lon } = await getLocation();
    const res = await fetch(`${API_BASE}/api/climate-risk`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ lat, lon }),
    });
    if (!res.ok) throw new Error(`Server error: ${res.status}`);
    const data = await res.json();

    const hasHighRisk = data.risks.some((r) => r.severity === "high");
    const hasModerateRisk = data.risks.some((r) => r.severity === "moderate");
    if (hasHighRisk) resultBox.classList.add("danger");
    else if (hasModerateRisk) resultBox.classList.add("warn");

    resultBox.innerHTML = data.risks
      .map(
        (r) => `
        <div class="risk-item">
          <strong>${r.type}</strong> ${r.severity !== "none" ? `(${r.severity})` : ""}<br/>
          ${r.detail}<br/>
          <em>Action: ${r.action}</em>
        </div>`
      )
      .join("");
  } catch (err) {
    resultBox.classList.add("danger");
    resultBox.innerHTML = `⚠️ ${err.message}`;
  }
});
