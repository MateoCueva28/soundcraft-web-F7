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
    '#7B2CBF','#9B4CD9','#5e1fa0','#b56de8',
    '#4a1880','#c98df0','#3d1266','#d4a8f5',
    '#2c0d4d','#e0c3fa'
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
    const repPaisCtx = document.getElementById('repPaisChart');
    if (repPaisCtx && window.repPaisData) {
        new Chart(repPaisCtx, {
            type: 'bar',
            data: {
                labels: window.repPaisData.labels,
                datasets: [{
                    label: 'Reproducciones',
                    data: window.repPaisData.values,
                    backgroundColor: CHART_COLORS[0],
                    borderRadius: 6,
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: { color: CHART_TICKS }, grid: { color: CHART_GRID } },
                    y: { ticks: { color: CHART_TICKS }, grid: { color: CHART_GRID } }
                }
            }
        });
    }

    const ingresosCtx = document.getElementById('ingresosChart');
    if (ingresosCtx && window.ingresosData) {
        new Chart(ingresosCtx, {
            type: 'pie',
            data: {
                labels: window.ingresosData.labels,
                datasets: [{
                    data: window.ingresosData.values,
                    backgroundColor: ['#7B2CBF', '#2ecc71', '#f0a500', '#3498db'],
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'bottom', labels: { color: CHART_TEXT } }
                }
            }
        });
    }

    const suscripcionesCtx = document.getElementById('suscripcionesChart');
    if (suscripcionesCtx && window.suscripcionesData) {
        new Chart(suscripcionesCtx, {
            type: 'doughnut',
            data: {
                labels: window.suscripcionesData.labels,
                datasets: [{
                    data: window.suscripcionesData.values,
                    backgroundColor: [
                        '#7B2CBF','#e74c3c','#2ecc71',
                        '#f0a500','#3498db','#9b59b6'
                    ],
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'bottom', labels: { color: CHART_TEXT } }
                }
            }
        });
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
// INIT
// ============================================================
document.addEventListener('DOMContentLoaded', function () {
    initSearch();
    initDeleteModal();
    initDashboardCharts();
    initReportesCharts();
    initNavbarToggle();
});