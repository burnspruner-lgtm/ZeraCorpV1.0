/** DOM Elements **/
const logsContainer = document.getElementById('logs');
const heartbeatElement = document.getElementById('heartbeat');
const messageBox = document.getElementById('message-box');
const aiActionDisplay = document.getElementById('ai-action-display');
const dataForm = document.getElementById('data-form');
let telemetryChart;
let userRole = null;
const API_URL = '' || window.location.origin;

// --- 1. Element References ---
const elements = {
    landingPage: document.getElementById('landing-page'),
    authPage: document.getElementById('auth-page'),
    appShell: document.getElementById('app-shell'),
    logs: document.getElementById('logs'),
    heartbeat: document.getElementById('heartbeat'),
    safetyLock: document.getElementById('safety-lock-status'),
    agentHealth: document.getElementById('agent-health'),
    agentUptime: document.getElementById('agent-uptime'),
    totalDecisions: document.getElementById('total-decisions'),
    dataForm: document.getElementById('data-form'),
    modal: document.getElementById('modal'),
    modalTitle: document.getElementById('modal-title'),
    modalBody: document.getElementById('modal-body'),
    modalClose: document.getElementById('modal-close'),
    pageTitle: document.getElementById('page-title'),
    sidebarNav: document.getElementById('sidebar-nav'),
    userName: document.getElementById('user-name'),
    userRole: document.getElementById('user-role'),
    aiTriggerBtn: document.getElementById('btn-trigger-ai'),
    chat: { 
        window: document.getElementById('chat-window'), 
        form: document.getElementById('chat-form'), 
        input: document.getElementById('chat-input') 
    },
    pageContents: {
        soil_analysis: document.getElementById('page-soil_analysis'),
        location_intel: document.getElementById('page-location_intel'),
        ml_insights: document.getElementById('page-ml_insights'),
        ai_heuristics: document.getElementById('page-ai_heuristics'),
        admin_panel: document.getElementById('page-admin_panel'),
        system_logs: document.getElementById('logs')
    },
    loginForm: document.getElementById('login-form'),
    loginError: document.getElementById('login-error'),
    loginUsername: document.getElementById('login-username'),
    loginPassword: document.getElementById('login-password'),
    registerForm: document.getElementById('register-form'),
    registerMessage: document.getElementById('register-message'),
    registerUsername: document.getElementById('register-username'),
    registerPassword: document.getElementById('register-password'),
    tabLogin: document.getElementById('tab-login'),
    tabRegister: document.getElementById('tab-register'),
    loginFormContainer: document.getElementById('login-form-container'),
    registerFormContainer: document.getElementById('register-form-container'),
    logoutButton: document.getElementById('logout-button')
};

const pages = document.querySelectorAll('.page');

// --- 2. Navigation Control ---

function showLanding() {
    elements.appShell?.classList.add('hidden');
    elements.authPage?.classList.add('hidden');
    elements.landingPage?.classList.remove('hidden');
}

window.transitionToAuth = function() {
    elements.landingPage.classList.add('hidden');
    elements.authPage.classList.remove('hidden');
    elements.authPage.classList.add('flex');
    toggleAuthTab('login'); // Default to login view
};

window.backToLanding = function() {
    elements.authPage.classList.add('hidden');
    elements.authPage.classList.remove('flex');
    elements.landingPage.classList.remove('hidden');
};

// --- 3. Role-Based Navigation & UI ---

const navConfig = {
    dashboard: '<a href="#dashboard" class="nav-link"><i class="fa-solid fa-chart-line"></i>Dashboard</a>',
    ai_chat: '<a href="#ai_chat" class="nav-link"><i class="fa-solid fa-comments"></i>AI Assistant</a>',
    soil_analysis: '<a href="#soil_analysis" class="nav-link"><i class="fa-solid fa-seedling"></i>Soil & Crop</a>',
    location_intel: '<a href="#location_intel" class="nav-link"><i class="fa-solid fa-map-location-dot"></i>Location Intel</a>',
    ml_insights: '<a href="#ml_insights" class="nav-link"><i class="fa-solid fa-brain"></i>ML Predictions</a>',
    ai_heuristics: '<a href="#ai_heuristics" class="nav-link"><i class="fa-solid fa-diagram-project"></i>Heuristics</a>',
    admin_panel: '<a href="#admin_panel" class="nav-link"><i class="fa-solid fa-users-gear"></i>Admin</a>',
    system_logs: '<a href="#system_logs" class="nav-link"><i class="fa-solid fa-terminal"></i>Logs</a>'
};

