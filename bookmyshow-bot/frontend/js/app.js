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
let urlDebounce     = null;

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  setupMovieSearch();
  setupCitySearch();
  setupTheatreSearch();
  loadMonitors();
  loadLogs();
  loadMovieCount();
  setInterval(() => { loadMonitors(); loadLogs(); loadMovieCount(); }, 15000);
});

async function loadMovieCount() {
  try {
    const res  = await fetch(`${API}/`);
    const data = await res.json();
    const el   = document.getElementById('movieCount');
    if (el) el.textContent = `${data.movies_in_db} movies · ${data.active_monitors} monitoring`;
  } catch(e) {
    const el = document.getElementById('movieCount');
    if (el) el.textContent = 'Connecting...';
  }
}

// ── URL Auto Extract ──────────────────────────────────────────────────────────
function onUrlInput(val) {
  clearTimeout(urlDebounce);
  const preview  = document.getElementById('moviePreview');
  const loading  = document.getElementById('urlLoading');
  if (!val.trim() || !val.includes('bookmyshow.com')) {
    preview.style.display = 'none';
    loading.style.display = 'none';
    return;
  }
  loading.style.display = 'flex';
  preview.style.display = 'none';
  urlDebounce = setTimeout(() => fetchMovieFromUrl(val.trim()), 800);
}

async function fetchMovieFromUrl(url) {
  const loading = document.getElementById('urlLoading');
  const preview = document.getElementById('moviePreview');
  try {
    const res  = await fetch(`${API}/api/extract-movie?url=${encodeURIComponent(url)}`);
    const data = await res.json();
    loading.style.display = 'none';
    if (!res.ok) {
      showToast(data.detail || 'Could not extract movie info', 'error');
      return;
    }

    // Auto fill fields
    document.getElementById('addMovieName').value  = data.name || '';
    document.getElementById('addMovieCode').value  = data.code || '';
    document.getElementById('addMovieLang').value  = data.language || '';
    document.getElementById('addMovieGenre').value = data.genre || '';

    // Show preview card
    const posterEl = document.getElementById('previewPoster');
    if (data.poster) { posterEl.src = data.poster; posterEl.style.display = 'block'; }
    else { posterEl.style.display = 'none'; }

    document.getElementById('previewName').textContent = data.name || 'Unknown';
    document.getElementById('previewMeta').textContent =
      [data.language, data.genre].filter(Boolean).join(' · ') || 'Movie';
    document.getElementById('previewCode').textContent = `Code: ${data.code}`;

    const statusEl = document.getElementById('previewStatus');
    if (data.status === 'coming_soon') {
      statusEl.textContent = '🔜 Coming Soon';
      statusEl.style.background = 'rgba(255,214,10,0.12)';
      statusEl.style.color = '#ffd60a';
    } else {
      statusEl.textContent = '🎬 Now Showing';
      statusEl.style.background = 'rgba(46,204,113,0.12)';
      statusEl.style.color = '#2ecc71';
    }

    preview.style.display = 'flex';
    showToast(`✅ Movie info extracted: ${data.name}`, 'success');
  } catch(e) {
    loading.style.display = 'none';
    showToast('Error extracting movie info', 'error');
  }
}

// ── Add Movie Section ─────────────────────────────────────────────────────────
function toggleAddMovie() {
  const sec = document.getElementById('addMovieSection');
  const btn = document.getElementById('toggleBtn');
  if (sec.style.display === 'none') {
    sec.style.display = 'block';
    btn.textContent = '▲ Collapse';
    loadMovieList();
  } else {
    sec.style.display = 'none';
    btn.textContent = '▼ Expand';
  }
}

async function addMovieManual() {
  const name   = document.getElementById('addMovieName').value.trim();
  const code   = document.getElementById('addMovieCode').value.trim().toUpperCase();
  const lang   = document.getElementById('addMovieLang').value.trim();
  const genre  = document.getElementById('addMovieGenre').value.trim();
  const poster = document.getElementById('previewPoster').src || '';
  const statusEl = document.getElementById('previewStatus');
  const status = statusEl.textContent.includes('Coming') ? 'coming_soon' : 'now_showing';
  const msg    = document.getElementById('addMovieMsg');

  if (!name) { showToast('Movie name is required!', 'error'); return; }
  if (!code) { showToast('Movie code is required! Paste BMS URL to auto-fill.', 'error'); return; }

  msg.style.color = '#9090aa'; msg.textContent = '⏳ Adding...';
  try {
    const res  = await fetch(`${API}/api/movies/add`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, code, poster, language: lang, genre, status })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Error');
    showToast(data.message, 'success');
    msg.style.color = '#2ecc71'; msg.textContent = data.message;
    // Clear
    ['bmsUrlInput','addMovieName','addMovieCode','addMovieLang','addMovieGenre'].forEach(id => {
      document.getElementById(id).value = '';
    });
    document.getElementById('moviePreview').style.display = 'none';
    loadMovieList(); loadMovieCount();
  } catch(e) {
    msg.style.color = '#e63946'; msg.textContent = '❌ ' + e.message;
  }
}

