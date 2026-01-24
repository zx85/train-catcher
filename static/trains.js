const API_URL = '/trains';  // current trains live data
const REFRESH_INTERVAL = 5000; // 5 seconds

let currentTrainData = {};

async function fetchTrains() {
    try {
        const response = await fetch(API_URL);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        currentTrainData = data['trains'];
        signalmaps_url = data['metadata']['signalmaps_url']
        updateTable(currentTrainData);
        updateTimestamp();
        hideError();
    } catch (error) {
        console.error('Error fetching trains:', error);
        showError(`Failed to fetch train data: ${error.message}`);
    }
}

function updateTable(trains) {
    const tbody = document.getElementById('trainsBody');
    const emptyState = document.getElementById('emptyState');
    const table = document.getElementById('trainsTable');
    const trainCount = document.getElementById('trainCount');

    const trainArray = Object.entries(trains).map(([headcode, data]) => ({
        headcode,
        ...data
    }));

    const trainCountContainer = document.querySelector('.train-count');
    trainCount.textContent = `${trainArray.length} ${trainArray.length === 1 ? 'train' : 'trains'}`;;
    
    if (trainArray.length === 0) {
        table.style.display = 'none';
        trainCountContainer.style.display = 'none';
        emptyState.style.display = 'block';
        return;
    }
    trainCountContainer.style.display = 'block';
    table.style.display = 'table';
    emptyState.style.display = 'none';

    const link = document.querySelector('#signalmaps-url a');
    if (link) {
        link.href = signalmaps_url || 'https://signalmaps.co.uk';
    }

    tbody.innerHTML = trainArray.map(train => `
        <tr>
            <td class="headcode">${getHeadcodeLink(train)}</td>
            <td>${escapeHtml(train.location || '-')}</td>
            <td><div class="direction">${escapeHtml(train.direction || '?')}</div></td>
            <td><button class="type-button" onclick="showTrainDetails('${escapeHtml(train.headcode)}')">${escapeHtml(train.type || '-')}</button></td>
            <td>${escapeHtml(train.origin || '-')}</td>
            <td>${escapeHtml(train.destination || '-')}</td>
            <td class="timestamp">${formatTime(train.timestamp)}</td>
        </tr>
    `).join('');
}

function showTrainDetails(headcode) {
    const train = currentTrainData[headcode];
    if (!train) return;

    // Check if service data exists
    const hasServiceData = train.type || train.atoc || train.power || train.speed;
    
    document.getElementById('modalHeadcode').textContent = `Train ${headcode} - Details`;
    document.getElementById('serviceDetailsSection').style.display = hasServiceData ? 'block' : 'none';
    document.getElementById('noServiceDataSection').style.display = hasServiceData ? 'none' : 'block';
    
    if (hasServiceData) {
        document.getElementById('modalType').textContent = escapeHtml(train.type || '-');
        document.getElementById('modalAtoc').textContent = escapeHtml(train.atoc || '-');
        document.getElementById('modalPower').textContent = escapeHtml(train.power || '-');
        document.getElementById('modalSpeed').textContent = escapeHtml(train.speed || '-');
    }

    document.getElementById('detailsModal').classList.add('show');
}

function getHeadcodeLink(train) {
    if (train.train_uid) {
        const today = new Date().toISOString().split('T')[0];
        const url = `https://www.realtimetrains.co.uk/train/${escapeHtml(train.train_uid)}/${today}/detailed`;
        return `<a href="${url}" target="_blank" style="color: #667eea; text-decoration: none;">${escapeHtml(train.headcode)}</a>`;
    }
    return escapeHtml(train.headcode);
}

function closeModal() {
    document.getElementById('detailsModal').classList.remove('show');
}

function showHistory() {
    document.getElementById('historyModal').classList.add('show');
}

function closeHistoryModal() {
    document.getElementById('historyModal').classList.remove('show');
}

// Close modal when clicking outside
window.onclick = function(event) {
    const detailsModal = document.getElementById('detailsModal');
    const historyModal = document.getElementById('historyModal');
    if (event.target === detailsModal) {
        closeModal();
    }
    if (event.target === historyModal) {
        closeHistoryModal();
    }
}

function updateTimestamp() {
    const now = new Date();
    document.getElementById('lastUpdate').textContent = now.toLocaleTimeString();
}

function formatTime(timestamp) {
    if (!timestamp) return '-';
    try {
        return new Date(timestamp).toLocaleTimeString();
    } catch {
        return timestamp;
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showError(message) {
    const errorDiv = document.getElementById('error');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
}

function hideError() {
    document.getElementById('error').style.display = 'none';
}

function updateHistory() {
    fetch('/history')
        .then(response => response.json())
        .then(data => {
            const tbody = document.querySelector('#history-table tbody');
            tbody.innerHTML = ''; // Clear existing rows
            
            data.history.slice(0, 15).forEach(row => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${row.timestamp}</td>
                    <td>${row.headcode}</td>
                    <td>${row.location}</td>
                    <td>${row.direction || '-'}</td>
                    <td>${row.event}</td>
                `;
                tbody.appendChild(tr);
            });
        });
}

// Initial load
fetchTrains();
updateHistory();

// Set up auto-refresh
setInterval(fetchTrains, REFRESH_INTERVAL);
setInterval(updateHistory, REFRESH_INTERVAL);
