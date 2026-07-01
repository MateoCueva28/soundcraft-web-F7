// ============================================================
// BÚSQUEDA EN TIEMPO REAL
// ============================================================
function initSearch() {
    const searchInput = document.getElementById('searchInput');
    if (!searchInput) return;

    const countEl = document.getElementById('recordCount');

    searchInput.addEventListener('keyup', function () {
        const filter = this.value.toLowerCase();
        const table = document.querySelector('.table tbody');
        if (!table) return;
        const rows = table.querySelectorAll('tr');

        let visible = 0;
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            const show = text.includes(filter);
            row.style.display = show ? '' : 'none';
            if (show && row.querySelector('td')) visible++;
        });

        if (countEl) {
            countEl.textContent = filter
                ? `${visible} resultado${visible !== 1 ? 's' : ''}`
                : `${rows.length} registros`;
        }
    });
}

// ============================================================
// MODAL DE CONFIRMACIÓN AL ELIMINAR
// ============================================================
function initDeleteModal() {
    const modal = document.getElementById('deleteModal');
    if (!modal) return;

    const confirmBtn = document.getElementById('confirmDelete');
    let deleteForm = null;

    document.querySelectorAll('.btn-delete-modal').forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            deleteForm = this.closest('form') || document.querySelector(this.dataset.form);
            const nombre = this.dataset.nombre || 'este elemento';
            document.getElementById('deleteModalName').textContent = nombre;
            modal.classList.add('active');
        });
    });

    confirmBtn.addEventListener('click', function () {
        if (deleteForm) deleteForm.submit();
    });

    document.getElementById('cancelDelete').addEventListener('click', function () {
        modal.classList.remove('active');
        deleteForm = null;
    });

    modal.addEventListener('click', function (e) {
        if (e.target === modal) {
            modal.classList.remove('active');
            deleteForm = null;
        }
    });
}

// ============================================================
// CHART.JS - PALETA DE COLORES
// ============================================================
const CHART_COLORS = [
    '#7B2CBF','#2ecc71','#f0a500','#e74c3c',
    '#3498db','#9b59b6','#1abc9c','#e67e22'
];

const CHART_GRID  = '#2a2a4e';
const CHART_TICKS = '#aaa';
const CHART_TEXT  = '#ccc';

// ============================================================
// CHART.JS - DASHBOARD
// ============================================================
function initDashboardCharts() {
    const topCancionesCtx = document.getElementById('topCancionesChart');
    if (topCancionesCtx && window.topCancionesData) {
        new Chart(topCancionesCtx, {
            type: 'bar',
            data: {
                labels: window.topCancionesData.labels,
                datasets: [{
                    label: 'Reproducciones',
                    data: window.topCancionesData.values,
                    backgroundColor: CHART_COLORS[0],
                    borderRadius: 6,
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: { color: CHART_TICKS }, grid: { color: CHART_GRID } },
                    y: { ticks: { color: CHART_TICKS }, grid: { color: CHART_GRID } }
                }
            }
        });
    }

    const paisCtx = document.getElementById('paisChart');
    if (paisCtx && window.paisData) {
        new Chart(paisCtx, {
            type: 'doughnut',
            data: {
                labels: window.paisData.labels,
                datasets: [{
                    data: window.paisData.values,
                    backgroundColor: [
                        '#7B2CBF','#e74c3c','#2ecc71','#f0a500',
                        '#3498db','#9b59b6','#1abc9c','#e67e22',
                        '#e91e63','#00bcd4'
                    ],
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'right', labels: { color: CHART_TEXT, padding: 10 } }
                }
            }
        });
    }
}

