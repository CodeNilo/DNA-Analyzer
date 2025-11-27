// ===== STATE =====
const API_BASE =
  window.API_BASE_URL ||
  (window.location.origin && !window.location.origin.startsWith('file:')
    ? `${window.location.origin}/api`
    : 'http://localhost:8000/api');
let isFileUploaded = false;
let uploadedSequence = null;
let vizCanvas = null;
let vizCtx = null;
let vizWidth = 0;
let vizHeight = 0;
let vizAnimationId = null;
let vizTime = 0;

// Datos de visualización
let vizData = {
    sequenceLength: 0,
    gcContent: 0,
    matches: [],
    algorithm: null,
    searchTime: null,
    isSearching: false,
    dnaStrands: [],
    particles: [],
    pulseRings: [],
    dataPoints: []
};

// ===== HISTORIAL CON LOCALSTORAGE =====
const HISTORY_KEY = 'dna_analyzer_history';
const MAX_HISTORY_ITEMS = 50;

function getHistory() {
    try {
        const data = localStorage.getItem(HISTORY_KEY);
        return data ? JSON.parse(data) : [];
    } catch (e) {
        console.error('Error reading history:', e);
        return [];
    }
}

function saveHistory(history) {
    try {
        localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
    } catch (e) {
        console.error('Error saving history:', e);
    }
}

function addToHistory(entry) {
    const history = getHistory();
    history.unshift({
        id: Date.now(),
        timestamp: new Date().toISOString(),
        ...entry
    });
    // Limitar el historial
    if (history.length > MAX_HISTORY_ITEMS) {
        history.pop();
    }
    saveHistory(history);
    renderHistory();
}

function clearHistory() {
    if (confirm('¿Estas seguro de que quieres limpiar todo el historial?')) {
        localStorage.removeItem(HISTORY_KEY);
        renderHistory();
        showToast('Historial limpiado');
    }
}

function formatTimeAgo(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Ahora mismo';
    if (diffMins < 60) return `Hace ${diffMins} min`;
    if (diffHours < 24) return `Hace ${diffHours} hora${diffHours > 1 ? 's' : ''}`;
    if (diffDays < 7) return `Hace ${diffDays} dia${diffDays > 1 ? 's' : ''}`;
    return date.toLocaleDateString('es-ES');
}

function renderHistory() {
    const container = document.getElementById('historyList');
    const emptyMsg = document.getElementById('historyEmpty');
    if (!container) return;
    
    const history = getHistory();
    
    // Limpiar contenedor pero mantener el mensaje vacío
    container.innerHTML = '';
    
    if (history.length === 0) {
        container.innerHTML = `
            <div class="history-empty" id="historyEmpty">
                <i class="ri-inbox-line"></i>
                <p>No hay registros de sesiones</p>
                <small>Las busquedas realizadas apareceran aqui</small>
            </div>
        `;
        return;
    }
    
    history.forEach(item => {
        const isError = item.status === 'error';
        const statusClass = isError ? 'error' : '';
        const statusText = isError ? 'ERR' : 'OK';
        const iconClass = isError ? 'ri-file-warning-line' : 'ri-search-line';
        
        const itemHtml = `
            <div class="history-item" data-id="${item.id}">
                <div class="h-icon ${statusClass}"><i class="${iconClass}"></i></div>
                <div class="h-info">
                    <h4>${item.pattern ? `Patron: ${item.pattern.toUpperCase()}` : item.fileName || 'Sin nombre'}</h4>
                    <small>${formatTimeAgo(item.timestamp)} • ${item.matches !== undefined ? item.matches + ' coincidencias' : item.message || 'Completado'}</small>
                </div>
                <span class="h-status ${statusClass}">${statusText}</span>
            </div>
        `;
        container.innerHTML += itemHtml;
    });
}