async function loadMovieList() {
  const c = document.getElementById('movieListContainer');
  if (!c) return;
  try {
    const res  = await fetch(`${API}/api/movies/list`);
    const data = await res.json();
    if (!data.movies || data.movies.length === 0) {
      c.innerHTML = '<div class="empty-state"><p>No movies yet. Paste a BMS URL above!</p></div>';
      return;
    }
    c.innerHTML = data.movies.map(m => `
      <div class="movie-list-item">
        ${m.poster
          ? `<img class="movie-list-poster" src="${m.poster}" alt="${m.name}" onerror="this.style.display='none'">`
          : `<div class="movie-list-poster" style="display:flex;align-items:center;justify-content:center;font-size:18px">🎬</div>`}
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
        <button class="delete-movie-btn" onclick="deleteMovie('${m.code}','${m.name.replace(/'/g,'\\'')}')">🗑️</button>
      </div>`).join('');
  } catch(e) {
    c.innerHTML = '<div class="empty-state"><p style="color:#e63946">Error loading</p></div>';
  }
}

async function deleteMovie(code, name) {
  if (!confirm(`Remove "${name}" from database?`)) return;
  await fetch(`${API}/api/movies/${code}`, { method: 'DELETE' });
  showToast(`"${name}" removed`, 'success');
  loadMovieList(); loadMovieCount();
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
  dropdown.innerHTML = `<div class="dropdown-item"><div class="dropdown-info" style="color:#9090aa">🔍 Searching...</div></div>`;
  dropdown.classList.add('open');
  try {
    const res  = await fetch(`${API}/api/search/movies?q=${encodeURIComponent(q)}`);
    const data = await res.json();
    if (!data.movies || data.movies.length === 0) {
      dropdown.innerHTML = `
        <div class="dropdown-item">
          <div class="dropdown-info" style="color:#9090aa">
            No results for "<b>${q}</b>"<br>
            <small style="color:#55556a">Add the movie using "➕ Add Movie" section above</small>
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
    dropdown.innerHTML = `<div class="dropdown-item"><div class="dropdown-info" style="color:#e63946">⚠️ Error connecting to server</div></div>`;
  }
}

function selectMovie(movie) {
  selectedMovie = movie;
  document.getElementById('movieInput').value = movie.name;
  closeDropdown(document.getElementById('movieDropdown'));
  const posterEl  = document.getElementById('selectedMoviePoster');
  const noIconEl  = document.getElementById('noPosterIcon');
  if (movie.poster) {
    posterEl.src = movie.poster; posterEl.style.display = 'block'; noIconEl.style.display = 'none';
  } else {
    posterEl.style.display = 'none'; noIconEl.style.display = 'flex';
  }
  document.getElementById('selectedMovieName').textContent = movie.name;
  document.getElementById('selectedMovieMeta').textContent =
    [movie.lang, movie.genre].filter(Boolean).join(' · ') || 'Movie';
  document.getElementById('selectedMovieBox').style.display = 'flex';
}

function clearMovie() {
  selectedMovie = null;
  document.getElementById('movieInput').value = '';
  document.getElementById('selectedMovieBox').style.display = 'none';
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
      dropdown.innerHTML = `<div class="dropdown-item"><div class="dropdown-info" style="color:#9090aa">No cities found</div></div>`;
      dropdown.classList.add('open'); return;
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
  document.getElementById('theatreNote').style.display = 'block';
}

// ── Theatre Search ────────────────────────────────────────────────────────────
function setupTheatreSearch() {
  const input    = document.getElementById('theatreInput');
  const dropdown = document.getElementById('theatreDropdown');
  input.addEventListener('input', () => {
    const q        = input.value.trim().toLowerCase();
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
  dropdown.innerHTML = `<div class="dropdown-item"><div class="dropdown-info" style="color:#9090aa">🎭 Loading theatres...</div></div>`;
  dropdown.classList.add('open');
  try {
    const res  = await fetch(`${API}/api/search/theatres?city=${encodeURIComponent(selectedCity.name)}`);
    const data = await res.json();
    allTheatres = data.theatres || [];
    if (allTheatres.length === 0) {
      input.placeholder = 'No theatres found for this city';
      dropdown.innerHTML = `<div class="dropdown-item"><div class="dropdown-info" style="color:#9090aa">No theatres found</div></div>`;
    } else {
      input.placeholder = `Search among ${allTheatres.length} theatres in ${selectedCity.name}...`;
      renderTheatres(allTheatres);
    }
  } catch(e) { input.placeholder = 'Error loading theatres'; }
}

function renderTheatres(theatres) {
  const dropdown = document.getElementById('theatreDropdown');
  if (!theatres.length) {
    dropdown.innerHTML = `<div class="dropdown-item"><div class="dropdown-info" style="color:#9090aa">No matching theatres</div></div>`;
    dropdown.classList.add('open'); return;
  }
  dropdown.innerHTML = theatres.map(t => `
    <div class="dropdown-item" onclick='selectTheatre(${JSON.stringify(t).replace(/'/g,"&#39;")})'>
      <div class="dropdown-poster-placeholder">🎭</div>
      <div class="dropdown-info">
        <div class="dropdown-name">${t.name}</div>
        <div class="dropdown-meta">${t.area}</div>
      </div>
      <span class="theatre-maps-tag" onclick="event.stopPropagation();window.open('${t.maps_url}','_blank')">📍 Maps</span>
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
  document.getElementById('theatreNote').style.display = 'none';
}