// ============================================================
// CHART.JS - REPORTES
// ============================================================
function initReportesCharts() {
    if (!window.REPORTES_DATA) return;
    var D = window.REPORTES_DATA;
    var ci = {};   // live Chart.js instances keyed by canvas id

    function kill(id) {
        if (ci[id]) { ci[id].destroy(); ci[id] = null; }
    }

    function toggle(canvasId, msgId, isEmpty) {
        var cv = document.getElementById(canvasId);
        var mg = document.getElementById(msgId);
        if (cv) cv.style.display = isEmpty ? 'none' : '';
        if (mg) mg.style.display = isEmpty ? '' : 'none';
    }

    function dateFilter(items, fechaKey, desde, hasta) {
        return items.filter(function(r) {
            var f = (r[fechaKey] || '').slice(0, 10);
            return (!desde || f >= desde) && (!hasta || f <= hasta);
        });
    }

    function groupCount(items, key) {
        var m = {};
        items.forEach(function(r) { m[r[key]] = (m[r[key]] || 0) + 1; });
        return Object.entries(m).sort(function(a, b) { return b[1] - a[1]; });
    }

    function groupSum(items, keyLabel, keyVal) {
        var m = {};
        items.forEach(function(r) {
            m[r[keyLabel]] = (m[r[keyLabel]] || 0) + Number(r[keyVal]);
        });
        return Object.entries(m).sort(function(a, b) { return b[1] - a[1]; });
    }

    function hBarOpts() {
        return {
            indexAxis: 'y',
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
                x: { ticks: { color: CHART_TICKS }, grid: { color: CHART_GRID } },
                y: { ticks: { color: CHART_TICKS }, grid: { color: CHART_GRID } }
            }
        };
    }

    // ── 1. REPRODUCCIONES POR PAÍS ──────────────────────────
    function drawRepPais() {
        var desde = (document.getElementById('repDesde') || {}).value || '';
        var hasta = (document.getElementById('repHasta') || {}).value || '';
        var rows = dateFilter(D.repros, 'fecha', desde, hasta);
        var sorted = groupCount(rows, 'pais');
        kill('repPaisChart');
        if (!sorted.length) { toggle('repPaisChart', 'repNoData', true); return; }
        toggle('repPaisChart', 'repNoData', false);
        ci['repPaisChart'] = new Chart(document.getElementById('repPaisChart'), {
            type: 'bar',
            data: {
                labels: sorted.map(function(e) { return e[0]; }),
                datasets: [{ label: 'Reproducciones', data: sorted.map(function(e) { return e[1]; }),
                    backgroundColor: CHART_COLORS[0], borderRadius: 6 }]
            },
            options: hBarOpts()
        });
    }

    var repDesde = document.getElementById('repDesde');
    if (repDesde) {
        repDesde.addEventListener('change', drawRepPais);
        document.getElementById('repHasta').addEventListener('change', drawRepPais);
        drawRepPais();
    }

    // ── 2. INGRESOS POR MÉTODO DE PAGO ─────────────────────
    function drawIngresos() {
        var desde = (document.getElementById('ingDesde') || {}).value || '';
        var hasta = (document.getElementById('ingHasta') || {}).value || '';
        var rows = dateFilter(D.pagos, 'fecha', desde, hasta);
        var sorted = groupSum(rows, 'metodo', 'monto');
        kill('ingresosChart');
        if (!sorted.length) { toggle('ingresosChart', 'ingNoData', true); return; }
        toggle('ingresosChart', 'ingNoData', false);
        ci['ingresosChart'] = new Chart(document.getElementById('ingresosChart'), {
            type: 'pie',
            data: {
                labels: sorted.map(function(e) { return e[0]; }),
                datasets: [{ data: sorted.map(function(e) { return Math.round(e[1] * 100) / 100; }),
                    backgroundColor: CHART_COLORS.slice(0, sorted.length) }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'right', labels: { color: CHART_TEXT, padding: 10 } },
                    tooltip: { callbacks: { label: function(c) {
                        return c.label + ': $' + c.parsed.toFixed(2);
                    }}}
                }
            }
        });
    }

    var ingDesde = document.getElementById('ingDesde');
    if (ingDesde) {
        ingDesde.addEventListener('change', drawIngresos);
        document.getElementById('ingHasta').addEventListener('change', drawIngresos);
        drawIngresos();
    }

    // ── 3. SUSCRIPCIONES POR PLAN ───────────────────────────
    var sussEstadoEl = document.getElementById('sussEstado');
    if (sussEstadoEl && D.suscripciones.length) {
        var estadosSet = Array.from(new Set(D.suscripciones.map(function(s) {
            return s.estado;
        }).filter(Boolean))).sort();
        ['Todas'].concat(estadosSet).forEach(function(e) {
            var o = document.createElement('option');
            o.value = e === 'Todas' ? '' : e;
            o.textContent = e;
            sussEstadoEl.appendChild(o);
        });
    }

    function drawSuscripciones() {
        var desde  = (document.getElementById('sussDesde') || {}).value || '';
        var hasta  = (document.getElementById('sussHasta') || {}).value || '';
        var estado = (document.getElementById('sussEstado') || {}).value || '';
        var rows = dateFilter(D.suscripciones, 'fecha', desde, hasta);
        if (estado) rows = rows.filter(function(s) { return s.estado === estado; });
        var sorted = groupCount(rows, 'plan');
        kill('suscripcionesChart');
        if (!sorted.length) { toggle('suscripcionesChart', 'sussNoData', true); return; }
        toggle('suscripcionesChart', 'sussNoData', false);
        ci['suscripcionesChart'] = new Chart(document.getElementById('suscripcionesChart'), {
            type: 'doughnut',
            data: {
                labels: sorted.map(function(e) { return e[0]; }),
                datasets: [{ data: sorted.map(function(e) { return e[1]; }),
                    backgroundColor: CHART_COLORS.slice(0, sorted.length) }]
            },
            options: {
                responsive: true,
                plugins: { legend: { position: 'bottom', labels: { color: CHART_TEXT } } }
            }
        });
    }

    var sussDesde = document.getElementById('sussDesde');
    if (sussDesde) {
        sussDesde.addEventListener('change', drawSuscripciones);
        document.getElementById('sussHasta').addEventListener('change', drawSuscripciones);
        if (sussEstadoEl) sussEstadoEl.addEventListener('change', drawSuscripciones);
        drawSuscripciones();
    }

    // ── 4. REGALÍAS POR ARTISTA ─────────────────────────────
    var regPeriodoEl = document.getElementById('regPeriodo');
    var regArtistaEl = document.getElementById('regArtista');

    if (regPeriodoEl && D.regalias && D.regalias.length) {
        var periodos = Array.from(new Set(D.regalias.map(function(r) {
            return r.periodo;
        }).filter(Boolean))).sort().reverse();
        periodos.forEach(function(p) {
            var o = document.createElement('option');
            o.value = o.textContent = p;
            regPeriodoEl.appendChild(o);
        });

        var artistas = Array.from(new Set(D.regalias.map(function(r) {
            return r.artista;
        }).filter(Boolean))).sort();
        var todosOpt = document.createElement('option');
        todosOpt.value = ''; todosOpt.textContent = 'Todos';
        regArtistaEl.appendChild(todosOpt);
        artistas.forEach(function(a) {
            var o = document.createElement('option');
            o.value = o.textContent = a;
            regArtistaEl.appendChild(o);
        });

        function drawRegalias() {
            var periodo = regPeriodoEl.value;
            var artista = regArtistaEl.value;
            var rows = D.regalias.filter(function(r) {
                return (!periodo || r.periodo === periodo) &&
                       (!artista || r.artista === artista);
            });
            var sorted = groupSum(rows, 'artista', 'repros');
            var montos = sorted.map(function(e) { return Math.round(e[1] * 0.004 * 100) / 100; });
            kill('regaliasChart');
            if (!sorted.length) { toggle('regaliasChart', 'regNoData', true); return; }
            toggle('regaliasChart', 'regNoData', false);
            var opts = hBarOpts();
            opts.scales.x.ticks.callback = function(v) { return '$' + v; };
            ci['regaliasChart'] = new Chart(document.getElementById('regaliasChart'), {
                type: 'bar',
                data: {
                    labels: sorted.map(function(e) { return e[0]; }),
                    datasets: [{ label: 'Monto Est. ($)', data: montos,
                        backgroundColor: CHART_COLORS[2], borderRadius: 6 }]
                },
                options: opts
            });
        }

        regPeriodoEl.addEventListener('change', drawRegalias);
        regArtistaEl.addEventListener('change', drawRegalias);
        drawRegalias();
    } else if (regPeriodoEl) {
        toggle('regaliasChart', 'regNoData', true);
    }
}