const rolePermissions = {
    user: ['dashboard', 'ai_chat', 'soil_analysis', 'location_intel'],
    admin: ['dashboard', 'admin_panel', 'ai_chat', 'soil_analysis', 'location_intel', 'ml_insights', 'ai_heuristics', 'system_logs'],
    maintenance: ['dashboard', 'ai_heuristics', 'system_logs'],
    developer: ['dashboard', 'admin_panel', 'ai_chat', 'soil_analysis', 'location_intel', 'ml_insights', 'ai_heuristics', 'system_logs']
};


/** Input Feedback Logic **/
const moistureInput = document.querySelector('input[name="moisture"]');
if (moistureInput) {
    moistureInput.addEventListener('input', (e) => {
        const val = parseInt(e.target.value);
        const feedback = document.getElementById('moisture-feedback');
        if (feedback) {
            if (val > 80) {
                feedback.textContent = "Warning: High rot risk!";
                feedback.className = "text-yellow-500 text-xs italic";
            } else {
                feedback.textContent = "";
            }
        }
    });
}

/** Navigation Logic **/
function showPage(pageId) {
    history.pushState({page: pageId}, "", `#${pageId}`);
}

window.onpopstate = function(event) {
    if(event.state) showPage(event.state.page);
}

/** System Heartbeat & Safety Monitoring **/
async function fetchHeartbeat() {
    try {
        const response = await fetch(`${API_URL}/status`);
        const data = await response.json();
        
        // Update Heartbeat Display
        heartbeatElement.textContent = new Date().toLocaleTimeString();
        
        // Safety lock status display logic
        const safetyLockElement = document.getElementById('safety-lock-status');
        if (safetyLockElement) {
            if (data.safety_lock === false) {
                safetyLockElement.textContent = `Lock: INACTIVE (Privilege Jump!)`;
                safetyLockElement.className = 'font-mono text-xs text-red-500 font-bold animate-pulse';
                heartbeatElement.textContent = `System: ${data.status} | Load: ${data.cpu_usage}%`;
                heartbeatElement.className = 'font-mono text-xs text-red-500 font-bold';
            } else {
                safetyLockElement.textContent = `Lock: ACTIVE`;
                safetyLockElement.className = 'font-mono text-xs text-gray-400';
                heartbeatElement.className = 'font-mono text-xs text-green-400';
            }
        }

    } catch (error) {
        heartbeatElement.textContent = 'Worker Offline';
        heartbeatElement.className = 'font-mono text-xs text-red-700 underline';
    }
}