// ===== DNA ANIMATION (COSMIC EDITION) =====
function initDNA() {
    const container = document.getElementById('dnaHelix');
    const wrapper = document.getElementById('dnaContainer');
    if (!container) return;
    
    container.innerHTML = '';
    
    const pairCount = 40;
    const pairs = [];
    
    for (let i = 0; i < pairCount; i++) {
        const pair = document.createElement('div');
        pair.className = 'base-pair';
        
        const left = document.createElement('div');
        left.className = 'nucleotide left';
        
        const right = document.createElement('div');
        right.className = 'nucleotide right';
        
        const connector = document.createElement('div');
        connector.className = 'connector';
        
        pair.appendChild(left);
        pair.appendChild(connector);
        pair.appendChild(right);
        container.appendChild(pair);
        
        pairs.push({ el: pair, index: i, left, right, connector });
    }
    
    for (let i = 0; i < 25; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.left = `${Math.random() * 100}%`;
        particle.style.top = `${Math.random() * 100}%`;
        const size = 2 + Math.random() * 4;
        particle.style.width = `${size}px`;
        particle.style.height = `${size}px`;
        particle.style.animationDelay = `${Math.random() * 6}s`;
        particle.style.background = Math.random() > 0.5 ? 'var(--purple-core)' : 'var(--cyan-accent)';
        wrapper.appendChild(particle);
    }
    
    let time = 0;
    function animate() {
        time += 0.008;
        
        pairs.forEach((pair, i) => {
            const y = (i / pairCount) * 100;
            const rotation = (i * 0.4) + (time * 2);
            
            const radius = 80;
            const leftX = Math.cos(rotation) * radius;
            const z = Math.sin(rotation) * radius;
            const rightX = Math.cos(rotation + Math.PI) * radius;
            
            pair.el.style.top = `${y}%`;
            
            pair.left.style.transform = `translateX(${leftX}px) translateZ(${z}px)`;
            pair.right.style.transform = `translateX(${rightX}px) translateZ(${-z}px)`;
            
            const depthScale = 0.6 + ((z + radius) / (radius * 2)) * 0.4;
            pair.left.style.transform += ` scale(${depthScale})`;
            pair.right.style.transform += ` scale(${1.2 - depthScale + 0.4})`;
            
            const connectorWidth = Math.abs(leftX - rightX);
            pair.connector.style.width = `${connectorWidth}px`;
            pair.connector.style.left = `calc(50% - ${connectorWidth / 2}px)`;
            pair.connector.style.opacity = 0.1 + (Math.abs(Math.cos(rotation)) * 0.4);
        });
        
        requestAnimationFrame(animate);
    }
    animate();
}

// ===== NAVIGATION & LOGIC =====
function switchView(viewId) {
    if (!isFileUploaded && !['upload', 'history'].includes(viewId)) {
        showToast('⚠️ Acceso Denegado: Importa una secuencia primero', 'error');
        return;
    }
    
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.getElementById('view' + viewId.charAt(0).toUpperCase() + viewId.slice(1)).classList.add('active');
    
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.view === viewId) btn.classList.add('active');
    });
}

document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => switchView(btn.dataset.view));
});

// ===== UPLOAD LOGIC =====
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');

dropZone.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', (e) => { if (e.target.files.length) handleUpload(e.target.files[0]); });

async function handleUpload(file) {
    const icon = dropZone.querySelector('.upload-icon');
    const title = dropZone.querySelector('.upload-title');
    const subtitle = dropZone.querySelector('.upload-subtitle');
    
    icon.innerHTML = '<i class="ri-loader-4-line loader"></i>';
    title.textContent = 'ANALIZANDO...';
    if (subtitle) subtitle.textContent = 'Procesando archivo...';

    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', file.name);

    try {
        const res = await fetch(`${API_BASE}/sequences/upload/`, {
            method: 'POST',
            body: formData,
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || JSON.stringify(err));
        }

        const data = await res.json();
        uploadedSequence = data;
        isFileUploaded = true;

        document.querySelectorAll('.nav-btn.locked').forEach(btn => btn.classList.remove('locked'));
        
        document.getElementById('fileName').textContent = data.name?.toUpperCase() || file.name.toUpperCase();
        document.getElementById('statChars').textContent = (data.length || 0).toLocaleString();
        // document.getElementById('statBP').textContent = (data.length || 0).toLocaleString();
        const gcVal = typeof data.gc_content === 'number' ? data.gc_content : null;
        document.getElementById('statGC').textContent = gcVal !== null ? `${gcVal.toFixed(2)}%` : '---';
        
        document.getElementById('statusDot').className = 'status-dot active-dot';
        document.getElementById('statusText').textContent = 'SISTEMA ACTIVO';
        
        // Actualizar visualización con datos de secuencia
        vizData.sequenceLength = data.length || 0;
        vizData.gcContent = gcVal || 0;
        initSequenceVisualization();
        
        showToast('Secuencia importada correctamente');
        switchView('dashboard');
        
        setTimeout(() => {
            icon.innerHTML = '<i class="ri-check-line"></i>';
            title.textContent = 'Archivo Cargado';
        }, 500);
    } catch (error) {
        console.error(error);
        icon.innerHTML = '<i class="ri-add-line"></i>';
        title.textContent = 'Importar Secuencia';
        showToast(`Error al cargar: ${error.message}`, 'error');
    }
}

// ===== SEARCH LOGIC =====
function setPattern(val) { document.getElementById('patternInput').value = val; }