// ============================================================
// NAVBAR TOGGLE (RESPONSIVE)
// ============================================================
function initNavbarToggle() {
    const toggle = document.getElementById('navbarToggle');
    const menu = document.getElementById('navbarMenu');
    if (!toggle || !menu) return;

    toggle.addEventListener('click', function (e) {
        e.stopPropagation();
        menu.classList.toggle('open');
    });

    document.addEventListener('click', function (e) {
        if (!toggle.contains(e.target) && !menu.contains(e.target)) {
            menu.classList.remove('open');
        }
    });
}

// ============================================================
// UTILIDADES COMPARTIDAS (playlists + canciones)
// ============================================================

// Convierte "HH:MM:SS" a "m:ss"
function fmtDur(str) {
    if (!str) return '—';
    var p = str.trim().split(':');
    if (p.length !== 3) return str;
    var totalMin = parseInt(p[0], 10) * 60 + parseInt(p[1], 10);
    var s = parseInt(p[2], 10);
    return totalMin + ':' + (s < 10 ? '0' : '') + s;
}

// ============================================================
// CANCIONES — MODAL DE DETALLE
// ============================================================
function onCancionClick(idStr) {
    if (!window.CANCIONES_DATA) return;
    var data = null;
    for (var i = 0; i < window.CANCIONES_DATA.length; i++) {
        if (window.CANCIONES_DATA[i].id === idStr) { data = window.CANCIONES_DATA[i]; break; }
    }
    if (data) openCkModal(data);
}

