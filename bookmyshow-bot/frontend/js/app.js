// ── Config ──────────────────────────────────────────────────────────────────
const API = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'http://localhost:8000'
  : 'https://your-backend.railway.app'; // ← Replace with your Railway URL after deploy

// ── State ────────────────────────────────────────────────────────────────────
let selectedMovie   = null;
let selectedCity    = null;
let selectedTheatre = null;
let movieDebounce   = null;
let cityDebounce    = null;
let theatreDebounce = null;
let pollTimer       = null;

// ── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  setupMovieSearch();
  setupCitySearch();
  setupTheatreSearch();
  loadMonitors();
  loadLogs();
  // Auto-refresh monitors every 15 seconds
  setInterval(() => { loadMonitors(); loadLogs(); }, 15000);
});

// ── Movie Search ──────────────────────────────────────────────────────────────
function setupMovieSearch() {
  const input = document.getElementById('movieInput');
  const dropdown = document.getElementById('movieDropdown');

  input.addEventListener('input', () => {
    clearTimeout(movieDebounce);
    const q = input.value.trim();
    if (q.length < 2) { closeDropdown(dropdown); return; }
    movieDebounce = setTimeout(() => fetchMovies(q), 300);
  });

  document.addEventListener('click', (e) => {
    if (!input.contains(e.target) && !dropdown.contains(e.target)) closeDropdown(dropdown);
  });
}

async function fetchMovies(q) {
  const dropdown = document.getElementById('movieDropdown');
  dropdown.innerHTML = '<div class="dropdown-item"><div class="dropdown-info" style="color:#606078">Searching...</div></div>';
  dropdown.classList.add('open');
  try {
    const res  = await fetch(`${API}/api/search/movies?q=${encodeURIComponent(q)}`);
    const data = await res.json();
    if (data.movies.length === 0) {
      dropdown.innerHTML = '<div class="dropdown-item"><div class="dropdown-info" style="color:#606078">No movies found</div></div>';
      return;
    }
    dropdown.innerHTML = data.movies.map(m => `
      <div class="dropdown-item" onclick="selectMovie(${JSON.stringify(m).replace(/"/g, '&quot;')})">
        ${m.poster
          ? `<img class="dropdown-poster" src="${m.poster}" alt="${m.name}" onerror="this.style.display='none'">`
          : `<div class="dropdown-poster-placeholder">🎬</div>`}
        <div class="dropdown-info">
          <div class="dropdown-name">${m.name}</div>
          <div class="dropdown-meta">${[m.lang, m.genre].filter(Boolean).join(' · ')}</div>
        </div>
      </div>
    `).join('');
  } catch (e) {
    dropdown.innerHTML = '<div class="dropdown-item"><div class="dropdown-info" style="color:#e63946">Error fetching movies</div></div>';
  }
}

function selectMovie(movie) {
  selectedMovie = movie;
  document.getElementById('movieInput').value = movie.name;
  closeDropdown(document.getElementById('movieDropdown'));

  const box = document.getElementById('selectedMovieBox');
  document.getElementById('selectedMoviePoster').src = movie.poster || '';
  document.getElementById('selectedMoviePoster').style.display = movie.poster ? 'block' : 'none';
  document.getElementById('selectedMovieName').textContent = movie.name;
  document.getElementById('selectedMovieMeta').textContent = [movie.lang, movie.genre].filter(Boolean).join(' · ');
  box.style.display = 'flex';

  // Enable theatre search if city is selected
  if (selectedCity) enableTheatreSearch();
}

function clearMovie() {
  selectedMovie = null;
  document.getElementById('movieInput').value = '';
  document.getElementById('selectedMovieBox').style.display = 'none';
  disableTheatreSearch();
}

// ── City Search ───────────────────────────────────────────────────────────────
function setupCitySearch() {
  const input    = document.getElementById('cityInput');
  const dropdown = document.getElementById('cityDropdown');

  input.addEventListener('input', () => {
    clearTimeout(cityDebounce);
    const q = input.value.trim();
    if (q.length < 1) { closeDropdown(dropdown); return; }
    cityDebounce = setTimeout(() => fetchCities(q), 200);
  });

  document.addEventListener('click', (e) => {
    if (!input.contains(e.target) && !dropdown.contains(e.target)) closeDropdown(dropdown);
  });
}

