// ── Config ────────────────────────────────────────────────────────────────────
const API = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'http://localhost:8000'
  : 'https://auto-movie-book.onrender.com';

// ── State ─────────────────────────────────────────────────────────────────────
let selectedMovie = null, selectedCity = null, selectedTheatre = null;
let allTheatres = [], movieDebounce = null, cityDebounce = null, urlDebounce = null;

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  setupMovieSearch(); setupCitySearch(); setupTheatreSearch();
  loadMonitors(); loadLogs(); loadMovieCount();
  setInterval(() => { loadMonitors(); loadLogs(); loadMovieCount(); }, 15000);
});

async function loadMovieCount() {
  try {
    const res = await fetch(`${API}/`, { signal: AbortSignal.timeout(8000) });
    const d   = await res.json();
    const el  = document.getElementById('movieCount');
    if (el) el.textContent = `${d.movies_in_db} movies · ${d.active_monitors} monitoring`;
  } catch(e) {
    const el = document.getElementById('movieCount');
    if (el) el.textContent = 'Backend waking up... ⏳';
    setTimeout(loadMovieCount, 5000);
  }
}

// ── URL Auto Extract ──────────────────────────────────────────────────────────
function onUrlInput(val) {
  clearTimeout(urlDebounce);
  const preview = document.getElementById('moviePreview');
  const loading = document.getElementById('urlLoading');
  if (!val.trim() || !val.includes('bookmyshow')) {
    preview.style.display = 'none'; loading.style.display = 'none'; return;
  }
  loading.style.display = 'flex'; preview.style.display = 'none';
  urlDebounce = setTimeout(() => fetchMovieFromUrl(val.trim()), 800);
}

async function fetchMovieFromUrl(url) {
  const loading = document.getElementById('urlLoading');
  const preview = document.getElementById('moviePreview');
  try {
    const res  = await fetch(`${API}/api/extract-movie?url=${encodeURIComponent(url)}`);
    const data = await res.json();
    loading.style.display = 'none';
    if (!res.ok) { showToast(data.detail || 'Could not extract', 'error'); return; }

    // Auto fill fields
    document.getElementById('addMovieName').value  = data.name || '';
    document.getElementById('addMovieCode').value  = data.code || '';
    document.getElementById('addMovieLang').value  = data.language || '';
    document.getElementById('addMovieGenre').value = data.genre || '';

    // Show preview
    const pImg = document.getElementById('previewPoster');
    const pIcon = document.getElementById('previewNoIcon');
    if (data.poster) { pImg.src = data.poster; pImg.style.display='block'; pIcon.style.display='none'; }
    else { pImg.style.display='none'; pIcon.style.display='flex'; }

    document.getElementById('previewName').textContent = data.name || 'Unknown';
    document.getElementById('previewMeta').textContent = [data.language, data.genre].filter(Boolean).join(' · ') || 'Movie';
    document.getElementById('previewCode').textContent = `Code: ${data.code}`;

    const sEl = document.getElementById('previewStatus');
    if (data.status === 'coming_soon') {
      sEl.textContent='🔜 Coming Soon'; sEl.style.background='rgba(255,214,10,0.12)'; sEl.style.color='#ffd60a';
    } else {
      sEl.textContent='🎬 Now Showing'; sEl.style.background='rgba(46,204,113,0.12)'; sEl.style.color='#2ecc71';
    }
    preview.style.display = 'flex';
    showToast(`✅ Extracted: ${data.name}`, 'success');
  } catch(e) {
    loading.style.display = 'none';
    showToast('Error fetching movie info', 'error');
  }
}

// ── Add Movie ─────────────────────────────────────────────────────────────────
function toggleAddMovie() {
  const sec = document.getElementById('addMovieSection');
  const btn = document.getElementById('toggleBtn');
  if (sec.style.display === 'none') {
    sec.style.display = 'block'; btn.textContent = '▲ Collapse'; loadMovieList();
  } else {
    sec.style.display = 'none'; btn.textContent = '▼ Expand';
  }
}