function openCkModal(data) {
    var overlay = document.getElementById('ckModal');
    if (!overlay) return;

    document.getElementById('ckModalCover').style.background  = plColor(data.idInt);
    document.getElementById('ckModalTitle').textContent       = data.tituloCancion;
    document.getElementById('ckModalArtist').textContent      = data.albumArtista || '—';
    document.getElementById('ckModalAlbum').textContent       = data.albumTitulo  || '—';
    document.getElementById('ckModalPista').textContent       = data.numeroPistaCancion || '—';
    document.getElementById('ckModalDur').textContent         = fmtDur(data.duracionCancion);

    var generosEl = document.getElementById('ckModalGeneros');
    generosEl.innerHTML = '';
    if (data.generos && data.generos.length) {
        data.generos.forEach(function(g) {
            var span = document.createElement('span');
            span.className   = 'badge badge-info';
            span.textContent = g;
            generosEl.appendChild(span);
        });
    } else {
        generosEl.innerHTML = '<span style="color:var(--color-text-dim)">—</span>';
    }

    var estadoEl = document.getElementById('ckModalEstado');
    estadoEl.textContent = data.estadoCancion;
    estadoEl.className   = 'badge ' + (data.estadoCancion === 'Publicada' ? 'badge-success' : 'badge-danger');

    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function initCkModal() {
    var overlay = document.getElementById('ckModal');
    if (!overlay) return;
    var closeBtn = document.getElementById('ckModalClose');

    function closeCkModal() {
        overlay.classList.remove('active');
        document.body.style.overflow = '';
    }

    closeBtn.addEventListener('click', closeCkModal);
    overlay.addEventListener('click', function(e) { if (e.target === overlay) closeCkModal(); });
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && overlay.classList.contains('active')) closeCkModal();
    });
}

// ============================================================
// CANCIONES — TRACK LIST
// ============================================================

function initCancionesTrackList() {
    var container = document.getElementById('tkRows');
    if (!container) return;

    var rows      = Array.from(container.querySelectorAll('.tk-row'));
    var noResults = document.getElementById('tkNoResults');
    var countEl   = document.getElementById('recordCount');
    var searchEl  = document.getElementById('searchInput');

    // Aplicar colores, formatear duración y fecha
    rows.forEach(function(row) {
        var idInt = parseInt(row.dataset.id, 10) || 0;
        var cover = row.querySelector('.tk-cover');
        if (cover) cover.style.background = plColor(idInt);

        var durEl = row.querySelector('.tk-dur');
        if (durEl) durEl.textContent = fmtDur(durEl.textContent);

        var dateEl = row.querySelector('.tk-album-date');
        if (dateEl && dateEl.textContent.trim()) {
            dateEl.textContent = plFmtFecha(dateEl.textContent.trim());
        }
    });

    // Stub click — data-id disponible para el modal futuro
    rows.forEach(function(row) {
        row.addEventListener('click', function()  { onCancionClick(row.dataset.id); });
        row.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') onCancionClick(row.dataset.id);
        });
    });

    // Búsqueda por título O artista
    if (searchEl) {
        searchEl.addEventListener('keyup', function() {
            var filter  = this.value.toLowerCase().trim();
            var visible = 0;
            rows.forEach(function(row) {
                var match = !filter ||
                    row.dataset.titulo.toLowerCase().includes(filter) ||
                    row.dataset.artista.toLowerCase().includes(filter);
                row.style.display = match ? '' : 'none';
                if (match) visible++;
            });
            if (noResults) noResults.style.display = (visible === 0 && filter) ? '' : 'none';
            if (countEl) {
                countEl.textContent = filter
                    ? visible + ' resultado' + (visible !== 1 ? 's' : '')
                    : rows.length + ' registros';
            }
        });
    }
}