function clearTheatre() {
  selectedTheatre = null;
  document.getElementById('theatreInput').value = '';
  document.getElementById('selectedTheatreBox').style.display = 'none';
  document.getElementById('theatreNote').style.display = 'block';
  if (allTheatres.length > 0) renderTheatres(allTheatres);
}

function enableTheatreSearch() {
  document.getElementById('theatreInput').disabled = false;
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
      method: 'POST', headers: { 'Content-Type': 'application/json' },
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
    showToast(`✅ Monitoring "${selectedMovie.name}"!`, 'success');
    msg.style.color = '#2ecc71';
    msg.textContent = selectedTheatre
      ? `✅ Waiting specifically for "${selectedTheatre.name}" booking to open!`
      : `✅ Monitoring all theatres in ${selectedCity.name}. You'll get WhatsApp + call!`;
    // Reset
    clearMovie();
    selectedCity = null; allTheatres = [];
    document.getElementById('cityInput').value = '';
    document.getElementById('theatreInput').value = '';
    document.getElementById('theatreInput').disabled = true;
    document.getElementById('theatreInput').placeholder = 'Select a city first...';
    document.getElementById('selectedTheatreBox').style.display = 'none';
    document.getElementById('theatreNote').style.display = 'none';
    selectedTheatre = null;
    loadMonitors(); loadMovieCount();
  } catch(e) {
    showToast(e.message, 'error');
    msg.style.color = '#e63946'; msg.textContent = '❌ ' + e.message;
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<span class="btn-icon">🚀</span> Start Monitoring';
  }
}

// ── Monitors ──────────────────────────────────────────────────────────────────
async function loadMonitors() {
  const c = document.getElementById('monitorsContainer');
  try {
    const res  = await fetch(`${API}/api/monitors`);
    const data = await res.json();
    const monitors = data.monitors || [];
    if (!monitors.length) {
      c.innerHTML = `<div class="empty-state"><div class="empty-icon">🎯</div><p>No monitors yet.<br>Add a movie above and start monitoring!</p></div>`;
      return;
    }
    c.innerHTML = monitors.map(m => {
      const isOpen = m.status === 'opened';
      return `
        <div class="monitor-item ${m.status}">
          ${m.movie_poster
            ? `<img class="monitor-poster" src="${m.movie_poster}" alt="${m.movie_name}" onerror="this.style.display='none'">`
            : `<div class="monitor-poster" style="display:flex;align-items:center;justify-content:center;font-size:26px;background:#17171f">🎬</div>`}
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
                ? `<span class="badge badge-opened">✅ BOOKING OPEN</span>
                   <a class="open-bms-btn" href="${m.booking_url}" target="_blank">🎟️ Book Now</a>`
                : `<span class="badge badge-active badge-pulse">● Monitoring${m.theatre ? ' — Waiting for ' + m.theatre : ''}</span>`}
              ${m.status === 'active'
                ? `<button class="cancel-btn" onclick="cancelMonitor(${m.id})">Cancel</button>`
                : `<span class="badge" style="background:rgba(255,255,255,0.05);color:#55556a">${m.status}</span>`}
            </div>
          </div>
        </div>`;
    }).join('');
  } catch(e) {
    c.innerHTML = `<div class="empty-state"><p style="color:#e63946">Could not connect to server.</p></div>`;
  }
}

async function cancelMonitor(id) {
  if (!confirm('Cancel this monitor?')) return;
  await fetch(`${API}/api/monitor/${id}`, { method: 'DELETE' });
  showToast('Monitor cancelled', 'success');
  loadMonitors(); loadMovieCount();
}

// ── Logs ──────────────────────────────────────────────────────────────────────
async function loadLogs() {
  const c = document.getElementById('logsContainer');
  try {
    const res  = await fetch(`${API}/api/logs`);
    const data = await res.json();
    if (!data.logs || !data.logs.length) {
      c.innerHTML = '<div class="empty-state"><p>No activity yet.</p></div>'; return;
    }
    c.innerHTML = data.logs.map(l => `
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
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = `toast ${type} show`;
  setTimeout(() => { t.className = 'toast'; }, 3500);
}
