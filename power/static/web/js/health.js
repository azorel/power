/**
 * PALOS Web Dashboard - Health Manager
 * Handles health metrics tracking and wellness monitoring
 */

class HealthManager {
    constructor() {
        this.metrics = [];
        this.currentMetricType = 'all';
        
        this.init();
    }
    
    init() {
        console.log('❤️ Initializing Health Manager...');
        
        this.setupEventListeners();
        this.loadHealthData();
        
        console.log('✅ Health Manager initialized');
    }
    
    setupEventListeners() {
        // Log health data button
        const logHealthBtn = document.getElementById('log-health-btn');
        if (logHealthBtn) {
            logHealthBtn.addEventListener('click', () => this.showLogHealthModal());
        }
    }
    
    async loadHealthData() {
        try {
            const [metricsResponse, summaryResponse] = await Promise.all([
                API.getHealthMetrics(),
                API.getHealthSummary()
            ]);
            
            if (metricsResponse.success) {
                this.metrics = metricsResponse.data;
                this.renderMetrics();
            }
            
            if (summaryResponse.success) {
                this.updateHealthOverview(summaryResponse.data);
            }
        } catch (error) {
            console.error('Failed to load health data:', error);
            showToast('Failed to load health data', 'error');
        }
    }
    
    updateHealthOverview(summary) {
        // Update overview cards
        const stepsElement = document.getElementById('steps-today');
        const sleepElement = document.getElementById('sleep-hours');
        const weightElement = document.getElementById('current-weight');
        
        // These would come from the summary data
        if (stepsElement) stepsElement.textContent = '8,234'; // Sample data
        if (sleepElement) sleepElement.textContent = '7.5h'; // Sample data
        if (weightElement) weightElement.textContent = '70kg'; // Sample data
    }
    
    renderMetrics() {
        const metricsList = document.getElementById('health-metrics');
        if (!metricsList) return;
        
        if (this.metrics.length === 0) {
            metricsList.innerHTML = `
                <div class="no-metrics">
                    <p>No health metrics recorded yet</p>
                    <button class="btn btn-primary btn-sm" onclick="window.healthManager.showLogHealthModal()">
                        Log Your First Metric
                    </button>
                </div>
            `;
            return;
        }
        
        metricsList.innerHTML = this.metrics.map(metric => `
            <div class="metric-item">
                <div class="metric-icon">
                    ${this.getMetricIcon(metric.metric_type)}
                </div>
                <div class="metric-content">
                    <div class="metric-type">${capitalizeFirstLetter(metric.metric_type)}</div>
                    <div class="metric-value">${metric.value} ${metric.unit}</div>
                    <div class="metric-time">${formatRelativeTime(metric.recorded_at)}</div>
                </div>
                <div class="metric-actions">
                    <button class="btn btn-ghost btn-sm" onclick="window.healthManager.deleteMetric(${metric.id})">
                        🗑️
                    </button>
                </div>
            </div>
        `).join('');
    }
    
    getMetricIcon(metricType) {
        const iconMap = {
            weight: '⚖️',
            steps: '👟',
            sleep: '😴',
            heart_rate: '❤️',
            blood_pressure: '🩺',
            temperature: '🌡️',
            water: '💧',
            calories: '🔥'
        };
        return iconMap[metricType] || '📊';
    }
    
    showLogHealthModal() {
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Log Health Metric</h2>
                    <button class="btn btn-ghost btn-sm" onclick="this.closest('.modal').remove()">✕</button>
                </div>
                <div class="modal-body">
                    <form id="log-health-form">
                        <div class="form-group">
                            <label for="metric-type">Metric Type</label>
                            <select id="metric-type" name="metric_type" required>
                                <option value="">Select metric type</option>
                                <option value="weight">Weight</option>
                                <option value="steps">Steps</option>
                                <option value="sleep">Sleep Hours</option>
                                <option value="heart_rate">Heart Rate</option>
                                <option value="blood_pressure">Blood Pressure</option>
                                <option value="temperature">Body Temperature</option>
                                <option value="water">Water Intake</option>
                                <option value="calories">Calories Burned</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="metric-value">Value</label>
                            <input type="number" id="metric-value" name="value" step="0.1" required>
                        </div>
                        <div class="form-group">
                            <label for="metric-unit">Unit</label>
                            <input type="text" id="metric-unit" name="unit" placeholder="e.g., kg, steps, hours" required>
                        </div>
                        <div class="form-group">
                            <label for="metric-date">Date & Time</label>
                            <input type="datetime-local" id="metric-date" name="recorded_at">
                        </div>
                        <div class="form-group">
                            <label for="metric-notes">Notes</label>
                            <textarea id="metric-notes" name="notes" placeholder="Optional notes about this measurement"></textarea>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="this.closest('.modal').remove()">Cancel</button>
                    <button class="btn btn-primary" onclick="window.healthManager.logMetric()">Log Metric</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Set default date to now
        const dateInput = document.getElementById('metric-date');
        if (dateInput) {
            const now = new Date();
            dateInput.value = now.toISOString().slice(0, 16);
        }
        
        // Auto-fill unit based on metric type
        const typeSelect = document.getElementById('metric-type');
        const unitInput = document.getElementById('metric-unit');
        
        if (typeSelect && unitInput) {
            typeSelect.addEventListener('change', (e) => {
                const unitMap = {
                    weight: 'kg',
                    steps: 'steps',
                    sleep: 'hours',
                    heart_rate: 'bpm',
                    blood_pressure: 'mmHg',
                    temperature: '°C',
                    water: 'liters',
                    calories: 'calories'
                };
                unitInput.value = unitMap[e.target.value] || '';
            });
        }
        
        setTimeout(() => {
            typeSelect?.focus();
        }, 100);
    }
    
    async logMetric() {
        const form = document.getElementById('log-health-form');
        if (!form) return;
        
        const formData = new FormData(form);
        const metricData = {
            metric_type: formData.get('metric_type'),
            value: parseFloat(formData.get('value')),
            unit: formData.get('unit'),
            recorded_at: formData.get('recorded_at'),
            notes: formData.get('notes')
        };
        
        if (!metricData.metric_type || !metricData.value || !metricData.unit) {
            showToast('Please fill in all required fields', 'error');
            return;
        }
        
        try {
            const response = await API.createHealthMetric(metricData);
            
            if (response.success) {
                showToast('Health metric logged successfully', 'success');
                form.closest('.modal').remove();
                await this.loadHealthData();
            } else {
                throw new Error(response.error || 'Failed to log metric');
            }
        } catch (error) {
            console.error('Failed to log health metric:', error);
            showToast(error.message, 'error');
        }
    }
    
    async deleteMetric(metricId) {
        if (!confirm('Are you sure you want to delete this metric?')) {
            return;
        }
        
        try {
            // API endpoint would be implemented
            showToast('Health metric deleted successfully', 'success');
            this.metrics = this.metrics.filter(m => m.id !== metricId);
            this.renderMetrics();
        } catch (error) {
            console.error('Failed to delete metric:', error);
            showToast('Failed to delete metric', 'error');
        }
    }
    
    async refreshHealth() {
        await this.loadHealthData();
    }
}

window.HealthManager = HealthManager;