// ============================================================
// PLAYLISTS — GRID + MODAL DE DETALLE
// ============================================================

// Gradiente determinístico por _id entero — misma paleta para card y modal
function plColor(idInt) {
    const PALETA = [
        ['#6d28d9','#4c1d95'],
        ['#0f766e','#134e4a'],
        ['#be185d','#831843'],
        ['#c2410c','#7c2d12'],
        ['#1d4ed8','#1e3a8a'],
        ['#15803d','#14532d'],
        ['#b45309','#78350f'],
        ['#0e7490','#164e63'],
    ];
    const pair = PALETA[((idInt % 8) + 8) % 8];
    return 'linear-gradient(135deg,' + pair[0] + ' 0%,' + pair[1] + ' 100%)';
}

function plFmtFecha(str) {
    if (!str) return '—';
    const m = str.match(/^(\d{4})-(\d{2})-(\d{2})/);
    return m ? m[3] + '/' + m[2] + '/' + m[1] : str;
}

function initPlaylistGrid() {
    var grid = document.getElementById('plGrid');
    if (!grid || !window.PLAYLISTS_DATA) return;

    var overlay    = document.getElementById('plModal');
    var closeBtn   = document.getElementById('plModalClose');
    var noResults  = document.getElementById('plNoResults');
    var countEl    = document.getElementById('recordCount');
    var searchEl   = document.getElementById('searchInput');
    var deleteForm = document.getElementById('plDeleteForm');
    var toggleBtn  = document.getElementById('plModalToggle');
    var delBtn     = document.getElementById('plModalDelete');

    var cards      = Array.from(grid.querySelectorAll('.pl-card'));
    var currentIdx = -1;

    // ── CSRF ─────────────────────────────────────────────────
    function getCsrf() {
        var m = document.cookie.match(/csrftoken=([^;]+)/);
        return m ? m[1] : '';
    }

    // ── COLORES ───────────────────────────────────────────────
    cards.forEach(function(card) {
        var idx  = parseInt(card.dataset.idx, 10);
        var data = window.PLAYLISTS_DATA[idx];
        if (data) card.querySelector('.pl-cover').style.background = plColor(data.idInt);
    });

    // ── BADGE Y BOTÓN DE ESTADO ──────────────────────────────
    function setStateBadge(estado) {
        var badge = document.getElementById('plModalBadge');
        if (!badge) return;
        badge.textContent = estado;
        badge.className = 'badge pl-modal-badge ' + (estado === 'Activa' ? 'badge-success' : 'badge-warning');
    }

    function setToggleBtn(estado) {
        if (!toggleBtn) return;
        if (estado === 'Activa') {
            toggleBtn.innerHTML = '<i class="fas fa-ban"></i> Suspender playlist';
            toggleBtn.className = 'btn btn-warning';
        } else {
            toggleBtn.innerHTML = '<i class="fas fa-circle-check"></i> Activar playlist';
            toggleBtn.className = 'btn btn-primary';
        }
        toggleBtn.disabled = false;
    }

    // ── ABRIR MODAL ───────────────────────────────────────────
    function openModal(card) {
        currentIdx   = parseInt(card.dataset.idx, 10);
        var data     = window.PLAYLISTS_DATA[currentIdx];
        if (!data) return;

        document.getElementById('plModalCover').style.background = plColor(data.idInt);
        document.getElementById('plModalTitle').textContent      = data.nombrePlaylist;

        var n = data.canciones.length;
        document.getElementById('plModalSub').textContent =
            'De ' + data.nombreUsuario + ' · ' + n + ' canción' + (n !== 1 ? 'es' : '');

        setStateBadge(data.estadoPlaylist);
        setToggleBtn(data.estadoPlaylist);

        if (deleteForm) deleteForm.action = '/playlists/eliminar/' + data.id + '/';
        if (delBtn)     delBtn.dataset.nombre = data.nombrePlaylist;

        // Tracklist
        var tbody = document.getElementById('plModalBody');
        tbody.innerHTML = '';
        if (n === 0) {
            tbody.innerHTML = '<tr><td colspan="3" style="text-align:center;color:var(--color-text-dim);padding:1.2rem">Sin canciones agregadas</td></tr>';
        } else {
            data.canciones.forEach(function(c, i) {
                var tr = document.createElement('tr');
                tr.innerHTML =
                    '<td style="color:var(--color-text-dim);width:36px;text-align:right;padding-right:1rem">' + (i + 1) + '</td>' +
                    '<td>' + (c.tituloCancion || '—') + '</td>' +
                    '<td style="color:var(--color-text-dim)">' + plFmtFecha(c.fechaAgregada) + '</td>';
                tbody.appendChild(tr);
            });
        }

        overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeModal() {
        overlay.classList.remove('active');
        document.body.style.overflow = '';
    }

    // ── LISTENERS DE TARJETAS ─────────────────────────────────
    cards.forEach(function(card) {
        card.addEventListener('click',   function()  { openModal(card); });
        card.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openModal(card); }
        });
    });

    // ── CERRAR ────────────────────────────────────────────────
    closeBtn.addEventListener('click', closeModal);
    overlay.addEventListener('click',  function(e) { if (e.target === overlay) closeModal(); });
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && overlay.classList.contains('active')) closeModal();
    });

    // ── ELIMINAR — texto de moderación personalizado ──────────
    if (delBtn) {
        delBtn.addEventListener('click', function() {
            var data  = window.PLAYLISTS_DATA[currentIdx];
            var msgEl = document.querySelector('#deleteModal .modal-box p');
            if (msgEl && data) {
                window._plOrigDeleteMsg = msgEl.innerHTML;
                msgEl.innerHTML = 'Esta playlist pertenece a <strong>' + data.nombreUsuario +
                    '</strong>. ¿Confirmas que quieres eliminarla?';
            }
            closeModal();
        });
    }

    // Restaurar el texto genérico al cancelar la eliminación
    var cancelBtn = document.getElementById('cancelDelete');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function() {
            if (window._plOrigDeleteMsg) {
                var msgEl = document.querySelector('#deleteModal .modal-box p');
                if (msgEl) msgEl.innerHTML = window._plOrigDeleteMsg;
                window._plOrigDeleteMsg = null;
            }
        });
    }

    // ── CAMBIAR ESTADO (fetch sin recarga) ────────────────────
    if (toggleBtn) {
        toggleBtn.addEventListener('click', function() {
            if (currentIdx < 0) return;
            var data = window.PLAYLISTS_DATA[currentIdx];
            toggleBtn.disabled  = true;
            toggleBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Guardando...';

            fetch('/playlists/cambiar-estado/' + data.id + '/', {
                method:  'POST',
                headers: { 'X-CSRFToken': getCsrf(), 'X-Requested-With': 'XMLHttpRequest' },
            })
            .then(function(r) { return r.json(); })
            .then(function(resp) {
                if (resp.estadoPlaylist) {
                    window.PLAYLISTS_DATA[currentIdx].estadoPlaylist = resp.estadoPlaylist;
                    setStateBadge(resp.estadoPlaylist);
                    setToggleBtn(resp.estadoPlaylist);
                    // Actualizar punto en la tarjeta del grid
                    var card = grid.querySelector('.pl-card[data-idx="' + currentIdx + '"]');
                    if (card) {
                        var dot = card.querySelector('.pl-dot');
                        if (dot) dot.classList.toggle('pl-dot--active', resp.estadoPlaylist === 'Activa');
                    }
                } else {
                    setToggleBtn(data.estadoPlaylist);
                }
            })
            .catch(function() { setToggleBtn(window.PLAYLISTS_DATA[currentIdx].estadoPlaylist); });
        });
    }

    // ── BÚSQUEDA ──────────────────────────────────────────────
    if (searchEl) {
        searchEl.addEventListener('keyup', function() {
            var filter  = this.value.toLowerCase().trim();
            var visible = 0;
            cards.forEach(function(card) {
                var match = card.dataset.nombre.toLowerCase().includes(filter);
                card.style.display = match ? '' : 'none';
                if (match) visible++;
            });
            if (noResults) noResults.style.display = (visible === 0 && filter) ? '' : 'none';
            if (countEl) {
                countEl.textContent = filter
                    ? visible + ' resultado' + (visible !== 1 ? 's' : '')
                    : cards.length + ' registros';
            }
        });
    }
}

// ============================================================
// INIT
// ============================================================
document.addEventListener('DOMContentLoaded', function () {
    initSearch();
    initDeleteModal();
    initDashboardCharts();
    initReportesCharts();
    initNavbarToggle();
    initPlaylistGrid();
    initCancionesTrackList();
    initCkModal();
});