async function fetchCities(q) {
  const dropdown = document.getElementById('cityDropdown');
  try {
    const res  = await fetch(`${API}/api/search/cities?q=${encodeURIComponent(q)}`);
    const data = await res.json();
    if (data.cities.length === 0) { closeDropdown(dropdown); return; }
    dropdown.innerHTML = data.cities.map(c => `
      <div class="dropdown-item" onclick="selectCity('${c.name}', '${c.code}')">
        <div class="dropdown-poster-placeholder">🏙️</div>
        <div class="dropdown-info">
          <div class="dropdown-name">${c.name}</div>
          <div class="dropdown-meta">${c.code}</div>
        </div>
      </div>
    `).join('');
    dropdown.classList.add('open');
  } catch (e) { console.error(e); }
}

function selectCity(name, code) {
  selectedCity = { name, code };
  document.getElementById('cityInput').value = name;
  closeDropdown(document.getElementById('cityDropdown'));
  if (selectedMovie) enableTheatreSearch();
}

// ── Theatre Search ────────────────────────────────────────────────────────────
function setupTheatreSearch() {
  const input    = document.getElementById('theatreInput');
  const dropdown = document.getElementById('theatreDropdown');

  input.addEventListener('input', () => {
    clearTimeout(theatreDebounce);
    const q = input.value.trim();
    if (q.length < 1) { closeDropdown(dropdown); return; }
    theatreDebounce = setTimeout(() => fetchTheatres(q), 300);
  });

  document.addEventListener('click', (e) => {
    if (!input.contains(e.target) && !dropdown.contains(e.target)) closeDropdown(dropdown);
  });
}

async function fetchTheatres(q) {
  if (!selectedMovie || !selectedCity) return;
  const dropdown = document.getElementById('theatreDropdown');
  dropdown.innerHTML = '<div class="dropdown-item"><div class="dropdown-info" style="color:#606078">Loading theatres...</div></div>';
  dropdown.classList.add('open');

  try {
    const res  = await fetch(`${API}/api/search/theatres?city=${encodeURIComponent(selectedCity.name)}&movie_code=${selectedMovie.code}`);
    const data = await res.json();
    const filtered = data.theatres.filter(t => t.name.toLowerCase().includes(q.toLowerCase()));

    if (filtered.length === 0) {
      dropdown.innerHTML = '<div class="dropdown-item"><div class="dropdown-info" style="color:#606078">No theatres found</div></div>';
      return;
    }

    dropdown.innerHTML = filtered.map(t => `
      <div class="dropdown-item" onclick='selectTheatre(${JSON.stringify(t).replace(/'/g, "&#39;")})'>
        <div class="dropdown-poster-placeholder">🎭</div>
        <div class="dropdown-info">
          <div class="dropdown-name">${t.name}</div>
          <div class="dropdown-meta">${t.area || 'Tap to view location'}</div>
        </div>
        <span class="theatre-maps-tag">📍 Maps</span>
      </div>
    `).join('');
  } catch (e) {
    dropdown.innerHTML = '<div class="dropdown-item"><div class="dropdown-info" style="color:#e63946">Error loading theatres</div></div>';
  }
}

function selectTheatre(theatre) {
  selectedTheatre = theatre;
  document.getElementById('theatreInput').value = theatre.name;
  closeDropdown(document.getElementById('theatreDropdown'));

  document.getElementById('selectedTheatreName').textContent = theatre.name;
  document.getElementById('selectedTheatreArea').textContent  = theatre.area || '';
  document.getElementById('mapsLink').href = theatre.maps_url || '#';
  document.getElementById('selectedTheatreBox').style.display = 'flex';

  // Auto-open Google Maps
  if (theatre.maps_url) window.open(theatre.maps_url, '_blank');
}

function clearTheatre() {
  selectedTheatre = null;
  document.getElementById('theatreInput').value = '';
  document.getElementById('selectedTheatreBox').style.display = 'none';
}

function enableTheatreSearch() {
  document.getElementById('theatreInput').disabled = false;
  document.getElementById('theatreInput').placeholder = 'Type theatre name...';
}

function disableTheatreSearch() {
  document.getElementById('theatreInput').disabled = true;
  document.getElementById('theatreInput').value    = '';
  selectedTheatre = null;
  document.getElementById('selectedTheatreBox').style.display = 'none';
}

