// ── Config ────────────────────────────────────────────────────────────────────
const API = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'http://localhost:8000'
  : 'https://auto-movie-book.onrender.com';

// ── State ─────────────────────────────────────────────────────────────────────
let selectedMovie   = null;
let selectedCity    = null;
let selectedTheatre = null;
let allTheatres     = [];
let movieDebounce   = null;
let cityDebounce    = null;

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  setupMovieSearch();
  setupCitySearch();
  setupTheatreSearch();
  loadMonitors();
  loadLogs();
  loadMovieCount();
  setInterval(() => { loadMonitors(); loadLogs(); }, 15000);
});

async function loadMovieCount() {
  try {
    const res  = await fetch(`${API}/`);
    const data = await res.json();
    const el   = document.getElementById('movieCount');
    if (el) el.textContent = `${data.movies_in_db} movies · ${data.active_monitors} monitoring`;
  } catch(e) {}
}

// ── Movie Search ──────────────────────────────────────────────────────────────
function setupMovieSearch() {
  const input    = document.getElementById('movieInput');
  const dropdown = document.getElementById('movieDropdown');
  input.addEventListener('input', () => {
    clearTimeout(movieDebounce);
    const q = input.value.trim();
    if (q.length < 2) { closeDropdown(dropdown); return; }
    movieDebounce = setTimeout(() => fetchMovies(q), 350);
  });
  document.addEventListener('click', (e) => {
    if (!input.contains(e.target) && !dropdown.contains(e.target)) closeDropdown(dropdown);
  });
}

async function fetchMovies(q) {
  const dropdown = document.getElementById('movieDropdown');
  dropdown.innerHTML = `<div class="dropdown-item"><div class="dropdown-info" style="color:#9090a8">🔍 Searching...</div></div>`;
  dropdown.classList.add('open');
  try {
    const res  = await fetch(`${API}/api/search/movies?q=${encodeURIComponent(q)}`);
    const data = await res.json();
    if (!data.movies || data.movies.length === 0) {
      dropdown.innerHTML = `
        <div class="dropdown-item">
          <div class="dropdown-info" style="color:#9090a8">
            No results for "<b>${q}</b>"<br>
            <small style="color:#606078">Add the movie first using "➕ Add Movie" section above</small>
          </div>
        </div>`;
      return;
    }
    dropdown.innerHTML = data.movies.map(m => `
      <div class="dropdown-item" onclick="selectMovie(${JSON.stringify(m).replace(/"/g,'&quot;')})">
        ${m.poster
          ? `<img class="dropdown-poster" src="${m.poster}" alt="${m.name}" onerror="this.outerHTML='<div class=\\'dropdown-poster-placeholder\\'>🎬</div>'">`
          : `<div class="dropdown-poster-placeholder">🎬</div>`}
        <div class="dropdown-info">
          <div class="dropdown-name">${m.name}</div>
          <div class="dropdown-meta">
            ${[m.lang, m.genre].filter(Boolean).join(' · ') || 'Movie'}
            <span class="status-tag ${m.status === 'coming_soon' ? 'coming' : 'showing'}">
              ${m.status === 'coming_soon' ? '🔜 Coming Soon' : '🎬 Now Showing'}
            </span>
          </div>
        </div>
      </div>`).join('');
  } catch(e) {
    dropdown.innerHTML = `<div class="dropdown-item"><div class="dropdown-info" style="color:#e63946">⚠️ Error connecting</div></div>`;
  }
}

function selectMovie(movie) {
  selectedMovie = movie;
  document.getElementById('movieInput').value = movie.name;
  closeDropdown(document.getElementById('movieDropdown'));
  const posterEl = document.getElementById('selectedMoviePoster');
  if (movie.poster) { posterEl.src = movie.poster; posterEl.style.display = 'block'; }
  else { posterEl.style.display = 'none'; }
  document.getElementById('selectedMovieName').textContent = movie.name;
  document.getElementById('selectedMovieMeta').textContent =
    [movie.lang, movie.genre].filter(Boolean).join(' · ') || 'Movie';
  document.getElementById('selectedMovieBox').style.display = 'flex';
  if (selectedCity) loadTheatresForCity();
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
    if (!data.cities || data.cities.length === 0) {
      dropdown.innerHTML = `<div class="dropdown-item"><div class="dropdown-info" style="color:#9090a8">No cities found</div></div>`;
      dropdown.classList.add('open');
      return;
    }
    dropdown.innerHTML = data.cities.map(c => `
      <div class="dropdown-item" onclick="selectCity('${c.name}','${c.code}')">
        <div class="dropdown-poster-placeholder">📍</div>
        <div class="dropdown-info">
          <div class="dropdown-name">${c.name}</div>
          <div class="dropdown-meta">Kerala · ${c.code}</div>
        </div>
      </div>`).join('');
    dropdown.classList.add('open');
  } catch(e) { console.error(e); }
}