/** Data Processing & AI Submission **/
async function handleDataSubmission(e) {
    e.preventDefault();
    if (messageBox) messageBox.textContent = 'Sending data to AI Engine...';
    
    const payload = [
        {
            "field_id": dataForm.elements['field_id'].value, 
            "moisture": parseInt(dataForm.elements['moisture'].value), 
            "nutrient_level": dataForm.elements['nutrient_level'].value,
            "temp": parseInt(dataForm.elements['temp'].value),
            "cost_kes": parseInt(dataForm.elements['cost_kes'].value), 
            "pump_pressure": parseInt(dataForm.elements['pump_pressure'].value),
            "historical_trend": dataForm.elements['historical_trend'].value
        }
    ];

    try {
        const response = await fetch(`${API_URL}/api/process_full_ai`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (response.ok) {
            if (messageBox) messageBox.textContent = `SUCCESS: ${data.prediction}`;
            if (aiActionDisplay) aiActionDisplay.textContent = data.ai_action;
            log(`[BACKEND] Prediction: ${data.prediction} | AI Action: ${data.ai_action}`, 'SUCCESS');
            
            // Update the chart if value exists
            if (payload[0].moisture) updateChart(payload[0].moisture);
        } else {
            if (messageBox) messageBox.textContent = `ERROR: ${data.message || 'Unknown error'}`;
            if (aiActionDisplay) aiActionDisplay.textContent = "Error during processing.";
            log(`[BACKEND] Error: ${data.message || 'Server did not respond.'}`, 'ERROR');
        }
    } catch (error) {
        if (messageBox) messageBox.textContent = `CONNECTION ERROR: Could not reach ${API_URL}`;
        if (aiActionDisplay) aiActionDisplay.textContent = "Worker Offline.";
        log(`[FATAL] Connection failed. Is the server running? ${error.message}`, 'CRITICAL');
    }
}

/** Telemetry Visualization **/
function initChart() {
    const chartCanvas = document.getElementById('telemetryChart');
    if (!chartCanvas) return;
    
    const ctx = chartCanvas.getContext('2d');
    telemetryChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [], // Time stamps
            datasets: [{
                label: 'Soil Moisture (%)',
                borderColor: '#3b82f6', 
                data: [],
                fill: true,
                tension: 0.4,
                backgroundColor: 'rgba(59, 130, 246, 0.1)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: { 
                y: { beginAtZero: true, max: 100, grid: { color: 'rgba(255,255,255,0.1)' } },
                x: { grid: { display: false } }
            },
            plugins: {
                legend: { labels: { color: '#94a3b8' } }
            }
        }
    });
}

function updateChart(newValue) {
    if (!telemetryChart) return;
    const now = new Date().toLocaleTimeString();
    telemetryChart.data.labels.push(now);
    telemetryChart.data.datasets[0].data.push(newValue);
    
    // Keep only last 10 readings for performance
    if (telemetryChart.data.labels.length > 10) {
        telemetryChart.data.labels.shift();
        telemetryChart.data.datasets[0].data.shift();
    }
    telemetryChart.update();
}

function applyRoles(role) {
    if (!elements.sidebarNav) return;
    
    elements.sidebarNav.innerHTML = '';
    const permissions = rolePermissions[role] || rolePermissions['user'];
    
    permissions.forEach(pageId => {
        if (navConfig[pageId]) {
            elements.sidebarNav.innerHTML += navConfig[pageId];
        }
    });

    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const pageId = e.currentTarget.getAttribute('href').substring(1);
            showPage(pageId);
        });
    });
    
    // UI Visibility based on data-role
    document.querySelectorAll('[data-role]').forEach(el => {
        const requiredRole = el.getAttribute('data-role');
        el.style.display = (role === requiredRole || role === 'admin' || role === 'developer') ? 'block' : 'none';
    });
    
    showPage('dashboard');
}

// --- 4. Auth Page Logic ---

function toggleAuthTab(type) {
    if (type === 'login') {
        elements.tabLogin.className = "flex-1 py-2.5 text-sm font-bold rounded-xl transition-all duration-300 text-white bg-blue-600/90 shadow-[0_4px_12px_rgba(37,99,235,0.3)]";
        elements.tabRegister.className = "flex-1 py-2.5 text-sm font-bold rounded-xl transition-all duration-300 text-slate-400 hover:text-slate-200";
        elements.loginFormContainer.classList.remove('hidden');
        elements.registerFormContainer.classList.add('hidden');
    } else {
        elements.tabRegister.className = "flex-1 py-2.5 text-sm font-bold rounded-xl transition-all duration-300 text-white bg-emerald-600/90 shadow-[0_4px_12px_rgba(16,185,129,0.3)]";
        elements.tabLogin.className = "flex-1 py-2.5 text-sm font-bold rounded-xl transition-all duration-300 text-slate-400 hover:text-slate-200";
        elements.registerFormContainer.classList.remove('hidden');
        elements.loginFormContainer.classList.add('hidden');
    }
}