// ── Start Monitor ─────────────────────────────────────────────────────────────
async function startMonitor() {
  if (!selectedMovie) { showToast('Please select a movie first!', 'error'); return; }
  if (!selectedCity)  { showToast('Please select a city!', 'error'); return; }

  const btn = document.getElementById('startBtn');
  const msg = document.getElementById('statusMsg');
  btn.disabled = true;
  btn.innerHTML = '<span class="btn-icon">⏳</span> Starting...';
  msg.textContent = '';

  try {
    const res  = await fetch(`${API}/api/monitor`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        movie_name:   selectedMovie.name,
        movie_code:   selectedMovie.code,
        movie_poster: selectedMovie.poster || '',
        city:         selectedCity.name,
        theatre:      selectedTheatre?.name || '',
        theatre_url:  selectedTheatre?.maps_url || '',
      })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Error');

    showToast(`✅ Now monitoring "${selectedMovie.name}" in ${selectedCity.name}!`, 'success');
    msg.textContent = `✅ Monitoring started! You'll get WhatsApp & call when booking opens.`;

    // Reset form
    clearMovie(); clearTheatre();
    selectedCity = null;
    document.getElementById('cityInput').value = '';

    loadMonitors();

  } catch (e) {
    showToast(e.message, 'error');
    msg.style.color = '#e63946';
    msg.textContent = '❌ ' + e.message;
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<span class="btn-icon">🚀</span> Start Monitoring';
  }
}

// ── Load Monitors ─────────────────────────────────────────────────────────────
async function loadMonitors() {
  const container = document.getElementById('monitorsContainer');
  try {
    const res  = await fetch(`${API}/api/monitors`);
    const data = await res.json();
    const monitors = data.monitors;

    if (monitors.length === 0) {
      container.innerHTML = `<div class="empty-state"><div class="empty-icon">🎯</div><p>No active monitors yet.<br>Set your movie above to start!</p></div>`;
      return;
    }

    container.innerHTML = monitors.map(m => {
      const isOpen = m.status === 'opened';
      return `
        <div class="monitor-item ${m.status}">
          ${m.movie_poster
            ? `<img class="monitor-poster" src="${m.movie_poster}" alt="${m.movie_name}" onerror="this.style.display='none'">`
            : `<div class="monitor-poster" style="display:flex;align-items:center;justify-content:center;font-size:28px;background:#1a1a25">🎬</div>`}
          <div class="monitor-info">
            <div class="monitor-movie">${m.movie_name}</div>
            <div class="monitor-meta">
              🏙️ ${m.city} &nbsp;·&nbsp;
              ${m.theatre ? `🎭 ${m.theatre} &nbsp;·&nbsp;` : ''}
              🕐 ${formatDate(m.created_at)}
              ${isOpen ? `<br>✅ Booking opened: ${formatDate(m.opened_at)}` : ''}
            </div>
            <div class="monitor-actions">
              ${isOpen
                ? `<span class="badge badge-opened">✅ OPEN</span>
                   <a class="open-bms-btn" href="${m.booking_url}" target="_blank">🎟️ Book Now</a>`
                : `<span class="badge badge-active badge-pulse">● Monitoring</span>`}
              ${m.status === 'active'
                ? `<button class="cancel-btn" onclick="cancelMonitor(${m.id})">Cancel</button>`
                : ''}
            </div>
          </div>
        </div>
      `;
    }).join('');
  } catch (e) {
    container.innerHTML = `<div class="empty-state"><p style="color:#e63946">Could not connect to server.<br>Make sure backend is running.</p></div>`;
  }
}

async function cancelMonitor(id) {
  await fetch(`${API}/api/monitor/${id}`, { method: 'DELETE' });
  showToast('Monitor cancelled', 'success');
  loadMonitors();
}

// ── Load Logs ─────────────────────────────────────────────────────────────────
async function loadLogs() {
  const container = document.getElementById('logsContainer');
  try {
    const res  = await fetch(`${API}/api/logs`);
    const data = await res.json();
    if (data.logs.length === 0) {
      container.innerHTML = '<div class="empty-state"><p>No activity yet.</p></div>';
      return;
    }
    container.innerHTML = data.logs.map(l => `
      <div class="log-item">
        <div class="log-time">${formatDate(l.created_at)}</div>
        <div class="log-msg">${l.message}</div>
      </div>
    `).join('');
  } catch (e) { console.error(e); }
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function closeDropdown(el) { el.classList.remove('open'); el.innerHTML = ''; }

function formatDate(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleString('en-IN', { day:'2-digit', month:'short', hour:'2-digit', minute:'2-digit' });
}

function showToast(msg, type = '') {
  const toast = document.getElementById('toast');
  toast.textContent = msg;
  toast.className   = `toast ${type} show`;
  setTimeout(() => { toast.className = 'toast'; }, 3500);
}
