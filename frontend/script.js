// ===== STATE =====
let isFileUploaded = false;

// ===== DNA ANIMATION (COSMIC EDITION) =====
function initDNA() {
    const container = document.getElementById('dnaHelix');
    const wrapper = document.getElementById('dnaContainer');
    if (!container) return;
    
    container.innerHTML = '';
    
    const pairCount = 40;
    const pairs = [];
    
    // 1. Generar Hélice
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
    
    // 2. Generar Partículas
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
    
    // 3. Bucle de Animación
    let time = 0;
    function animate() {
        time += 0.008; // Velocidad
        
        pairs.forEach((pair, i) => {
            const y = (i / pairCount) * 100; // Porcentaje vertical
            const rotation = (i * 0.4) + (time * 2); // Giro
            
            // Calcular coordenadas 3D
            const radius = 80;
            const leftX = Math.cos(rotation) * radius;
            const z = Math.sin(rotation) * radius;
            const rightX = Math.cos(rotation + Math.PI) * radius;
            
            // Aplicar transformaciones
            pair.el.style.top = `${y}%`;
            
            // Nucleótidos
            pair.left.style.transform = `translateX(${leftX}px) translateZ(${z}px)`;
            pair.right.style.transform = `translateX(${rightX}px) translateZ(${-z}px)`;
            
            // Profundidad (Escala y Opacidad)
            const depthScale = 0.6 + ((z + radius) / (radius * 2)) * 0.4;
            pair.left.style.transform += ` scale(${depthScale})`;
            pair.right.style.transform += ` scale(${1.2 - depthScale + 0.4})`; // Inverso para el otro lado
            
            // Conector
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
    // Bloqueo de Seguridad
    if (!isFileUploaded && !['upload', 'history'].includes(viewId)) {
        showToast('⛔ Acceso Denegado: Importa una secuencia primero', 'error');
        return;
    }
    
    // UI Update
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.getElementById('view' + viewId.charAt(0).toUpperCase() + viewId.slice(1)).classList.add('active');
    
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.view === viewId) btn.classList.add('active');
    });
}

// Event Listeners Nav
document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => switchView(btn.dataset.view));
});

// ===== UPLOAD LOGIC =====
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');

dropZone.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', (e) => { if (e.target.files.length) handleUpload(e.target.files[0]); });

function handleUpload(file) {
    // UI Carga
    const icon = dropZone.querySelector('.upload-icon');
    const title = dropZone.querySelector('.upload-title');
    
    icon.innerHTML = '<i class="ri-loader-4-line loader"></i>';
    title.textContent = 'ANALIZANDO...';
    
    setTimeout(() => {
        isFileUploaded = true;
        
        // Desbloquear botones
        document.querySelectorAll('.nav-btn.locked').forEach(btn => btn.classList.remove('locked'));
        
        // Actualizar Datos Dashboard
        document.getElementById('fileName').textContent = file.name.toUpperCase();
        document.getElementById('statBP').textContent = (Math.random() * 900000).toFixed(0).toLocaleString();
        document.getElementById('statGC').textContent = (Math.random() * 40 + 30).toFixed(1) + '%';
        
        // Actualizar Header Status
        document.getElementById('statusDot').className = 'status-dot active-dot';
        document.getElementById('statusText').textContent = 'SISTEMA ACTIVO';
        
        showToast('Secuencia importada correctamente');
        switchView('dashboard');
        
        // Reset Upload Zone
        setTimeout(() => {
            icon.innerHTML = '<i class="ri-check-line"></i>';
            title.textContent = 'Archivo Cargado';
        }, 500);
    }, 1500);
}

// ===== SEARCH LOGIC =====
function setPattern(val) { document.getElementById('patternInput').value = val; }

function runSearch() {
    const val = document.getElementById('patternInput').value;
    if(!val) return showToast('⚠️ Ingrese un patrón', 'error');
    
    switchView('results');
    document.getElementById('resPattern').innerText = val.toUpperCase();
    document.getElementById('resMatches').innerText = Math.floor(Math.random() * 50) + 5;
    
    // Generar Mapa y Tabla
    const track = document.getElementById('genomeTrack');
    const tbody = document.getElementById('resultsTableBody');
    track.innerHTML = '';
    tbody.innerHTML = '';
    
    for(let i=0; i<15; i++) {
        const pct = Math.random() * 98;
        const mark = document.createElement('div');
        mark.className = 'match-mark';
        mark.style.left = pct + '%';
        track.appendChild(mark);
        
        if(i < 8) {
            tbody.innerHTML += `
                <tr>
                    <td>#${i+1}</td>
                    <td style="color:var(--cyan-accent)">${(pct*10000).toFixed(0)}</td>
                    <td style="font-family:monospace; color:var(--text-muted)">...ACT<span style="color:#fff; font-weight:bold">${val.toUpperCase()}</span>G...</td>
                    <td>99.9%</td>
                </tr>
            `;
        }
    }
}

// ===== TOAST =====
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    document.getElementById('toastMessage').textContent = message;
    if(type === 'error') toast.classList.add('error'); else toast.classList.remove('error');
    
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3000);
}

// INIT
document.addEventListener('DOMContentLoaded', initDNA);