const API_BASE = '/api';  // Relative path, works behind Nginx proxy

// DOM helpers
const el = (id) => document.getElementById(id);
const startDate = el('startDate');
const endDate = el('endDate');
const vendorId = el('vendorId');
const passengerCount = el('passengerCount');
const minSpeed = el('minSpeed');
const maxSpeed = el('maxSpeed');
const bbox = el('bbox');

const applyBtn = el('applyFilters');
const resetBtn = el('resetFilters');

const kpiTotal = el('kpiTotal');
const kpiAvgSpeed = el('kpiAvgSpeed');
const kpiAvgDist = el('kpiAvgDist');
const kpiDate = el('kpiDate');
const summaryDate = el('summaryDate');
const loadSummaryBtn = el('loadSummary');
const summaryOutput = el('summaryOutput');

const tripList = el('tripList');
const prevPage = el('prevPage');
const nextPage = el('nextPage');
const pageInfo = el('pageInfo');

// Charts
let hourlyChart, weekdayChart, slowChart;

// Map
let map, markersLayer;

// Utility for building query strings
function qs(params) {
  const p = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== null && v !== undefined && v !== '') p.set(k, v);
  });
  return p.toString();
}

async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// Load KPIs
async function loadKPIs() {
  try {
    const stats = await fetchJSON(`${API_BASE}/stats`);
    kpiTotal.textContent = stats.total_rows?.toLocaleString() ?? '—';
    kpiAvgSpeed.textContent = stats.avg_speed_kmh ?? '—';
    kpiAvgDist.textContent = stats.avg_distance_km ?? '—';
  } catch (e) {
    console.error(e);
  }
}

// Load summary
async function loadSummary() {
  const d = summaryDate.value;
  if (!d) { summaryOutput.textContent = 'Pick a date'; return; }
  try {
    const data = await fetchJSON(`${API_BASE}/summary?date=${encodeURIComponent(d)}`);
    if (!data) {
      summaryOutput.textContent = 'No data for selected date';
      kpiDate.textContent = '—';
      return;
    }
    summaryOutput.innerHTML = `
      <div class="trip-row"><b>Date:</b> ${data.date}</div>
      <div class="trip-row"><b>Trips:</b> ${data.trips?.toLocaleString()}</div>
      <div class="trip-row"><b>Avg Speed (km/h):</b> ${data.avg_speed_kmh}</div>
      <div class="trip-row"><b>Avg Distance (km):</b> ${data.avg_distance_km}</div>
      <div class="trip-row"><b>Avg Duration (min):</b> ${data.avg_duration_min}</div>
    `;
    kpiDate.textContent = data.date;
  } catch (e) {
    summaryOutput.textContent = 'Error loading summary';
    console.error(e);
  }
}

// Load charts
async function loadCharts() {
  try {
    const hourly = await fetchJSON(`${API_BASE}/insights/hourly`);
    const weekday = await fetchJSON(`${API_BASE}/insights/weekday-speed`);
    const slow = await fetchJSON(`${API_BASE}/insights/slow-hours`);

    // Hourly chart
    const ctxH = el('hourlyChart');
    const labelsH = hourly.map(x => x.pickup_hour);
    const dataH = hourly.map(x => x.trips);
    const existingH = Chart.getChart(ctxH);
    if (existingH) existingH.destroy();
    hourlyChart = new Chart(ctxH, {
      type: 'bar',
      data: { labels: labelsH, datasets: [{ label: 'Trips', data: dataH }] },
      options: { responsive: true, plugins: { legend: { display: false } } }
    });

    // Weekday chart
    const ctxW = el('weekdayChart');
    const labelsW = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];
    const dataW = weekday.map(x => x.avg_speed_kmh);
    const existingW = Chart.getChart(ctxW);
    if (existingW) existingW.destroy();
    weekdayChart = new Chart(ctxW, {
      type: 'bar',
      data: { labels: labelsW, datasets: [{ label: 'Avg Speed (km/h)', data: dataW }] },
      options: { responsive: true, plugins: { legend: { display: false } } }
    });

    // Slow chart
    const ctxS = el('slowChart');
    const labelsS = slow.map(x => x.pickup_hour);
    const dataS = slow.map(x => x.avg_sec_per_km);
    const existingS = Chart.getChart(ctxS);
    if (existingS) existingS.destroy();
    slowChart = new Chart(ctxS, {
      type: 'line',
      data: { labels: labelsS, datasets: [{ label: 'Sec per km', data: dataS }] },
      options: { responsive: true }
    });
  } catch (e) {
    console.error(e);
  }
}

// Trips
let currentPage = 1;
let currentFilters = {};

