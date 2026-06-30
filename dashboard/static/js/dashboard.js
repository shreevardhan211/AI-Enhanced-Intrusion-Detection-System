/* ============================================================================
   AI-ENHANCED INTRUSION DETECTION SYSTEM - DASHBOARD JAVASCRIPT
   Real-time Updates, API Integration, Chart Management
   ============================================================================ */

// Configuration
const CONFIG = {
    API_BASE: '/api',
    REFRESH_INTERVAL: 2000,  // 2 seconds
    CHART_UPDATE_INTERVAL: 3000,  // 3 seconds
    MAX_CHART_POINTS: 20,
};

// Global state
const state = {
    stats: {
        total_packets: 0,
        normal_packets: 0,
        attack_packets: 0,
        attack_breakdown: {}
    },
    logs: [],
    alerts: [],
    chartData: {
        timestamps: [],
        normalTraffic: [],
        attackTraffic: [],
    }
};

// Chart instances
let charts = {
    attackDistribution: null,
    trafficStatus: null,
    trafficTrend: null
};

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('[✓] Dashboard initializing...');
    
    initializeCharts();
    initializeEventListeners();
    checkSystemHealth();
    startRealtimeUpdates();
    
    console.log('[✓] Dashboard ready');
});

// ============================================================================
// SYSTEM HEALTH CHECK
// ============================================================================

async function checkSystemHealth() {
    try {
        const response = await fetch(`${CONFIG.API_BASE}/health`);
        const data = await response.json();
        
        const statusIndicator = document.querySelector('.status-indicator');
        const statusText = document.querySelector('.status-text');
        const statusDot = document.querySelector('.status-dot');
        
        if (data.model_loaded) {
            statusIndicator.classList.remove('offline');
            statusText.textContent = 'Online';
            console.log('[✓] System online - Model loaded');
            return true;
        } else {
            statusIndicator.classList.add('offline');
            statusText.textContent = 'Offline';
            console.warn('[✗] System offline - Model not loaded');
            return false;
        }
    } catch (error) {
        console.error('[✗] Health check failed:', error);
        document.querySelector('.status-indicator').classList.add('offline');
        document.querySelector('.status-text').textContent = 'Connection Error';
        return false;
    }
}

// ============================================================================
// EVENT LISTENERS
// ============================================================================

function initializeEventListeners() {
    // Refresh stats on demand
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden) {
            updateAllStats();
        }
    });
}

// ============================================================================
// CHART INITIALIZATION & MANAGEMENT
// ============================================================================

function initializeCharts() {
    // Chart.js defaults
    Chart.defaults.color = '#a0aac0';
    Chart.defaults.borderColor = '#2d3a5f';
    Chart.defaults.font.family = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto";
    
    // Attack Distribution (Pie Chart)
    const attackCtx = document.getElementById('attackDistributionChart')?.getContext('2d');
    if (attackCtx) {
        charts.attackDistribution = new Chart(attackCtx, {
            type: 'doughnut',
            data: {
                labels: ['Normal', 'DoS', 'Probe', 'R2L', 'U2R'],
                datasets: [{
                    data: [70, 15, 8, 4, 3],
                    backgroundColor: [
                        'rgba(16, 185, 129, 0.8)',    // Green - Normal
                        'rgba(239, 68, 68, 0.8)',     // Red - DoS
                        'rgba(245, 158, 11, 0.8)',    // Yellow - Probe
                        'rgba(59, 130, 246, 0.8)',    // Blue - R2L
                        'rgba(139, 92, 246, 0.8)',    // Purple - U2R
                    ],
                    borderColor: [
                        'rgba(16, 185, 129, 1)',
                        'rgba(239, 68, 68, 1)',
                        'rgba(245, 158, 11, 1)',
                        'rgba(59, 130, 246, 1)',
                        'rgba(139, 92, 246, 1)',
                    ],
                    borderWidth: 2,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 15,
                            font: { size: 12 }
                        }
                    }
                }
            }
        });
    }
    
    // Traffic Status (Bar Chart)
    const trafficCtx = document.getElementById('trafficStatusChart')?.getContext('2d');
    if (trafficCtx) {
        charts.trafficStatus = new Chart(trafficCtx, {
            type: 'bar',
            data: {
                labels: ['Normal', 'Attacks'],
                datasets: [{
                    label: 'Packets',
                    data: [0, 0],
                    backgroundColor: [
                        'rgba(16, 185, 129, 0.8)',
                        'rgba(239, 68, 68, 0.8)',
                    ],
                    borderColor: [
                        'rgba(16, 185, 129, 1)',
                        'rgba(239, 68, 68, 1)',
                    ],
                    borderWidth: 2,
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        grid: { color: 'rgba(45, 58, 95, 0.3)' }
                    },
                    y: {
                        grid: { display: false }
                    }
                }
            }
        });
    }
    
    // Traffic Trend (Line Chart)
    const trendCtx = document.getElementById('trafficTrendChart')?.getContext('2d');
    if (trendCtx) {
        charts.trafficTrend = new Chart(trendCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Normal Traffic',
                        data: [],
                        borderColor: 'rgba(16, 185, 129, 1)',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        borderWidth: 2,
                        tension: 0.4,
                        fill: true,
                        pointRadius: 4,
                        pointBackgroundColor: 'rgba(16, 185, 129, 1)',
                    },
                    {
                        label: 'Attack Traffic',
                        data: [],
                        borderColor: 'rgba(239, 68, 68, 1)',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        borderWidth: 2,
                        tension: 0.4,
                        fill: true,
                        pointRadius: 4,
                        pointBackgroundColor: 'rgba(239, 68, 68, 1)',
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: { padding: 15 }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(45, 58, 95, 0.3)' }
                    },
                    x: {
                        grid: { color: 'rgba(45, 58, 95, 0.3)' }
                    }
                }
            }
        });
    }
}