async function runSearch() {
    const val = document.getElementById('patternInput').value;
    if(!val) return showToast('Ingrese un patron', 'error');
    if(!uploadedSequence?.id) return showToast('Carga una secuencia antes de buscar', 'error');

    document.getElementById('resPattern').innerText = val.toUpperCase();
    document.getElementById('resMatches').innerText = '...';
    document.getElementById('genomeTrack').innerHTML = '';
    document.getElementById('resultsTableBody').innerHTML = '';

    vizData.isSearching = true;
    switchView('results');

    try {
        const res = await fetch(`${API_BASE}/search/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sequence_id: uploadedSequence.id,
                pattern: val,
                allow_overlapping: true,
            }),
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || JSON.stringify(err));
        }

        const data = await res.json();
        vizData.isSearching = false;
        renderResults(data, uploadedSequence.length);
        
        // Guardar en historial
        const job = data.job || {};
        const results = data.results || [];
        addToHistory({
            type: 'search',
            pattern: val,
            fileName: uploadedSequence.name || 'Secuencia',
            matches: job.total_matches ?? results.length,
            algorithm: job.algorithm_used || data.algorithm_used || 'naive-local',
            searchTime: data.end_to_end_ms ?? job.search_time_ms ?? data.search_time_ms,
            status: 'success'
        });
        
        showToast('Busqueda completada');
    } catch (error) {
        console.error(error);
        vizData.isSearching = false;
        
        // Guardar error en historial
        addToHistory({
            type: 'search',
            pattern: val,
            fileName: uploadedSequence?.name || 'Secuencia',
            message: error.message,
            status: 'error'
        });
        
        showToast(`Error en busqueda: ${error.message}`, 'error');
    }
}

function renderResults(data, seqLength = 0) {
    const job = data.job || {};
    const results = data.results || [];

    const displayAlgo = (algo) => {
        if (!algo) return 'N/A';
        return algo === 'naive-local' ? 'Busqueda Ingenua' : algo;
    };

    document.getElementById('resPattern').innerText = job.pattern?.toUpperCase() || '---';
    document.getElementById('resMatches').innerText = job.total_matches ?? results.length;
    
    const algoRaw = job.algorithm_used || data.algorithm_used || 'naive-local';
    const algo = displayAlgo(algoRaw);
    const isGrpc = algoRaw && algoRaw !== 'naive-local';
    const timeMsGrpc = isGrpc ? (job.search_time_ms ?? data.search_time_ms) : null;
    const totalMs = data.end_to_end_ms ?? job.search_time_ms ?? data.search_time_ms;
    const perfLabel = totalMs ? `${totalMs.toFixed(2)} ms (${algo})` : algo;
    const perfEl = document.getElementById('statusText');
    if (perfEl) perfEl.textContent = perfLabel;
    const algoEl = document.getElementById('statAlgo');
    if (algoEl) algoEl.textContent = algo;
    const grpcEl = document.getElementById('resTimeGrpc');
    const timeLabelEl = document.getElementById('resTimeLabel');
    if (timeLabelEl) timeLabelEl.textContent = isGrpc ? 'TIEMPO gRPC' : 'TIEMPO HTTP';
    if (grpcEl) {
        const showMs = isGrpc ? timeMsGrpc : totalMs;
        grpcEl.textContent = showMs ? `${showMs.toFixed(2)} ms` : '---';
    }
    const totalEl = document.getElementById('resTimeTotal');
    if (totalEl) {
        const totalSec = totalMs ? totalMs / 1000 : null;
        totalEl.textContent = totalSec ? `${totalSec.toFixed(3)} s` : '---';
    }
    
    // Actualizar datos de visualización
    vizData.matches = results;
    vizData.algorithm = algoRaw;
    vizData.searchTime = totalMs;
    updateVisualizationWithResults();

    // Mapa de densidad
    const track = document.getElementById('genomeTrack');
    track.innerHTML = '';
    results.forEach((r) => {
        const pct = seqLength ? (r.position / seqLength) * 100 : Math.random() * 98;
        const mark = document.createElement('div');
        mark.className = 'match-mark';
        mark.style.left = Math.min(98, pct) + '%';
        track.appendChild(mark);
    });

    // Tabla
    const tbody = document.getElementById('resultsTableBody');
    tbody.innerHTML = '';
    results.slice(0, 50).forEach((r, idx) => {
        tbody.innerHTML += `
            <tr>
                <td>#${idx + 1}</td>
                <td style="color:var(--cyan-accent)">${r.position}</td>
                <td style="font-family:monospace; color:var(--text-muted)">...${r.context_before || ''}<span style="color:#fff; font-weight:bold">${job.pattern?.toUpperCase() || ''}</span>${r.context_after || ''}...</td>
                <td>${algo}</td>
            </tr>
        `;
    });
}

// ===== TOAST =====
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    document.getElementById('toastMessage').textContent = message;
    if(type === 'error') toast.classList.add('error'); else toast.classList.remove('error');
    
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3000);
}

// ===== VISUALIZACIÓN 3D ESPECTACULAR =====

let vizInitialized = false;

function initVisualizer() {
    vizCanvas = document.getElementById('viz3d');
    if (!vizCanvas) return;
    
    vizCtx = vizCanvas.getContext('2d');
    
    // Tamaño inicial pequeño, se ajustará al mostrar el dashboard
    vizWidth = 400;
    vizHeight = 300;
    
    const dpr = window.devicePixelRatio || 1;
    vizCanvas.width = vizWidth * dpr;
    vizCanvas.height = vizHeight * dpr;
    vizCtx.scale(dpr, dpr);
    
    initParticles();
    
    if (!vizAnimationId) {
        animateVisualizer();
    }
    
    window.addEventListener('resize', resizeCanvas);
    vizInitialized = true;
}

function resizeCanvas() {
    if (!vizCanvas || !vizCtx) return;
    
    const wrapper = vizCanvas.parentElement;
    if (!wrapper) return;
    
    const newWidth = wrapper.clientWidth;
    const newHeight = wrapper.clientHeight;
    
    if (newWidth < 50 || newHeight < 50) return;
    if (newWidth === vizWidth && newHeight === vizHeight) return;
    
    vizWidth = newWidth;
    vizHeight = newHeight;
    
    const dpr = window.devicePixelRatio || 1;
    vizCanvas.width = vizWidth * dpr;
    vizCanvas.height = vizHeight * dpr;
    
    vizCtx.setTransform(1, 0, 0, 1, 0, 0);
    vizCtx.scale(dpr, dpr);
    
    initParticles();
}

function initParticles() {
    vizData.particles = [];
    for (let i = 0; i < 60; i++) {
        vizData.particles.push({
            x: Math.random() * vizWidth,
            y: Math.random() * vizHeight,
            vx: (Math.random() - 0.5) * 0.5,
            vy: (Math.random() - 0.5) * 0.5,
            size: 1 + Math.random() * 2,
            color: ['#8b5cf6', '#22d3ee', '#f472b6', '#a78bfa'][Math.floor(Math.random() * 4)],
            pulse: Math.random() * Math.PI * 2
        });
    }
}

function initSequenceVisualization() {
    // No crear datos falsos - solo preparar estructura
    vizData.dataPoints = [];
    
    // Crear anillos de pulso
    vizData.pulseRings = [];
    for (let i = 0; i < 3; i++) {
        vizData.pulseRings.push({
            radius: 50 + i * 40,
            maxRadius: 150,
            opacity: 0.5,
            speed: 0.5 + i * 0.2
        });
    }
}

function updateVisualizationWithResults() {
    // Actualizar puntos de datos con las posiciones de matches
    if (vizData.matches.length > 0 && vizData.sequenceLength > 0) {
        vizData.dataPoints = [];
        const points = 100;
        const matchDensity = new Array(points).fill(0);
        
        vizData.matches.forEach(m => {
            const bucket = Math.floor((m.position / vizData.sequenceLength) * points);
            if (bucket >= 0 && bucket < points) {
                matchDensity[bucket]++;
            }
        });
        
        const maxDensity = Math.max(...matchDensity, 1);
        
        for (let i = 0; i < points; i++) {
            vizData.dataPoints.push({
                x: i / points,
                y: 0.2,
                targetY: 0.2 + (matchDensity[i] / maxDensity) * 0.6
            });
        }
    }
    
    // Añadir explosión de partículas
    for (let i = 0; i < 20; i++) {
        vizData.particles.push({
            x: vizWidth / 2,
            y: vizHeight / 2,
            vx: (Math.random() - 0.5) * 4,
            vy: (Math.random() - 0.5) * 4,
            size: 2 + Math.random() * 3,
            color: '#22d3ee',
            pulse: 0,
            life: 1
        });
    }
}

function animateVisualizer() {
    if (!vizCtx) {
        vizAnimationId = requestAnimationFrame(animateVisualizer);
        return;
    }
    
    vizTime += 0.016;
    
    // Limpiar canvas (transparente para ver el fondo cósmico)
    vizCtx.clearRect(0, 0, vizWidth, vizHeight);
    
    // NO dibujamos fondo ni nebulosas - dejamos ver el fondo cósmico de atrás
    
    // Dibujar grid holográfico
    drawHolographicGrid();
    
    // Dibujar doble hélice de ADN rotando
    drawDNAHelix();
    
    // Dibujar gráfico de densidad/frecuencia
    drawFrequencyGraph();
    
    // Dibujar partículas flotantes
    drawParticles();
    
    // Dibujar anillos de pulso centrales
    drawPulseRings();
    
    // Dibujar HUD con estadísticas
    drawHUD();
    
    // Efecto de escaneo
    drawScanEffect();
    
    vizAnimationId = requestAnimationFrame(animateVisualizer);
}

function drawNebulas() {
    const nebulas = [
        { x: 0.2, y: 0.3, r: 200, color: [139, 92, 246] },
        { x: 0.8, y: 0.6, r: 150, color: [34, 211, 238] },
        { x: 0.5, y: 0.8, r: 180, color: [244, 114, 182] }
    ];
    
    nebulas.forEach((n, i) => {
        const offsetX = Math.sin(vizTime * 0.2 + i) * 30;
        const offsetY = Math.cos(vizTime * 0.15 + i) * 20;
        const x = n.x * vizWidth + offsetX;
        const y = n.y * vizHeight + offsetY;
        
        const grad = vizCtx.createRadialGradient(x, y, 0, x, y, n.r);
        grad.addColorStop(0, `rgba(${n.color.join(',')}, 0.15)`);
        grad.addColorStop(0.5, `rgba(${n.color.join(',')}, 0.05)`);
        grad.addColorStop(1, 'transparent');
        
        vizCtx.fillStyle = grad;
        vizCtx.fillRect(0, 0, vizWidth, vizHeight);
    });
}

function drawHolographicGrid() {
    const gridSpacing = 40;
    const perspective = 0.6;
    const horizonY = vizHeight * 0.4;
    
    vizCtx.strokeStyle = 'rgba(139, 92, 246, 0.1)';
    vizCtx.lineWidth = 1;
    
    // Líneas horizontales con perspectiva
    for (let i = 0; i < 15; i++) {
        const y = horizonY + (i * i * 3);
        if (y > vizHeight) break;
        
        const alpha = 0.1 - (i * 0.006);
        vizCtx.strokeStyle = `rgba(139, 92, 246, ${Math.max(0.02, alpha)})`;
        vizCtx.beginPath();
        vizCtx.moveTo(0, y);
        vizCtx.lineTo(vizWidth, y);
        vizCtx.stroke();
    }
    
    // Líneas verticales convergentes
    const vanishX = vizWidth / 2;
    for (let i = -10; i <= 10; i++) {
        const baseX = vanishX + i * gridSpacing * 3;
        const alpha = 0.1 - Math.abs(i) * 0.008;
        vizCtx.strokeStyle = `rgba(139, 92, 246, ${Math.max(0.02, alpha)})`;
        vizCtx.beginPath();
        vizCtx.moveTo(vanishX, horizonY);
        vizCtx.lineTo(baseX, vizHeight);
        vizCtx.stroke();
    }
}

function drawDNAHelix() {
    const centerX = vizWidth * 0.72;
    const centerY = vizHeight * 0.5;
    const helixHeight = vizHeight * 0.75;
    const helixWidth = 70;
    const segments = 40;
    
    for (let strand = 0; strand < 2; strand++) {
        const offset = strand * Math.PI;
        const color = strand === 0 ? '#8b5cf6' : '#22d3ee';
        
        vizCtx.beginPath();
        vizCtx.strokeStyle = color;
        vizCtx.lineWidth = 3;
        vizCtx.shadowColor = color;
        vizCtx.shadowBlur = 20;
        
        for (let i = 0; i <= segments; i++) {
            const t = i / segments;
            const angle = t * Math.PI * 5 + vizTime * 1.5 + offset;
            const x = centerX + Math.cos(angle) * helixWidth;
            const y = centerY - helixHeight / 2 + t * helixHeight;
            const z = Math.sin(angle);
            
            const scale = 0.6 + z * 0.4;
            const adjustedX = centerX + (x - centerX) * scale;
            
            if (i === 0) {
                vizCtx.moveTo(adjustedX, y);
            } else {
                vizCtx.lineTo(adjustedX, y);
            }
        }
        vizCtx.stroke();
        vizCtx.shadowBlur = 0;
        
        // Dibujar nucleótidos
        for (let i = 0; i <= segments; i += 2) {
            const t = i / segments;
            const angle = t * Math.PI * 5 + vizTime * 1.5 + offset;
            const x = centerX + Math.cos(angle) * helixWidth;
            const y = centerY - helixHeight / 2 + t * helixHeight;
            const z = Math.sin(angle);
            
            const scale = 0.6 + z * 0.4;
            const adjustedX = centerX + (x - centerX) * scale;
            const size = 5 * scale;
            
            // Glow del nucleótido
            const glowGrad = vizCtx.createRadialGradient(adjustedX, y, 0, adjustedX, y, size * 3);
            glowGrad.addColorStop(0, color);
            glowGrad.addColorStop(0.3, color + '80');
            glowGrad.addColorStop(1, 'transparent');
            
            vizCtx.beginPath();
            vizCtx.arc(adjustedX, y, size * 3, 0, Math.PI * 2);
            vizCtx.fillStyle = glowGrad;
            vizCtx.fill();
            
            vizCtx.beginPath();
            vizCtx.arc(adjustedX, y, size, 0, Math.PI * 2);
            vizCtx.fillStyle = '#fff';
            vizCtx.fill();
        }
    }
    
    // Conectores entre hebras
    vizCtx.lineWidth = 1;
    for (let i = 0; i <= segments; i += 2) {
        const t = i / segments;
        const angle = t * Math.PI * 5 + vizTime * 1.5;
        const y = centerY - helixHeight / 2 + t * helixHeight;
        
        const x1 = centerX + Math.cos(angle) * helixWidth;
        const x2 = centerX + Math.cos(angle + Math.PI) * helixWidth;
        const z1 = Math.sin(angle);
        const z2 = Math.sin(angle + Math.PI);
        
        const scale1 = 0.6 + z1 * 0.4;
        const scale2 = 0.6 + z2 * 0.4;
        
        const connGrad = vizCtx.createLinearGradient(
            centerX + (x1 - centerX) * scale1, y,
            centerX + (x2 - centerX) * scale2, y
        );
        connGrad.addColorStop(0, 'rgba(139, 92, 246, 0.5)');
        connGrad.addColorStop(0.5, 'rgba(255, 255, 255, 0.3)');
        connGrad.addColorStop(1, 'rgba(34, 211, 238, 0.5)');
        
        vizCtx.beginPath();
        vizCtx.moveTo(centerX + (x1 - centerX) * scale1, y);
        vizCtx.lineTo(centerX + (x2 - centerX) * scale2, y);
        vizCtx.strokeStyle = connGrad;
        vizCtx.stroke();
    }
}

function drawFrequencyGraph() {
    // Solo mostrar si hay matches reales
    if (vizData.matches.length === 0) return;
    if (vizData.dataPoints.length === 0) return;
    
    const graphX = 30;
    const graphY = vizHeight * 0.85;
    const graphWidth = vizWidth * 0.42;
    const graphHeight = vizHeight * 0.35;
    
    // Fondo del gráfico con gradiente
    const bgGrad = vizCtx.createLinearGradient(graphX, graphY - graphHeight, graphX, graphY);
    bgGrad.addColorStop(0, 'rgba(139, 92, 246, 0.1)');
    bgGrad.addColorStop(1, 'rgba(0, 0, 0, 0.4)');
    vizCtx.fillStyle = bgGrad;
    vizCtx.fillRect(graphX - 5, graphY - graphHeight - 25, graphWidth + 10, graphHeight + 30);
    
    // Borde del gráfico
    vizCtx.strokeStyle = 'rgba(139, 92, 246, 0.4)';
    vizCtx.lineWidth = 1;
    vizCtx.strokeRect(graphX - 5, graphY - graphHeight - 25, graphWidth + 10, graphHeight + 30);
    
    // Líneas de referencia horizontales
    vizCtx.strokeStyle = 'rgba(139, 92, 246, 0.15)';
    for (let i = 0; i <= 4; i++) {
        const y = graphY - (i / 4) * graphHeight;
        vizCtx.beginPath();
        vizCtx.setLineDash([3, 3]);
        vizCtx.moveTo(graphX, y);
        vizCtx.lineTo(graphX + graphWidth, y);
        vizCtx.stroke();
    }
    vizCtx.setLineDash([]);
    
    // Actualizar puntos con animación suave
    vizData.dataPoints.forEach(p => {
        p.y += (p.targetY - p.y) * 0.08;
    });
    
    // Dibujar área rellena con gradiente
    vizCtx.beginPath();
    vizCtx.moveTo(graphX, graphY);
    
    vizData.dataPoints.forEach((p, i) => {
        const x = graphX + p.x * graphWidth;
        const y = graphY - p.y * graphHeight;
        vizCtx.lineTo(x, y);
    });
    
    vizCtx.lineTo(graphX + graphWidth, graphY);
    vizCtx.closePath();
    
    const areaGrad = vizCtx.createLinearGradient(0, graphY - graphHeight, 0, graphY);
    areaGrad.addColorStop(0, 'rgba(34, 211, 238, 0.5)');
    areaGrad.addColorStop(0.3, 'rgba(139, 92, 246, 0.3)');
    areaGrad.addColorStop(1, 'rgba(139, 92, 246, 0.05)');
    vizCtx.fillStyle = areaGrad;
    vizCtx.fill();
    
    // Dibujar línea principal con glow
    vizCtx.beginPath();
    vizData.dataPoints.forEach((p, i) => {
        const x = graphX + p.x * graphWidth;
        const y = graphY - p.y * graphHeight;
        
        if (i === 0) {
            vizCtx.moveTo(x, y);
        } else {
            vizCtx.lineTo(x, y);
        }
    });
    
    vizCtx.strokeStyle = '#22d3ee';
    vizCtx.lineWidth = 2.5;
    vizCtx.shadowColor = '#22d3ee';
    vizCtx.shadowBlur = 15;
    vizCtx.stroke();
    vizCtx.shadowBlur = 0;
    
    // Puntos en los picos
    vizData.dataPoints.forEach((p, i) => {
        if (i % 5 === 0 && p.y > 0.4) {
            const x = graphX + p.x * graphWidth;
            const y = graphY - p.y * graphHeight;
            
            vizCtx.beginPath();
            vizCtx.arc(x, y, 3, 0, Math.PI * 2);
            vizCtx.fillStyle = '#fff';
            vizCtx.fill();
        }
    });
    
    // Etiqueta del gráfico
    vizCtx.fillStyle = 'rgba(255, 255, 255, 0.8)';
    vizCtx.font = 'bold 11px "JetBrains Mono", monospace';
    vizCtx.fillText('DISTRIBUCION DE COINCIDENCIAS', graphX, graphY - graphHeight - 35);
}

function drawParticles() {
    vizData.particles.forEach((p, i) => {
        // Actualizar posición
        p.x += p.vx;
        p.y += p.vy;
        p.pulse += 0.05;
        
        // Rebote en bordes
        if (p.x < 0 || p.x > vizWidth) p.vx *= -1;
        if (p.y < 0 || p.y > vizHeight) p.vy *= -1;
        
        // Vida de partículas de explosión
        if (p.life !== undefined) {
            p.life -= 0.015;
            if (p.life <= 0) {
                vizData.particles.splice(i, 1);
                return;
            }
        }
        
        const size = p.size * (0.8 + Math.sin(p.pulse) * 0.2);
        const alpha = p.life !== undefined ? p.life : 0.6;
        
        // Glow
        const grad = vizCtx.createRadialGradient(p.x, p.y, 0, p.x, p.y, size * 4);
        grad.addColorStop(0, p.color + Math.floor(alpha * 80).toString(16).padStart(2, '0'));
        grad.addColorStop(1, 'transparent');
        vizCtx.fillStyle = grad;
        vizCtx.beginPath();
        vizCtx.arc(p.x, p.y, size * 4, 0, Math.PI * 2);
        vizCtx.fill();
        
        // Núcleo
        vizCtx.beginPath();
        vizCtx.arc(p.x, p.y, size, 0, Math.PI * 2);
        vizCtx.fillStyle = p.color;
        vizCtx.fill();
    });
}

function drawPulseRings() {
    const centerX = vizWidth * 0.72;
    const centerY = vizHeight * 0.5;
    
    vizData.pulseRings.forEach((ring, i) => {
        ring.radius += ring.speed;
        if (ring.radius > ring.maxRadius) {
            ring.radius = 30;
        }
        
        const progress = ring.radius / ring.maxRadius;
        const alpha = 0.4 * (1 - progress);
        
        vizCtx.beginPath();
        vizCtx.arc(centerX, centerY, ring.radius, 0, Math.PI * 2);
        vizCtx.strokeStyle = `rgba(139, 92, 246, ${alpha})`;
        vizCtx.lineWidth = 2;
        vizCtx.stroke();
    });
}

function drawHUD() {
    const padding = 15;
    
    // Panel superior izquierdo - Info de secuencia
    drawHUDPanel(padding, padding, 180, 85, [
        { label: 'SECUENCIA', value: vizData.sequenceLength > 0 ? vizData.sequenceLength.toLocaleString() + ' bp' : '---' },
        { label: 'GC CONTENT', value: vizData.gcContent > 0 ? vizData.gcContent.toFixed(1) + '%' : '---' }
    ], 'SEQ');
    
    // Panel superior derecho - Info de búsqueda
    const rightPanelX = vizWidth - 180 - padding;
    drawHUDPanel(rightPanelX, padding, 180, 115, [
        { label: 'MATCHES', value: vizData.matches.length > 0 ? vizData.matches.length.toLocaleString() : '---', highlight: vizData.matches.length > 0 },
        { label: 'ALGORITMO', value: getAlgorithmName(vizData.algorithm) },
        { label: 'TIEMPO', value: vizData.searchTime ? vizData.searchTime.toFixed(2) + ' ms' : '---' }
    ], 'SRC');
    
    // Indicador de estado central
    const statusX = vizWidth / 2;
    const statusY = padding + 20;
    const status = vizData.isSearching ? 'ANALIZANDO...' : (vizData.matches.length > 0 ? 'ANALISIS COMPLETADO' : (vizData.sequenceLength > 0 ? 'LISTO PARA BUSCAR' : 'ESPERANDO SECUENCIA'));
    const statusColor = vizData.isSearching ? '#fbbf24' : (vizData.matches.length > 0 ? '#22c55e' : '#8b5cf6');
    
    // Fondo del status
    const statusWidth = 200;
    vizCtx.fillStyle = 'rgba(0, 0, 0, 0.5)';
    vizCtx.fillRect(statusX - statusWidth/2, statusY - 15, statusWidth, 25);
    vizCtx.strokeStyle = statusColor + '60';
    vizCtx.lineWidth = 1;
    vizCtx.strokeRect(statusX - statusWidth/2, statusY - 15, statusWidth, 25);
    
    vizCtx.fillStyle = statusColor;
    vizCtx.font = 'bold 11px "JetBrains Mono", monospace';
    vizCtx.textAlign = 'center';
    vizCtx.fillText(status, statusX, statusY);
    
    // Punto parpadeante
    const blink = Math.sin(vizTime * 6) > 0;
    if (vizData.isSearching || blink) {
        vizCtx.beginPath();
        vizCtx.arc(statusX - 85, statusY - 3, 4, 0, Math.PI * 2);
        vizCtx.fillStyle = statusColor;
        vizCtx.shadowColor = statusColor;
        vizCtx.shadowBlur = 10;
        vizCtx.fill();
        vizCtx.shadowBlur = 0;
    }
    
    vizCtx.textAlign = 'left';
}

function drawHUDPanel(x, y, width, height, items, label = '') {
    // Fondo del panel con gradiente
    const bgGrad = vizCtx.createLinearGradient(x, y, x + width, y + height);
    bgGrad.addColorStop(0, 'rgba(10, 0, 30, 0.85)');
    bgGrad.addColorStop(1, 'rgba(5, 0, 15, 0.9)');
    vizCtx.fillStyle = bgGrad;
    vizCtx.fillRect(x, y, width, height);
    
    // Borde con glow sutil
    vizCtx.strokeStyle = 'rgba(139, 92, 246, 0.5)';
    vizCtx.lineWidth = 1;
    vizCtx.strokeRect(x, y, width, height);
    
    // Esquinas decorativas brillantes
    const cornerSize = 10;
    vizCtx.strokeStyle = '#8b5cf6';
    vizCtx.lineWidth = 2;
    vizCtx.shadowColor = '#8b5cf6';
    vizCtx.shadowBlur = 5;
    
    // Esquinas
    [[x, y, 1, 1], [x + width, y, -1, 1], [x, y + height, 1, -1], [x + width, y + height, -1, -1]].forEach(([cx, cy, dx, dy]) => {
        vizCtx.beginPath();
        vizCtx.moveTo(cx, cy + cornerSize * dy);
        vizCtx.lineTo(cx, cy);
        vizCtx.lineTo(cx + cornerSize * dx, cy);
        vizCtx.stroke();
    });
    vizCtx.shadowBlur = 0;
    
    // Label de texto en lugar de emoji
    if (label) {
        vizCtx.fillStyle = 'rgba(139, 92, 246, 0.8)';
        vizCtx.font = 'bold 10px "JetBrains Mono", monospace';
        vizCtx.fillText('[' + label + ']', x + 10, y + 18);
    }
    
    // Contenido
    let offsetY = y + (label ? 32 : 20);
    items.forEach((item, idx) => {
        vizCtx.fillStyle = 'rgba(255, 255, 255, 0.5)';
        vizCtx.font = '9px "JetBrains Mono", monospace';
        vizCtx.fillText(item.label, x + 12, offsetY);
        
        vizCtx.fillStyle = item.highlight ? '#22d3ee' : '#ffffff';
        vizCtx.font = 'bold 13px "JetBrains Mono", monospace';
        
        if (item.highlight) {
            vizCtx.shadowColor = '#22d3ee';
            vizCtx.shadowBlur = 8;
        }
        vizCtx.fillText(item.value, x + 12, offsetY + 14);
        vizCtx.shadowBlur = 0;
        
        offsetY += 28;
    });
}

function drawScanEffect() {
    const scanY = (vizTime * 40) % vizHeight;
    
    const grad = vizCtx.createLinearGradient(0, scanY - 40, 0, scanY + 40);
    grad.addColorStop(0, 'transparent');
    grad.addColorStop(0.5, 'rgba(34, 211, 238, 0.08)');
    grad.addColorStop(1, 'transparent');
    
    vizCtx.fillStyle = grad;
    vizCtx.fillRect(0, scanY - 40, vizWidth, 80);
}

function getAlgorithmName(algo) {
    if (!algo) return '---';
    const names = {
        'naive-local': 'NAIVE',
        'kmp': 'KMP',
        'boyer-moore': 'BOYER-MOORE',
        'rabin-karp': 'RABIN-KARP'
    };
    return names[algo] || algo.toUpperCase();
}

// INIT
document.addEventListener('DOMContentLoaded', () => {
    initDNA();
    initVisualizer();
    renderHistory();
});

// Reinicializar visualizador cuando se cambie a la vista dashboard
const originalSwitchView = switchView;
switchView = function(viewId) {
    originalSwitchView(viewId);
    
    // Si cambiamos al dashboard, ajustar tamaño del canvas
    if (viewId === 'dashboard') {
        // Pequeño delay para que el CSS se aplique
        setTimeout(resizeCanvas, 50);
    }
};