async function addMovieManual() {
  const name   = document.getElementById('addMovieName').value.trim();
  const code   = document.getElementById('addMovieCode').value.trim().toUpperCase();
  const lang   = document.getElementById('addMovieLang').value.trim();
  const genre  = document.getElementById('addMovieGenre').value.trim();
  const pImg = document.getElementById('previewPoster');
  const poster = (pImg && pImg.style.display !== 'none' && pImg.src && !pImg.src.endsWith('/')) ? pImg.src : '';
  const status = 'now_showing';
  const msg    = document.getElementById('addMovieMsg');
  if (!name) { showToast('Enter movie name!', 'error'); return; }
  if (!code) { showToast('Enter movie code! Paste BMS URL to auto-fill.', 'error'); return; }
  msg.style.color='#9090aa'; msg.textContent='⏳ Adding...';
  try {
    const res  = await fetch(`${API}/api/movies/add`, {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({name, code, poster, language:lang, genre, status})
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Error');
    showToast(data.message, 'success');
    msg.style.color='#2ecc71'; msg.textContent=data.message;
    ['bmsUrlInput','addMovieName','addMovieCode','addMovieLang','addMovieGenre'].forEach(id => {
      document.getElementById(id).value = '';
    });
    document.getElementById('moviePreview').style.display = 'none';
    loadMovieList(); loadMovieCount();
  } catch(e) { msg.style.color='#e63946'; msg.textContent='❌ '+e.message; }
}

async function loadMovieList() {
  const c = document.getElementById('movieListContainer');
  if (!c) return;
  try {
    const res  = await fetch(`${API}/api/movies/list`);
    const data = await res.json();
    if (!data.movies || !data.movies.length) {
      c.innerHTML = '<div class="empty-state"><p>No movies yet. Paste a BMS URL above!</p></div>'; return;
    }
    c.innerHTML = data.movies.map(m => `
      <div class="ml-item">
        ${m.poster
          ? `<img class="ml-poster" src="${m.poster}" onerror="this.style.display='none'" alt="${m.name}">`
          : `<div class="ml-poster" style="display:flex;align-items:center;justify-content:center;font-size:16px">🎬</div>`}
        <div class="ml-info">
          <div class="ml-name">${m.name}</div>
          <div class="ml-meta">${[m.language,m.genre].filter(Boolean).join(' · ')}
            <span class="stag ${m.status==='coming_soon'?'coming':'showing'}">${m.status==='coming_soon'?'🔜 Coming':'🎬 Showing'}</span>
          </div>
        </div>
        <span class="ml-code">${m.code}</span>
        <button class="ml-del" onclick="deleteMovie('${m.code}','${m.name.replace(/'/g,"\\'")}')">🗑️</button>
      </div>`).join('');
  } catch(e) { c.innerHTML='<div class="empty-state"><p style="color:#e63946">Error loading</p></div>'; }
}

async function deleteMovie(code, name) {
  if (!confirm(`Remove "${name}"?`)) return;
  await fetch(`${API}/api/movies/${code}`, {method:'DELETE'});
  showToast(`"${name}" removed`, 'success');
  loadMovieList(); loadMovieCount();
}

// ── Movie Search with Poster ──────────────────────────────────────────────────
function setupMovieSearch() {
  const input = document.getElementById('movieInput');
  const dd    = document.getElementById('movieDropdown');
  input.addEventListener('input', () => {
    clearTimeout(movieDebounce);
    const q = input.value.trim();
    if (q.length < 2) { closeDD(dd); return; }
    movieDebounce = setTimeout(() => fetchMovies(q), 350);
  });
  document.addEventListener('click', e => {
    if (!input.contains(e.target) && !dd.contains(e.target)) closeDD(dd);
  });
}

async function fetchMovies(q) {
  const dd = document.getElementById('movieDropdown');
  dd.innerHTML = `<div class="dropdown-item"><div class="dd-icon">🔍</div><div class="dd-info"><div class="dd-name" style="color:#9090aa">Searching...</div></div></div>`;
  dd.classList.add('open');
  try {
    const res  = await fetch(`${API}/api/search/movies?q=${encodeURIComponent(q)}`);
    const data = await res.json();
    if (!data.movies || !data.movies.length) {
      dd.innerHTML = `<div class="dropdown-item"><div class="dd-icon">🎬</div><div class="dd-info"><div class="dd-name" style="color:#9090aa">No results for "${q}"</div><div class="dd-meta">Add movie using ➕ Add Movie above</div></div></div>`;
      return;
    }
    dd.innerHTML = data.movies.map(m => `
      <div class="dropdown-item" onclick="selectMovie(${JSON.stringify(m).replace(/"/g,'&quot;')})">
        ${m.poster
          ? `<img class="dd-poster" src="${m.poster}" alt="${m.name}" onerror="this.outerHTML='<div class=\\'dd-icon\\'>🎬</div>'">`
          : `<div class="dd-icon">🎬</div>`}
        <div class="dd-info">
          <div class="dd-name">${m.name}</div>
          <div class="dd-meta">
            ${[m.lang,m.genre].filter(Boolean).join(' · ')||'Movie'}
            <span class="stag ${m.status==='coming_soon'?'coming':'showing'}">${m.status==='coming_soon'?'🔜 Coming Soon':'🎬 Now Showing'}</span>
          </div>
        </div>
      </div>`).join('');
  } catch(e) {
    dd.innerHTML = `<div class="dropdown-item"><div class="dd-info"><div class="dd-name" style="color:#e63946">⚠️ Connection error</div></div></div>`;
  }
}

function selectMovie(m) {
  selectedMovie = m;
  document.getElementById('movieInput').value = m.name;
  closeDD(document.getElementById('movieDropdown'));
  const pImg = document.getElementById('selectedMoviePoster');
  const pIcon = document.getElementById('selNoIcon');
  if (m.poster) { pImg.src=m.poster; pImg.style.display='block'; pIcon.style.display='none'; }
  else { pImg.style.display='none'; pIcon.style.display='flex'; }
  document.getElementById('selectedMovieName').textContent = m.name;
  document.getElementById('selectedMovieMeta').textContent = [m.lang,m.genre].filter(Boolean).join(' · ')||'Movie';
  document.getElementById('selectedMovieBox').style.display = 'flex';
}

function clearMovie() {
  selectedMovie = null;
  document.getElementById('movieInput').value = '';
  document.getElementById('selectedMovieBox').style.display = 'none';
}

// ── City Search ───────────────────────────────────────────────────────────────
function setupCitySearch() {
  const input = document.getElementById('cityInput');
  const dd    = document.getElementById('cityDropdown');
  input.addEventListener('input', () => {
    clearTimeout(cityDebounce);
    const q = input.value.trim();
    if (q.length < 1) { closeDD(dd); return; }
    cityDebounce = setTimeout(() => fetchCities(q), 200);
  });
  document.addEventListener('click', e => {
    if (!input.contains(e.target) && !dd.contains(e.target)) closeDD(dd);
  });
}

async function fetchCities(q) {
  const dd = document.getElementById('cityDropdown');
  try {
    const res  = await fetch(`${API}/api/search/cities?q=${encodeURIComponent(q)}`);
    const data = await res.json();
    if (!data.cities || !data.cities.length) {
      dd.innerHTML=`<div class="dropdown-item"><div class="dd-info"><div class="dd-name" style="color:#9090aa">No cities found</div></div></div>`;
      dd.classList.add('open'); return;
    }
    dd.innerHTML = data.cities.map(c => `
      <div class="dropdown-item" onclick="selectCity('${c.name}','${c.code}')">
        <div class="dd-icon">📍</div>
        <div class="dd-info">
          <div class="dd-name">${c.name}</div>
          <div class="dd-meta">Kerala · ${c.code}</div>
        </div>
      </div>`).join('');
    dd.classList.add('open');
  } catch(e) { console.error(e); }
}

function selectCity(name, code) {
  selectedCity = {name, code};
  document.getElementById('cityInput').value = name;
  closeDD(document.getElementById('cityDropdown'));
  document.getElementById('theatreInput').disabled = false;
  document.getElementById('theatreNote').style.display = 'block';
  loadTheatresForCity();
}

// ── Theatre Search ────────────────────────────────────────────────────────────
function setupTheatreSearch() {
  const input = document.getElementById('theatreInput');
  const dd    = document.getElementById('theatreDropdown');
  input.addEventListener('input', () => {
    const q = input.value.trim().toLowerCase();
    renderTheatres(q ? allTheatres.filter(t => t.name.toLowerCase().includes(q)) : allTheatres);
  });
  input.addEventListener('focus', () => { if (allTheatres.length) renderTheatres(allTheatres); });
  document.addEventListener('click', e => {
    if (!input.contains(e.target) && !dd.contains(e.target)) closeDD(dd);
  });
}

async function loadTheatresForCity() {
  if (!selectedCity) return;
  const input = document.getElementById('theatreInput');
  const dd    = document.getElementById('theatreDropdown');
  input.placeholder = `Loading theatres in ${selectedCity.name}...`;
  dd.innerHTML = `<div class="dropdown-item"><div class="dd-icon">🎭</div><div class="dd-info"><div class="dd-name" style="color:#9090aa">Loading theatres...</div></div></div>`;
  dd.classList.add('open');
  try {
    const res  = await fetch(`${API}/api/search/theatres?city=${encodeURIComponent(selectedCity.name)}`);
    const data = await res.json();
    allTheatres = data.theatres || [];
    if (!allTheatres.length) {
      input.placeholder = 'No theatres found';
      dd.innerHTML = `<div class="dropdown-item"><div class="dd-info"><div class="dd-name" style="color:#9090aa">No theatres found for ${selectedCity.name}</div></div></div>`;
    } else {
      input.placeholder = `Search ${allTheatres.length} theatres in ${selectedCity.name}...`;
      renderTheatres(allTheatres);
    }
  } catch(e) { input.placeholder = 'Error loading theatres'; }
}

function renderTheatres(list) {
  const dd = document.getElementById('theatreDropdown');
  if (!list.length) {
    dd.innerHTML=`<div class="dropdown-item"><div class="dd-info"><div class="dd-name" style="color:#9090aa">No matching theatres</div></div></div>`;
    dd.classList.add('open'); return;
  }
  dd.innerHTML = list.map(t => `
    <div class="dropdown-item" onclick='selectTheatre(${JSON.stringify(t).replace(/'/g,"&#39;")})'>
      <div class="dd-icon">🎭</div>
      <div class="dd-info">
        <div class="dd-name">${t.name}</div>
        <div class="dd-meta">${t.area}</div>
      </div>
      <span class="maps-tag" onclick="event.stopPropagation();window.open('${t.maps_url}','_blank')">📍 Maps</span>
    </div>`).join('');
  dd.classList.add('open');
}

function selectTheatre(t) {
  selectedTheatre = t;
  document.getElementById('theatreInput').value = t.name;
  closeDD(document.getElementById('theatreDropdown'));
  document.getElementById('selectedTheatreName').textContent = t.name;
  document.getElementById('selectedTheatreArea').textContent = t.area;
  document.getElementById('mapsLink').href = t.maps_url || '#';
  document.getElementById('selectedTheatreBox').style.display = 'flex';
  document.getElementById('theatreNote').style.display = 'none';
}

function clearTheatre() {
  selectedTheatre = null;
  document.getElementById('theatreInput').value = '';
  document.getElementById('selectedTheatreBox').style.display = 'none';
  document.getElementById('theatreNote').style.display = 'block';
  if (allTheatres.length) renderTheatres(allTheatres);
}

// ── Start Monitor ─────────────────────────────────────────────────────────────
async function startMonitor() {
  if (!selectedMovie) { showToast('Please select a movie!', 'error'); return; }
  if (!selectedCity)  { showToast('Please select a city!', 'error'); return; }
  const btn = document.getElementById('startBtn');
  const msg = document.getElementById('statusMsg');
  btn.disabled = true; btn.innerHTML = '<span>⏳</span> Starting...'; msg.textContent = '';
  try {
    const res = await fetch(`${API}/api/monitor`, {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({
        movie_name: selectedMovie.name, movie_code: selectedMovie.code,
        movie_poster: selectedMovie.poster||'', city: selectedCity.name,
        theatre: selectedTheatre?.name||'', theatre_code: selectedTheatre?.code||'',
        theatre_url: selectedTheatre?.maps_url||'', maps_url: selectedTheatre?.maps_url||''
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail||'Error');
    showToast(`✅ Monitoring "${selectedMovie.name}"!`, 'success');
    msg.style.color='#2ecc71';
    msg.textContent = selectedTheatre
      ? `✅ Waiting for "${selectedTheatre.name}" booking to open! WhatsApp + call when it does.`
      : `✅ Monitoring all theatres in ${selectedCity.name}!`;
    // Reset
    clearMovie(); clearTheatre(); selectedCity=null; allTheatres=[];
    document.getElementById('cityInput').value='';
    document.getElementById('theatreInput').value='';
    document.getElementById('theatreInput').disabled=true;
    document.getElementById('theatreInput').placeholder='Select a city first...';
    document.getElementById('theatreNote').style.display='none';
    loadMonitors(); loadMovieCount();
  } catch(e) {
    showToast(e.message,'error'); msg.style.color='#e63946'; msg.textContent='❌ '+e.message;
  } finally {
    btn.disabled=false; btn.innerHTML='<span>🚀</span> Start Monitoring';
  }
}

// ── Monitors ──────────────────────────────────────────────────────────────────
async function loadMonitors() {
  const c = document.getElementById('monitorsContainer');
  try {
    const res  = await fetch(`${API}/api/monitors`);
    const data = await res.json();
    const list = data.monitors||[];
    if (!list.length) {
      c.innerHTML=`<div class="empty-state"><div class="empty-icon">🎯</div><p>No monitors yet.<br>Add a movie above!</p></div>`; return;
    }
    c.innerHTML = list.map(m => {
      const open = m.status==='opened';
      return `
        <div class="monitor-item ${m.status}">
          ${m.movie_poster
            ? `<img class="mon-poster" src="${m.movie_poster}" alt="${m.movie_name}" onerror="this.style.display='none'">`
            : `<div class="mon-poster" style="display:flex;align-items:center;justify-content:center;font-size:24px">🎬</div>`}
          <div class="mon-info">
            <div class="mon-title">${m.movie_name}</div>
            <div class="mon-meta">
              🏙️ ${m.city} &nbsp;·&nbsp; ${m.theatre?`🎭 ${m.theatre} &nbsp;·&nbsp;`:'🎭 Any Theatre &nbsp;·&nbsp;'}
              🕐 ${fmt(m.created_at)}${open?`<br>✅ Opened: ${fmt(m.opened_at)}`:''}
            </div>
            <div class="mon-actions">
              ${open
                ? `<span class="badge badge-opened">✅ BOOKING OPEN</span>
                   <a class="book-btn" href="${m.booking_url}" target="_blank">🎟️ Book Now</a>`
                : `<span class="badge badge-active badge-pulse">● Monitoring${m.theatre?' — Waiting for '+m.theatre:''}</span>`}
              ${m.status==='active'?`<button class="cancel-btn" onclick="cancelMonitor(${m.id})">Cancel</button>`:''}
            </div>
          </div>
        </div>`;
    }).join('');
  } catch(e) { c.innerHTML=`<div class="empty-state"><p style="color:#e63946">Could not connect to server.</p></div>`; }
}

async function cancelMonitor(id) {
  if (!confirm('Cancel this monitor?')) return;
  await fetch(`${API}/api/monitor/${id}`, {method:'DELETE'});
  showToast('Cancelled','success'); loadMonitors(); loadMovieCount();
}

// ── Logs ──────────────────────────────────────────────────────────────────────
async function loadLogs() {
  const c = document.getElementById('logsContainer');
  try {
    const res  = await fetch(`${API}/api/logs`);
    const data = await res.json();
    if (!data.logs||!data.logs.length) {
      c.innerHTML='<div class="empty-state"><p>No activity yet.</p></div>'; return;
    }
    c.innerHTML = data.logs.map(l => `
      <div class="log-item">
        <div class="log-time">${fmt(l.created_at)}</div>
        <div class="log-msg">${l.message}</div>
      </div>`).join('');
  } catch(e) { console.error(e); }
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function closeDD(el) { el.classList.remove('open'); el.innerHTML=''; }
function fmt(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleString('en-IN',{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'});
}
function showToast(msg, type='') {
  const t = document.getElementById('toast');
  t.textContent=msg; t.className=`toast ${type} show`;
  setTimeout(()=>{t.className='toast';}, 3500);
}