function updateCharts() {
    if (!charts.attackDistribution) return;
    
    const attackBreakdown = state.stats.attack_breakdown || {};
    
    // Update Attack Distribution
    charts.attackDistribution.data.datasets[0].data = [
        state.stats.normal_packets,
        attackBreakdown.DoS || 0,
        attackBreakdown.Probe || 0,
        attackBreakdown.R2L || 0,
        attackBreakdown.U2R || 0,
    ];
    charts.attackDistribution.update('none');
    
    // Update Traffic Status
    charts.trafficStatus.data.datasets[0].data = [
        state.stats.normal_packets,
        state.stats.attack_packets
    ];
    charts.trafficStatus.update('none');
    
    // Update Traffic Trend
    const timestamp = new Date().toLocaleTimeString();
    
    if (state.chartData.timestamps.length >= CONFIG.MAX_CHART_POINTS) {
        state.chartData.timestamps.shift();
        state.chartData.normalTraffic.shift();
        state.chartData.attackTraffic.shift();
    }
    
    state.chartData.timestamps.push(timestamp);
    state.chartData.normalTraffic.push(state.stats.normal_packets);
    state.chartData.attackTraffic.push(state.stats.attack_packets);
    
    charts.trafficTrend.data.labels = state.chartData.timestamps;
    charts.trafficTrend.data.datasets[0].data = state.chartData.normalTraffic;
    charts.trafficTrend.data.datasets[1].data = state.chartData.attackTraffic;
    charts.trafficTrend.update('none');
}

// ============================================================================
// API CALLS
// ============================================================================