elements.tabLogin?.addEventListener('click', () => toggleAuthTab('login'));
elements.tabRegister?.addEventListener('click', () => toggleAuthTab('register'));

elements.registerForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = elements.registerUsername.value;
    const password = elements.registerPassword.value;
    elements.registerMessage.textContent = "Processing registration...";
    
    try {
        const response = await fetch(`${API_URL}/api/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.message);
        
        elements.registerMessage.textContent = "Registration Successful!";
        elements.registerMessage.className = "mt-4 text-center text-emerald-500";
        setTimeout(() => toggleAuthTab('login'), 1500);
    } catch (error) {
        elements.registerMessage.textContent = `Error: ${error.message}`;
        elements.registerMessage.className = "mt-4 text-center text-red-500";
    }
});

elements.loginForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = elements.loginUsername.value;
    const password = elements.loginPassword.value;
    elements.loginError.textContent = "Authenticating...";
    
    try {
        const response = await fetch(`${API_URL}/api/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.message);
        startFullApp(data.username, data.role);
    } catch (error) {
        elements.loginError.textContent = `Access Denied: ${error.message}`;
        elements.loginError.className = "mt-4 text-center text-red-500";
    }
});

elements.logoutButton?.addEventListener('click', async () => {
    await fetch(`${API_URL}/api/logout`, { method: 'POST' }); 
    window.location.reload();
});

// --- 5. Main App Initialization ---

function startFullApp(username, role) {
    userRole = role;
    if (elements.userName) elements.userName.textContent = username;
    if (elements.userRole) elements.userRole.textContent = role.toUpperCase();
    
    elements.landingPage.classList.add('hidden');
    elements.authPage.classList.add('hidden');
    elements.appShell.classList.remove('hidden');
    
    applyRoles(userRole);
    startAppServices();
}

async function checkSession() {
    try {
        const response = await fetch(`${API_URL}/api/check_session`); 
        const data = await response.json();
        if (data.is_logged_in) {
            startFullApp(data.username, data.role);
        } else {
            showLanding();
        }
    } catch (e) {
        console.error("Auth system offline", e);
        showLanding(); 
    }
}

// --- 6. Logging, Modal, SPA ---

function log(message, type = 'INFO') {
    if(!elements.logs) return;
    const colors = { 'FATAL': 'text-red-500', 'ERROR': 'text-red-400', 'SUCCESS': 'text-emerald-400', 'INFO': 'text-slate-400' };
    const entry = document.createElement('div');
    entry.className = `${colors[type] || 'text-slate-400'} font-mono mb-1 text-xs`;
    entry.innerHTML = `<span class="opacity-50">[${new Date().toLocaleTimeString()}]</span> ${message}`;
    elements.logs.appendChild(entry);
    elements.logs.scrollTop = elements.logs.scrollHeight;
}

function showModal(title, jsonData) {
    elements.modalTitle.textContent = title;
    elements.modalBody.innerHTML = `<pre class="bg-slate-950 p-4 rounded text-xs font-mono text-emerald-400 overflow-x-auto">${JSON.stringify(jsonData, null, 2)}</pre>`;
    elements.modal.classList.remove('hidden');
    elements.modal.classList.add('flex');
}

elements.modalClose?.addEventListener('click', () => {
    elements.modal.classList.add('hidden');
    elements.modal.classList.remove('flex');
});

