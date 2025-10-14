// Minimal D3 bar chart using demo data so you SEE it instantly.
(function renderHourlyDemo(){
  const container = d3.select("#d3-hourly");
  if (container.empty()) return;

  container.selectAll("*").remove();
  const width = container.node().clientWidth || 800;
  const height = 360;
  const margin = {top: 20, right: 24, bottom: 40, left: 48};

  const data = Array.from({length:24}, (_,h)=>({
    pickup_hour: h,
    trips: Math.round(2000 + 1000*Math.sin(h/24*Math.PI*2))
  }));

  const svg = container.append("svg")
    .attr("viewBox", `0 0 ${width} ${height}`)
    .style("width","100%").style("height","100%");

  const x = d3.scaleBand()
    .domain(data.map(d=>d.pickup_hour))
    .range([margin.left, width - margin.right]).padding(0.15);

  const y = d3.scaleLinear()
    .domain([0, d3.max(data, d=>d.trips)]).nice()
    .range([height - margin.bottom, margin.top]);

  svg.append("g")
    .attr("transform", `translate(0,${height - margin.bottom})`)
    .call(d3.axisBottom(x).tickFormat(d=>`${d}:00`))
    .selectAll("text").style("font-size","11px");

  svg.append("g")
    .attr("transform", `translate(${margin.left},0)`)
    .call(d3.axisLeft(y).ticks(6).tickFormat(d3.format(",")))
    .selectAll("text").style("font-size","11px");

  svg.append("g").attr("fill","#8aa9ff")
    .selectAll("rect").data(data).join("rect")
      .attr("x", d=>x(d.pickup_hour))
      .attr("y", d=>y(d.trips))
      .attr("width", x.bandwidth())
      .attr("height", d=>y(0)-y(d.trips))
      .attr("rx",4);

  svg.append("text")
    .attr("x", margin.left)
    .attr("y", margin.top - 6)
    .attr("fill", "#a9b4d0")
    .attr("font-size", 12)
    .text("Trips per hour (demo)");
})();

// --- Helper: safe get ctx by id
function ctx(id){ const el=document.getElementById(id); return el ? el.getContext('2d') : null; }

// --- Chart 1: Trips by Hour (demo)
(function(){
  const c = ctx('hourlyChart'); if(!c) return;
  const labels = Array.from({length:24}, (_,h)=> `${h}:00`);
  const data = labels.map((_,i)=> Math.round(800 + 600*Math.sin(i/24*Math.PI*2)));
  new Chart(c, {
    type:'bar',
    data:{ labels, datasets:[{ label:'Trips', data }] },
    options:{ responsive:true, plugins:{ legend:{ display:false }}, scales:{ y:{ beginAtZero:true } } }
  });
})();

// --- Chart 2: Avg Speed by Weekday (demo)
(function(){
  const c = ctx('weekdayChart'); if(!c) return;
  const labels = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];
  const data = [21,22,20,21,19,24,25];
  new Chart(c, {
    type:'bar',
    data:{ labels, datasets:[{ label:'km/h', data }] },
    options:{ responsive:true, plugins:{ legend:{ display:false }}, scales:{ y:{ beginAtZero:true } } }
  });
})();

// --- Chart 3: Slowest Hours (sec/km, demo)
(function(){
  const c = ctx('slowChart'); if(!c) return;
  const labels = Array.from({length:24}, (_,h)=> `${h}:00`);
  const data = labels.map((_,i)=> Math.round(150 + 70*Math.cos(i/24*Math.PI*2)));
  new Chart(c, {
    type:'line',
    data:{ labels, datasets:[{ label:'sec/km', data, tension:.25 }] },
    options:{ responsive:true, plugins:{ legend:{ display:false }}, scales:{ y:{ beginAtZero:false } } }
  });
})();

// --- Leaflet map (NYC, demo markers)
(function(){
  const el = document.getElementById('map'); if(!el) return;
  const map = L.map('map').setView([40.758, -73.985], 12);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{
    maxZoom: 19, attribution: '&copy; OpenStreetMap'
  }).addTo(map);

  // demo pickups
  [[40.758,-73.985],[40.742,-73.992],[40.731,-73.978],[40.75,-73.97]].forEach(([lat,lon])=>{
    L.circle([lat,lon], { radius: 250, color:'#8aa9ff', fillColor:'#8aa9ff', fillOpacity:.25 }).addTo(map);
  });
})();