async function fetchStats() {
    try {
        const response = await fetch(`${CONFIG.API_BASE}/stats`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        state.stats = data;
        
        return data;
    } catch (error) {
        console.error('[✗] Failed to fetch stats:', error);
        return null;
    }
}

async function fetchLogs(limit = 50) {
    try {
        const response = await fetch(`${CONFIG.API_BASE}/logs?limit=${limit}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        state.logs = data.logs || [];
        
        return data;
    } catch (error) {
        console.error('[✗] Failed to fetch logs:', error);
        return null;
    }
}

async function fetchAlerts(limit = 50) {
    try {
        const response = await fetch(`${CONFIG.API_BASE}/alerts?limit=${limit}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        state.alerts = data.alerts || [];
        
        return data;
    } catch (error) {
        console.error('[✗] Failed to fetch alerts:', error);
        return null;
    }
}

async function fetchModelInfo() {
    try {
        const response = await fetch(`${CONFIG.API_BASE}/model-info`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        return await response.json();
    } catch (error) {
        console.error('[✗] Failed to fetch model info:', error);
        return null;
    }
}

// ============================================================================
// UI UPDATES
// ============================================================================

function updateKPICards(stats) {
    // Total Traffic
    document.getElementById('totalPackets').textContent = formatNumber(stats.total_packets);
    
    // Normal Traffic
    document.getElementById('normalPackets').textContent = formatNumber(stats.normal_packets);
    document.getElementById('normalPercent').textContent = `${stats.normal_percentage}%`;
    
    // Attacks
    document.getElementById('attackPackets').textContent = formatNumber(stats.attack_packets);
    document.getElementById('attackPercent').textContent = `${stats.attack_percentage}%`;
    
    // Alert Count
    document.getElementById('alertCount').textContent = state.alerts.length;
}

function updateAlertsTable(alerts) {
    const container = document.getElementById('alertsContainer');
    
    if (!alerts || alerts.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <p>No alerts detected</p>
                <span>🟢 System is secure</span>
            </div>
        `;
        return;
    }
    
    container.innerHTML = alerts.slice(0, 10).map(alert => `
        <div class="alert-row">
            <div class="alert-info">
                <div class="alert-type ${alert.type.toLowerCase()}">${alert.type}</div>
                <div class="alert-time">${formatTime(alert.timestamp)}</div>
                <div class="alert-meta">
                    <span>${alert.src_port} → ${alert.dst_port}</span>
                    <span class="severity-badge severity-${alert.severity.toLowerCase()}">${alert.severity}</span>
                </div>
            </div>
            <div class="confidence">${alert.confidence.toFixed(1)}%</div>
        </div>
    `).join('');
    
    document.getElementById('alertBadge').textContent = alerts.length;
}

function updateLogsTable(logs) {
    const container = document.getElementById('logsContainer');
    
    if (!logs || logs.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <p>Waiting for traffic...</p>
                <span>⏳ Analyzing network</span>
            </div>
        `;
        return;
    }
    
    container.innerHTML = logs.slice(0, 15).map(log => `
        <div class="log-row">
            <div class="log-info">
                <div class="attack-type ${log.attack_type.toLowerCase()}">${log.attack_type}</div>
                <div class="log-time">${formatTime(log.timestamp)}</div>
                <div class="log-meta">
                    <span>${log.src_port} → ${log.dst_port}</span>
                    <span>${log.packet_count} packets</span>
                </div>
            </div>
            <div class="confidence">${log.confidence.toFixed(1)}%</div>
        </div>
    `).join('');
    
    document.getElementById('logBadge').textContent = logs.length;
}

async function updateSystemInfo() {
    const modelInfo = await fetchModelInfo();
    
    if (!modelInfo) {
        document.getElementById('systemInfo').innerHTML = '<p>Unable to load system info</p>';
        return;
    }
    
    document.getElementById('systemInfo').innerHTML = `
        <div>
            <span class="info-label">ML Model</span>
            <span class="info-value">${modelInfo.model_type}</span>
        </div>
        <div>
            <span class="info-label">Estimators</span>
            <span class="info-value">${modelInfo.n_estimators}</span>
        </div>
        <div>
            <span class="info-label">Features</span>
            <span class="info-value">${modelInfo.n_features}</span>
        </div>
        <div>
            <span class="info-label">Attack Classes</span>
            <span class="info-value">${modelInfo.classes.join(', ')}</span>
        </div>
    `;
}

function updateLastUpdate() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString();
    document.getElementById('lastUpdate').textContent = `Last update: ${timeStr}`;
}

// ============================================================================
// REALTIME UPDATE LOOP
// ============================================================================

function startRealtimeUpdates() {
    // Initial fetch
    updateAllStats();
    
    // Set up intervals
    setInterval(updateAllStats, CONFIG.REFRESH_INTERVAL);
    setInterval(() => {
        updateCharts();
        updateLastUpdate();
    }, CONFIG.CHART_UPDATE_INTERVAL);
}

async function updateAllStats() {
    // Fetch all data in parallel
    const [statsData, logsData, alertsData] = await Promise.all([
        fetchStats(),
        fetchLogs(50),
        fetchAlerts(50)
    ]);
    
    // Update UI
    if (statsData) updateKPICards(statsData);
    if (logsData) updateLogsTable(logsData.logs);
    if (alertsData) updateAlertsTable(alertsData.alerts);
    
    // Update system info on first load
    if (state.stats.total_packets === 0) {
        updateSystemInfo();
    }
    
    updateLastUpdate();
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function formatNumber(num) {
    return num.toLocaleString('en-US');
}

function formatTime(isoString) {
    try {
        const date = new Date(isoString);
        return date.toLocaleTimeString();
    } catch (e) {
        return isoString;
    }
}

async function resetStats() {
    if (!confirm('Are you sure you want to reset all statistics?')) return;
    
    try {
        const response = await fetch(`${CONFIG.API_BASE}/reset-stats`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (response.ok) {
            // Clear local state
            state.stats = {
                total_packets: 0,
                normal_packets: 0,
                attack_packets: 0,
                attack_breakdown: {}
            };
            state.logs = [];
            state.alerts = [];
            state.chartData = {
                timestamps: [],
                normalTraffic: [],
                attackTraffic: [],
            };
            
            // Update UI
            updateAllStats();
            updateCharts();
            
            console.log('[✓] Statistics reset');
        }
    } catch (error) {
        console.error('[✗] Failed to reset stats:', error);
    }
}

// ============================================================================
// WEBSOCKET SUPPORT (Future Enhancement)
// ============================================================================

// Placeholder for WebSocket connection (future enhancement)
// This would replace polling for real-time updates
function initializeWebSocket() {
    // if (window.location.protocol === 'https:') {
    //     const ws = new WebSocket('wss://localhost:5000/ws');
    // } else {
    //     const ws = new WebSocket('ws://localhost:5000/ws');
    // }
    // 
    // ws.onmessage = (event) => {
    //     const data = JSON.parse(event.data);
    //     // Handle real-time updates
    // };
}

console.log('[✓] Dashboard script loaded');