function showPage(pageId) {
    document.querySelectorAll('.page').forEach(p => {
        p.classList.remove('active');
        p.classlist.add('hidden');
    });
    const target = document.getElementById(`page-${pageId}`);
    if (target) {
        target.classList.add('active');
        target.classList.remove('hidden');
        // Update Title
        const navLink = document.querySelector(`a[href="#${pageId}"]`);
        if (navLink && elements.pageTitle) {
            elements.pageTitle.textContent = navLink.textContent.trim();
            elements.pageTitle.innerText = pageId.replace('_', ' ').toUpperCase();
        } else {
        console.error(`Logic Error: Page ID 'page-${pageId}' not found in DOM.`);
    }

    // Contextual Page Triggers
    if (pageId === 'admin_panel') runAdminPanel();
    if (pageId === 'ml_insights') runFeature('ml_insights', 'api/ml_insights', 'ML Insights');
}

// --- 7. API Services ---

async function fetchHeartbeat() {
    try {
        const response = await fetch(`${API_URL}/status`); 
        const data = await response.json();
        
        if (elements.heartbeat) {
            elements.heartbeat.textContent = "ONLINE";
            elements.heartbeat.className = 'text-xs font-mono text-emerald-500 ml-2';
        }
        
        if (elements.safetyLock) {
            elements.safetyLock.textContent = data.safety_lock ? 'ENGAGED' : 'BREACH';
            elements.safetyLock.className = data.safety_lock ? 'text-xs font-mono text-emerald-500 ml-2' : 'text-xs font-mono text-red-500 ml-2 animate-pulse';
        }

        const status = data.agent_deep_status || {};
        if (elements.agentHealth) elements.agentHealth.textContent = status.agent_health_status || 'OK';
        if (elements.agentUptime) elements.agentUptime.textContent = `${(status.uptime_seconds || 0).toFixed(1)}s`;
        if (elements.totalDecisions) elements.totalDecisions.textContent = status.total_decisions || 0;
        
    } catch (error) { 
        if (elements.heartbeat) {
            elements.heartbeat.textContent = 'OFFLINE';
            elements.heartbeat.className = 'text-xs font-mono text-red-600 ml-2';
        }
    }
}

function startAppServices() {
    setInterval(fetchHeartbeat, 5000);
    fetchHeartbeat();
    log('ZeraCorp V1.0 Neural Link Established.', 'SUCCESS');
}

// --- 8. Admin & Features ---

async function runAdminPanel() {
    try {
        const response = await fetch(`${API_URL}/api/admin/get_users`); 
        const data = await response.json();
        if (!response.ok) throw new Error(data.message);
        
        let html = `<table class="min-w-full text-sm text-left text-slate-300">
            <thead class="text-xs uppercase bg-slate-800 text-slate-400">
                <tr><th class="px-4 py-2">User</th><th class="px-4 py-2">Role</th></tr>
            </thead>
            <tbody>`;
        
        data.forEach(user => {
            html += `<tr class="border-b border-slate-800">
                <td class="px-4 py-2 font-bold">${user.username}</td>
                <td class="px-4 py-2">
                    <select onchange="promoteUser('${user.id}', this.value)" class="bg-slate-900 border border-slate-700 rounded text-xs p-1">
                        <option value="user" ${user.role === 'user' ? 'selected' : ''}>User</option>
                        <option value="admin" ${user.role === 'admin' ? 'selected' : ''}>Admin</option>
                        <option value="maintenance" ${user.role === 'maintenance' ? 'selected' : ''}>Maint</option>
                    </select>
                </td>
            </tr>`;
        });
        html += `</tbody></table>`;
        elements.pageContents.admin_panel.innerHTML = html;
    } catch (e) {
        elements.pageContents.admin_panel.innerHTML = `<p class="text-red-500">Access Denied: Admin Privileges Required.</p>`;
    }
}

window.promoteUser = async function(userId, newRole) {
    try {
        const response = await fetch(`${API_URL}/api/admin/promote_user`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId, new_role: newRole })
        });
        if (response.ok) log(`User updated to ${newRole}`, 'SUCCESS');
    } catch (e) { log('Promotion failed', 'ERROR'); }
};

/** Initialization **/
document.addEventListener('DOMContentLoaded', async () => {
    // 1. Await the session check first
    await checkSession();
    
    // 2. Attach form listener
    if (dataForm) {
        dataForm.addEventListener('submit', handleDataSubmission);
    }
    
    // 3. Setup Chart
    initChart();
    
    // 4. Start background services
    if (typeof startAppServices === 'function') {
        startAppServices();
    } else {
        setInterval(fetchHeartbeat, 3000);
        fetchHeartbeat();
        log('ZeraCorp V1.0 - Front-end systems active.', 'INFO');
    }
});