function selectCity(name, code) {
  selectedCity = { name, code };
  document.getElementById('cityInput').value = name;
  closeDropdown(document.getElementById('cityDropdown'));
  enableTheatreSearch();
  loadTheatresForCity();
}

// ── Theatre Search ────────────────────────────────────────────────────────────
function setupTheatreSearch() {
  const input    = document.getElementById('theatreInput');
  const dropdown = document.getElementById('theatreDropdown');
  input.addEventListener('input', () => {
    const q = input.value.trim().toLowerCase();
    const filtered = q ? allTheatres.filter(t => t.name.toLowerCase().includes(q)) : allTheatres;
    renderTheatres(filtered);
  });
  input.addEventListener('focus', () => {
    if (allTheatres.length > 0) renderTheatres(allTheatres);
  });
  document.addEventListener('click', (e) => {
    if (!input.contains(e.target) && !dropdown.contains(e.target)) closeDropdown(dropdown);
  });
}

async function loadTheatresForCity() {
  if (!selectedCity) return;
  const input    = document.getElementById('theatreInput');
  const dropdown = document.getElementById('theatreDropdown');
  input.placeholder = `Loading theatres in ${selectedCity.name}...`;
  dropdown.innerHTML = `<div class="dropdown-item"><div class="dropdown-info" style="color:#9090a8">🎭 Loading theatres...</div></div>`;
  dropdown.classList.add('open');
  try {
    const res  = await fetch(`${API}/api/search/theatres?city=${encodeURIComponent(selectedCity.name)}`);
    const data = await res.json();
    allTheatres = data.theatres || [];
    if (allTheatres.length === 0) {
      input.placeholder = 'No theatres found for this city';
      dropdown.innerHTML = `<div class="dropdown-item"><div class="dropdown-info" style="color:#9090a8">No theatres found</div></div>`;
    } else {
      input.placeholder = `Search among ${allTheatres.length} theatres in ${selectedCity.name}...`;
      renderTheatres(allTheatres);
    }
  } catch(e) {
    input.placeholder = 'Error loading theatres';
  }
}

function renderTheatres(theatres) {
  const dropdown = document.getElementById('theatreDropdown');
  if (theatres.length === 0) {
    dropdown.innerHTML = `<div class="dropdown-item"><div class="dropdown-info" style="color:#9090a8">No matching theatres</div></div>`;
    dropdown.classList.add('open');
    return;
  }
  dropdown.innerHTML = theatres.map(t => `
    <div class="dropdown-item" onclick='selectTheatre(${JSON.stringify(t).replace(/'/g,"&#39;")})'>
      <div class="dropdown-poster-placeholder">🎭</div>
      <div class="dropdown-info">
        <div class="dropdown-name">${t.name}</div>
        <div class="dropdown-meta">${t.area}</div>
      </div>
      <span class="theatre-maps-tag" onclick="event.stopPropagation(); window.open('${t.maps_url}','_blank')">📍 Maps</span>
    </div>`).join('');
  dropdown.classList.add('open');
}

function selectTheatre(theatre) {
  selectedTheatre = theatre;
  document.getElementById('theatreInput').value = theatre.name;
  closeDropdown(document.getElementById('theatreDropdown'));
  document.getElementById('selectedTheatreName').textContent = theatre.name;
  document.getElementById('selectedTheatreArea').textContent = theatre.area;
  document.getElementById('mapsLink').href = theatre.maps_url || '#';
  document.getElementById('selectedTheatreBox').style.display = 'flex';
}

function clearTheatre() {
  selectedTheatre = null;
  document.getElementById('theatreInput').value = '';
  document.getElementById('selectedTheatreBox').style.display = 'none';
  if (allTheatres.length > 0) renderTheatres(allTheatres);
}

function enableTheatreSearch() {
  document.getElementById('theatreInput').disabled = false;
  document.getElementById('theatreInput').placeholder = 'Loading theatres...';
}