async function loadTrips(page = 1) {
  currentPage = page;
  const sortBy = el('sortBy')?.value || 'pickup_datetime';
  const sortOrder = el('sortOrder')?.value || 'desc';

  const params = {
    page,
    pageSize: 20,
    sortBy,
    sortOrder,
    start: startDate.value || undefined,
    end: endDate.value || undefined,
    vendorId: vendorId.value || undefined,
    passengerCount: passengerCount.value || undefined,
    minSpeed: minSpeed.value || undefined,
    maxSpeed: maxSpeed.value || undefined,
    bbox: bbox.value || undefined
  };
  currentFilters = params;
  const url = `${API_BASE}/trips?${qs(params)}`;

  try {
    const data = await fetchJSON(url);
    renderTrips(data);
    const statusEl = el('filterStatus');
    if (statusEl) {
      statusEl.textContent = `Sorted by ${sortBy} (${sortOrder}) | Using custom QuickSort algorithm`;
    }
  } catch (e) {
    console.error(e);
    const statusEl = el('filterStatus');
    if (statusEl) {
      statusEl.textContent = 'Error loading trips';
      statusEl.style.color = 'red';
    }
  }
}

function renderTrips(payload) {
  pageInfo.textContent = `Page ${payload.page} of ${Math.ceil(payload.total / payload.pageSize)} (Total: ${payload.total.toLocaleString()})`;
  tripList.innerHTML = '';
  payload.data.forEach(t => {
    const div = document.createElement('div');
    div.className = 'trip';
    div.innerHTML = `
      <div class="trip-row"><b>ID:</b> ${t.id}</div>
      <div class="trip-row">
        <div><b>Pickup:</b> ${t.pickup_datetime}</div>
        <div><b>Dropoff:</b> ${t.dropoff_datetime}</div>
      </div>
      <div class="trip-row">
        <div><b>Passengers:</b> ${t.passenger_count}</div>
        <div><b>Vendor:</b> ${t.vendor_id}</div>
        <div><b>Speed (km/h):</b> ${Number(t.speed_kmh).toFixed(1)}</div>
        <div><b>Distance (km):</b> ${Number(t.distance_km).toFixed(2)}</div>
        <div><b>Duration (s):</b> ${t.trip_duration}</div>
      </div>
      <div class="trip-row">
        <div><b>Pickup:</b> [${t.pickup_latitude}, ${t.pickup_longitude}]</div>
        <div><b>Dropoff:</b> [${t.dropoff_latitude}, ${t.dropoff_longitude}]</div>
      </div>
    `;
    tripList.appendChild(div);
  });
}

// Events
function attachEvents() {
  applyBtn.addEventListener('click', () => loadTrips(1));
  resetBtn.addEventListener('click', () => {
    [startDate, endDate, vendorId, passengerCount, minSpeed, maxSpeed, bbox].forEach(i => i.value = '');
    if (el('sortBy')) el('sortBy').value = 'pickup_datetime';
    if (el('sortOrder')) el('sortOrder').value = 'desc';
    loadTrips(1);
  });
  prevPage.addEventListener('click', () => { if (currentPage > 1) loadTrips(currentPage - 1); });
  nextPage.addEventListener('click', () => loadTrips(currentPage + 1));
  loadSummaryBtn.addEventListener('click', loadSummary);
  el('loadNear').addEventListener('click', loadNear);

  if (el('sortBy')) el('sortBy').addEventListener('change', () => loadTrips(1));
  if (el('sortOrder')) el('sortOrder').addEventListener('change', () => loadTrips(1));
}

// Map
function initMap() {
  map = L.map('map').setView([40.7580, -73.9855], 13);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '&copy; OpenStreetMap contributors' }).addTo(map);
  markersLayer = L.layerGroup().addTo(map);
}

async function loadNear() {
  const lat = Number(el('nearLat').value);
  const lon = Number(el('nearLon').value);
  const radius = Number(el('nearRadius').value || 1000);
  const url = `${API_BASE}/insights/near?lat=${lat}&lon=${lon}&radius=${radius}&page=1&pageSize=100`;
  try {
    const payload = await fetchJSON(url);
    markersLayer.clearLayers();
    payload.data.forEach(row => {
      const m = L.circleMarker([row.pickup_latitude, row.pickup_longitude], { radius: 4 });
      m.bindPopup(`<b>${row.id}</b><br/>${row.pickup_datetime}<br/>${(row.meters_away).toFixed(0)} m away`);
      markersLayer.addLayer(m);
    });
    map.setView([lat, lon], 14);
  } catch (e) { console.error(e); }
}

// Init
(async function init() {
  attachEvents();
  initMap();
  await loadKPIs();
  await loadCharts();
  await loadTrips(1);
})();