function disableTheatreSearch() {
  document.getElementById('theatreInput').disabled = true;
  document.getElementById('theatreInput').value = '';
  selectedTheatre = null; allTheatres = [];
  document.getElementById('selectedTheatreBox').style.display = 'none';
}

// ── Start Monitor ─────────────────────────────────────────────────────────────
async function startMonitor() {
  if (!selectedMovie) { showToast('Please select a movie!', 'error'); return; }
  if (!selectedCity)  { showToast('Please select a city!', 'error'); return; }
  const btn = document.getElementById('startBtn');
  const msg = document.getElementById('statusMsg');
  btn.disabled = true;
  btn.innerHTML = '<span class="btn-icon">⏳</span> Starting...';
  msg.textContent = '';
  try {
    const res = await fetch(`${API}/api/monitor`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        movie_name:   selectedMovie.name,
        movie_code:   selectedMovie.code,
        movie_poster: selectedMovie.poster || '',
        city:         selectedCity.name,
        theatre:      selectedTheatre?.name || '',
        theatre_code: selectedTheatre?.code || '',
        theatre_url:  selectedTheatre?.maps_url || '',
        maps_url:     selectedTheatre?.maps_url || '',
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Error');
    showToast(`✅ Monitoring "${selectedMovie.name}" in ${selectedCity.name}!`, 'success');
    msg.style.color = '#2ecc71';
    msg.textContent = selectedTheatre
      ? `✅ Waiting specifically for ${selectedTheatre.name} booking to open!`
      : `✅ Monitoring all theatres in ${selectedCity.name}!`;
    clearMovie(); clearTheatre();
    selectedCity = null; allTheatres = [];
    document.getElementById('cityInput').value = '';
    loadMonitors(); loadMovieCount();
  } catch(e) {
    showToast(e.message, 'error');
    msg.style.color = '#e63946';
    msg.textContent = '❌ ' + e.message;
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<span class="btn-icon">🚀</span> Start Monitoring';
  }
}

// ── Monitors ──────────────────────────────────────────────────────────────────
async function loadMonitors() {
  const container = document.getElementById('monitorsContainer');
  try {
    const res  = await fetch(`${API}/api/monitors`);
    const data = await res.json();
    const monitors = data.monitors || [];
    if (monitors.length === 0) {
      container.innerHTML = `<div class="empty-state"><div class="empty-icon">🎯</div><p>No monitors yet.<br>Add a movie and start monitoring!</p></div>`;
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
              ${m.theatre ? `🎭 ${m.theatre} &nbsp;·&nbsp;` : '🎭 Any Theatre &nbsp;·&nbsp;'}
              🕐 ${formatDate(m.created_at)}
              ${isOpen ? `<br>✅ Opened: ${formatDate(m.opened_at)}` : ''}
            </div>
            <div class="monitor-actions">
              ${isOpen
                ? `<span class="badge badge-opened">✅ OPEN</span>
                   <a class="open-bms-btn" href="${m.booking_url}" target="_blank">🎟️ Book Now</a>`
                : `<span class="badge badge-active badge-pulse">● Monitoring${m.theatre ? ' — Waiting for ' + m.theatre : ''}</span>`}
              ${m.status === 'active'
                ? `<button class="cancel-btn" onclick="cancelMonitor(${m.id})">Cancel</button>`
                : ''}
            </div>
          </div>
        </div>`;
    }).join('');
  } catch(e) {
    container.innerHTML = `<div class="empty-state"><p style="color:#e63946">Could not connect to server.</p></div>`;
  }
}

async function cancelMonitor(id) {
  await fetch(`${API}/api/monitor/${id}`, { method: 'DELETE' });
  showToast('Monitor cancelled', 'success');
  loadMonitors();
}

// ── Add Movie Manually ────────────────────────────────────────────────────────
function toggleAddMovie() {
  const sec = document.getElementById('addMovieSection');
  const btn = event.target;
  if (sec.style.display === 'none') {
    sec.style.display = 'block';
    btn.textContent = '▲ Collapse';
    loadMovieList();
  } else {
    sec.style.display = 'none';
    btn.textContent = '▼ Expand';
  }
}

function extractFromUrl(url) {
  const codeMatch = url.match(/movie-[a-z]+-([A-Z0-9]+)-MT/i);
  if (codeMatch) document.getElementById('addMovieCode').value = codeMatch[1].toUpperCase();
  const nameMatch = url.match(/buytickets\/([^\/]+)\//);
  if (nameMatch && !document.getElementById('addMovieName').value) {
    document.getElementById('addMovieName').value =
      nameMatch[1].replace(/-/g,' ').replace(/\b\w/g, l => l.toUpperCase());
  }
}

async function addMovieManual() {
  const name   = document.getElementById('addMovieName').value.trim();
  const code   = document.getElementById('addMovieCode').value.trim().toUpperCase();
  const lang   = document.getElementById('addMovieLang').value.trim();
  const genre  = document.getElementById('addMovieGenre').value.trim();
  const status = document.getElementById('addMovieStatus').value;
  const msg    = document.getElementById('addMovieMsg');
  if (!name) { showToast('Enter movie name!', 'error'); return; }
  if (!code) { showToast('Enter movie code!', 'error'); return; }
  msg.style.color = '#9090a8'; msg.textContent = 'Adding...';
  try {
    const res  = await fetch(`${API}/api/movies/add`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, code, language: lang, genre, status })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Error');
    showToast(data.message, 'success');
    msg.style.color = '#2ecc71'; msg.textContent = data.message;
    ['bmsUrlInput','addMovieName','addMovieCode','addMovieLang','addMovieGenre'].forEach(id => {
      document.getElementById(id).value = '';
    });
    loadMovieList(); loadMovieCount();
  } catch(e) {
    msg.style.color = '#e63946'; msg.textContent = '❌ ' + e.message;
  }
}

async function loadMovieList() {
  const container = document.getElementById('movieListContainer');
  if (!container) return;
  try {
    const res  = await fetch(`${API}/api/movies/list`);
    const data = await res.json();
    if (!data.movies || data.movies.length === 0) {
      container.innerHTML = '<div class="empty-state"><p>No movies yet. Add one above!</p></div>';
      return;
    }
    container.innerHTML = data.movies.map(m => `
      <div class="movie-list-item">
        ${m.poster
          ? `<img class="movie-list-poster" src="${m.poster}" alt="${m.name}" onerror="this.style.display='none'">`
          : `<div class="movie-list-poster" style="display:flex;align-items:center;justify-content:center;font-size:20px">🎬</div>`}
        <div class="movie-list-info">
          <div class="movie-list-name">${m.name}</div>
          <div class="movie-list-meta">
            ${[m.language, m.genre].filter(Boolean).join(' · ')}
            <span class="status-tag ${m.status === 'coming_soon' ? 'coming' : 'showing'}">
              ${m.status === 'coming_soon' ? '🔜 Coming Soon' : '🎬 Now Showing'}
            </span>
          </div>
        </div>
        <span class="movie-list-code">${m.code}</span>
        <button class="delete-movie-btn" onclick="deleteMovie('${m.code}','${m.name}')">🗑️</button>
      </div>`).join('');
  } catch(e) {
    container.innerHTML = '<div class="empty-state"><p style="color:#e63946">Error loading</p></div>';
  }
}

async function deleteMovie(code, name) {
  if (!confirm(`Remove "${name}"?`)) return;
  await fetch(`${API}/api/movies/${code}`, { method: 'DELETE' });
  showToast(`"${name}" removed`, 'success');
  loadMovieList(); loadMovieCount();
}

// ── Logs ──────────────────────────────────────────────────────────────────────
async function loadLogs() {
  const container = document.getElementById('logsContainer');
  try {
    const res  = await fetch(`${API}/api/logs`);
    const data = await res.json();
    if (!data.logs || data.logs.length === 0) {
      container.innerHTML = '<div class="empty-state"><p>No activity yet.</p></div>';
      return;
    }
    container.innerHTML = data.logs.map(l => `
      <div class="log-item">
        <div class="log-time">${formatDate(l.created_at)}</div>
        <div class="log-msg">${l.message}</div>
      </div>`).join('');
  } catch(e) { console.error(e); }
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function closeDropdown(el) { el.classList.remove('open'); el.innerHTML = ''; }
function formatDate(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleString('en-IN', { day:'2-digit', month:'short', hour:'2-digit', minute:'2-digit' });
}
function showToast(msg, type = '') {
  const toast = document.getElementById('toast');
  toast.textContent = msg;
  toast.className = `toast ${type} show`;
  setTimeout(() => { toast.className = 'toast'; }, 3500);
}
