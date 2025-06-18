/**
 * PALOS Web Dashboard - AI Agents Manager
 * Handles agent monitoring, delegation, and real-time status updates
 */

class AgentsManager {
    constructor() {
        this.agents = new Map();
        this.activeCollaborations = new Map();
        this.refreshInterval = null;
        this.autoRefreshEnabled = true;
        this.refreshRate = 10000; // 10 seconds for agent status
        this.lastUpdate = null;
        this.selectedAgent = null;
        this.sortBy = 'department';
        this.filterBy = 'all';
        this.viewMode = 'grid'; // 'grid' or 'list'
        
        this.init();
    }
    
    init() {
        console.log('🤖 Initializing Agents Manager...');
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Setup auto-refresh
        this.setupAutoRefresh();
        
        // Setup real-time updates
        this.setupRealTimeUpdates();
        
        // Initialize UI components
        this.initializeUI();
        
        console.log('✅ Agents Manager initialized');
    }
    
    setupEventListeners() {
        // Agent settings button
        const settingsBtn = document.getElementById('agent-settings-btn');
        if (settingsBtn) {
            settingsBtn.addEventListener('click', () => this.showAgentSettings());
        }
        
        // View mode toggles
        const gridViewBtn = document.getElementById('grid-view-btn');
        const listViewBtn = document.getElementById('list-view-btn');
        
        if (gridViewBtn) {
            gridViewBtn.addEventListener('click', () => this.setViewMode('grid'));
        }
        if (listViewBtn) {
            listViewBtn.addEventListener('click', () => this.setViewMode('list'));
        }
        
        // Filter and sort controls
        const filterSelect = document.getElementById('agent-filter');
        const sortSelect = document.getElementById('agent-sort');
        
        if (filterSelect) {
            filterSelect.addEventListener('change', (e) => this.setFilter(e.target.value));
        }
        if (sortSelect) {
            sortSelect.addEventListener('change', (e) => this.setSortBy(e.target.value));
        }
        
        // Delegate task button
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('delegate-task-btn')) {
                const agentId = e.target.dataset.agentId;
                this.showTaskDelegationModal(agentId);
            }
            if (e.target.classList.contains('view-agent-btn')) {
                const agentId = e.target.dataset.agentId;
                this.showAgentDetail(agentId);
            }
            if (e.target.classList.contains('agent-performance-btn')) {
                const agentId = e.target.dataset.agentId;
                this.showPerformanceModal(agentId);
            }
        });
        
        // Create organization button
        const createOrgBtn = document.getElementById('create-organization-btn');
        if (createOrgBtn) {
            createOrgBtn.addEventListener('click', () => this.createFullOrganization());
        }
    }
    
    setupAutoRefresh() {
        if (this.autoRefreshEnabled) {
            this.refreshInterval = setInterval(() => {
                if (this.isVisible()) {
                    this.refreshAgentData();
                }
            }, this.refreshRate);
        }
    }
    
    setupRealTimeUpdates() {
        // Subscribe to agent-related WebSocket events
        if (window.websocketManager) {
            window.websocketManager.subscribe('agent_status_update', (data) => {
                this.handleAgentStatusUpdate(data);
            });
            
            window.websocketManager.subscribe('task_completed', (data) => {
                this.handleTaskCompletion(data);
            });
            
            window.websocketManager.subscribe('collaboration_update', (data) => {
                this.handleCollaborationUpdate(data);
            });
            
            window.websocketManager.subscribe('agent_performance_update', (data) => {
                this.handlePerformanceUpdate(data);
            });
        }
    }
    
    initializeUI() {
        // Add view controls to page header if not exists
        const pageHeader = document.querySelector('#agents-page .page-header');
        if (pageHeader && !document.getElementById('agent-view-controls')) {
            const viewControls = this.createViewControls();
            pageHeader.appendChild(viewControls);
        }
        
        // Add filter controls
        const agentsPage = document.getElementById('agents-page');
        if (agentsPage && !document.getElementById('agent-controls')) {
            const controls = this.createAgentControls();
            const pageHeader = agentsPage.querySelector('.page-header');
            pageHeader.insertAdjacentElement('afterend', controls);
        }
    }
    
    createViewControls() {
        const controls = document.createElement('div');
        controls.id = 'agent-view-controls';
        controls.className = 'view-controls';
        controls.innerHTML = `
            <div class="btn-group">
                <button id="grid-view-btn" class="btn btn-sm ${this.viewMode === 'grid' ? 'btn-primary' : 'btn-ghost'}">
                    <span class="icon icon-grid"></span>
                    Grid
                </button>
                <button id="list-view-btn" class="btn btn-sm ${this.viewMode === 'list' ? 'btn-primary' : 'btn-ghost'}">
                    <span class="icon icon-list"></span>
                    List
                </button>
            </div>
            <button id="create-organization-btn" class="btn btn-sm btn-secondary">
                <span class="icon icon-plus"></span>
                Create Full Organization
            </button>
        `;
        return controls;
    }
    
    createAgentControls() {
        const controls = document.createElement('div');
        controls.id = 'agent-controls';
        controls.className = 'agent-controls';
        controls.innerHTML = `
            <div class="controls-row">
                <div class="control-group">
                    <label for="agent-filter">Filter:</label>
                    <select id="agent-filter" class="form-select">
                        <option value="all">All Agents</option>
                        <option value="executive">Executive</option>
                        <option value="operations">Operations</option>
                        <option value="marketing">Marketing</option>
                        <option value="finance">Finance</option>
                        <option value="technology">Technology</option>
                        <option value="personal_development">Personal Development</option>
                        <option value="active">Active Only</option>
                        <option value="idle">Idle Only</option>
                    </select>
                </div>
                <div class="control-group">
                    <label for="agent-sort">Sort by:</label>
                    <select id="agent-sort" class="form-select">
                        <option value="department">Department</option>
                        <option value="role">Role</option>
                        <option value="performance">Performance</option>
                        <option value="activity">Last Activity</option>
                        <option value="name">Name</option>
                    </select>
                </div>
                <div class="control-group">
                    <button id="refresh-agents-btn" class="btn btn-sm btn-ghost">
                        <span class="icon icon-refresh"></span>
                        Refresh
                    </button>
                </div>
            </div>
        `;
        return controls;
    }
    
    async refreshAgentData() {
        try {
            const response = await api.get('/api/agents');
            if (response.success) {
                this.updateAgentsData(response.data);
                this.lastUpdate = new Date();
            }
        } catch (error) {
            console.error('Error refreshing agent data:', error);
            this.showError('Failed to refresh agent data');
        }
    }
    
    updateAgentsData(agentsData) {
        // Update internal agents map
        this.agents.clear();
        agentsData.forEach(agent => {
            this.agents.set(agent.agent_id, agent);
        });
        
        // Re-render the agents display
        this.renderAgents();
        
        // Update system status
        this.updateSystemStatus();
    }
    
    renderAgents() {
        const agentsGrid = document.getElementById('agents-grid');
        if (!agentsGrid) return;
        
        // Clear existing content
        agentsGrid.innerHTML = '';
        
        // Apply filters and sorting
        const filteredAgents = this.getFilteredAndSortedAgents();
        
        if (filteredAgents.length === 0) {
            agentsGrid.innerHTML = this.getEmptyStateHTML();
            return;
        }
        
        // Set grid class based on view mode
        agentsGrid.className = this.viewMode === 'grid' ? 'agents-grid' : 'agents-list';
        
        // Render each agent
        filteredAgents.forEach(agent => {
            const agentElement = this.createAgentElement(agent);
            agentsGrid.appendChild(agentElement);
        });
    }
    
    getFilteredAndSortedAgents() {
        let agents = Array.from(this.agents.values());
        
        // Apply filters
        if (this.filterBy !== 'all') {
            switch (this.filterBy) {
                case 'active':
                    agents = agents.filter(agent => agent.status === 'active');
                    break;
                case 'idle':
                    agents = agents.filter(agent => agent.status === 'idle');
                    break;
                default:
                    agents = agents.filter(agent => 
                        agent.department.toLowerCase().includes(this.filterBy.toLowerCase())
                    );
            }
        }
        
        // Apply sorting
        agents.sort((a, b) => {
            switch (this.sortBy) {
                case 'department':
                    return a.department.localeCompare(b.department) || a.role.localeCompare(b.role);
                case 'role':
                    return a.role.localeCompare(b.role);
                case 'performance':
                    return (b.performance_score || 0) - (a.performance_score || 0);
                case 'activity':
                    return new Date(b.last_active || 0) - new Date(a.last_active || 0);
                case 'name':
                    return a.name.localeCompare(b.name);
                default:
                    return 0;
            }
        });
        
        return agents;
    }
    
    createAgentElement(agent) {
        const element = document.createElement('div');
        element.className = this.viewMode === 'grid' ? 'agent-card' : 'agent-list-item';
        element.dataset.agentId = agent.agent_id;
        
        const statusClass = this.getStatusClass(agent.status || 'idle');
        const performanceScore = agent.performance_score || 0;
        const lastActive = agent.last_active ? new Date(agent.last_active).toLocaleString() : 'Never';
        
        if (this.viewMode === 'grid') {
            element.innerHTML = `
                <div class="agent-header">
                    <div class="agent-avatar">
                        <span class="agent-initials">${this.getAgentInitials(agent.name)}</span>
                        <div class="status-indicator ${statusClass}"></div>
                    </div>
                    <div class="agent-info">
                        <h3 class="agent-name">${agent.name}</h3>
                        <p class="agent-role">${agent.role}</p>
                        <span class="agent-department">${agent.department}</span>
                    </div>
                </div>
                <div class="agent-stats">
                    <div class="stat">
                        <span class="stat-label">Performance</span>
                        <div class="stat-value">
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${performanceScore * 10}%"></div>
                            </div>
                            <span class="score">${performanceScore.toFixed(1)}</span>
                        </div>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Tasks Completed</span>
                        <span class="stat-value">${agent.tasks_completed || 0}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Last Active</span>
                        <span class="stat-value stat-time">${this.formatRelativeTime(agent.last_active)}</span>
                    </div>
                </div>
                <div class="agent-actions">
                    <button class="btn btn-sm btn-primary delegate-task-btn" data-agent-id="${agent.agent_id}">
                        <span class="icon icon-delegate"></span>
                        Delegate Task
                    </button>
                    <button class="btn btn-sm btn-ghost view-agent-btn" data-agent-id="${agent.agent_id}">
                        <span class="icon icon-eye"></span>
                        View Details
                    </button>
                    <button class="btn btn-sm btn-ghost agent-performance-btn" data-agent-id="${agent.agent_id}">
                        <span class="icon icon-chart"></span>
                        Performance
                    </button>
                </div>
                <div class="agent-skills">
                    <div class="skills-label">Key Skills:</div>
                    <div class="skills-list">
                        ${this.renderSkills(agent.skills)}
                    </div>
                </div>
            `;
        } else {
            element.innerHTML = `
                <div class="list-item-content">
                    <div class="agent-avatar">
                        <span class="agent-initials">${this.getAgentInitials(agent.name)}</span>
                        <div class="status-indicator ${statusClass}"></div>
                    </div>
                    <div class="agent-details">
                        <div class="agent-primary">
                            <h3 class="agent-name">${agent.name}</h3>
                            <span class="agent-role">${agent.role}</span>
                            <span class="agent-department badge">${agent.department}</span>
                        </div>
                        <div class="agent-secondary">
                            <span class="performance">Performance: ${performanceScore.toFixed(1)}/10</span>
                            <span class="tasks">Tasks: ${agent.tasks_completed || 0}</span>
                            <span class="last-active">Active: ${this.formatRelativeTime(agent.last_active)}</span>
                        </div>
                    </div>
                    <div class="agent-actions">
                        <button class="btn btn-sm btn-primary delegate-task-btn" data-agent-id="${agent.agent_id}">
                            Delegate Task
                        </button>
                        <button class="btn btn-sm btn-ghost view-agent-btn" data-agent-id="${agent.agent_id}">
                            View Details
                        </button>
                    </div>
                </div>
            `;
        }
        
        return element;
    }
    
    renderSkills(skills) {
        if (!skills) return '';
        
        return Object.entries(skills)
            .sort(([,a], [,b]) => b - a)
            .slice(0, 3)
            .map(([skill, level]) => `
                <span class="skill-tag" title="${skill}: ${level}/10">
                    ${skill.replace('_', ' ')}
                </span>
            `).join('');
    }
    
    getAgentInitials(name) {
        return name.split(' ').map(word => word[0]).join('').toUpperCase().slice(0, 2);
    }
    
    getStatusClass(status) {
        const statusMap = {
            'active': 'status-active',
            'busy': 'status-busy',
            'idle': 'status-idle',
            'offline': 'status-offline'
        };
        return statusMap[status] || 'status-idle';
    }
    
    formatRelativeTime(timestamp) {
        if (!timestamp) return 'Never';
        
        const now = new Date();
        const time = new Date(timestamp);
        const diffMs = now - time;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);
        
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        return time.toLocaleDateString();
    }
    
    getEmptyStateHTML() {
        return `
            <div class="empty-state">
                <div class="empty-icon">
                    <span class="icon icon-agents"></span>
                </div>
                <h3>No agents found</h3>
                <p>Create your first AI agent to get started with autonomous task management.</p>
                <button class="btn btn-primary" id="create-first-agent-btn">
                    <span class="icon icon-plus"></span>
                    Create Agent
                </button>
            </div>
        `;
    }
    
    setViewMode(mode) {
        this.viewMode = mode;
        
        // Update button states
        const gridBtn = document.getElementById('grid-view-btn');
        const listBtn = document.getElementById('list-view-btn');
        
        if (gridBtn && listBtn) {
            gridBtn.className = `btn btn-sm ${mode === 'grid' ? 'btn-primary' : 'btn-ghost'}`;
            listBtn.className = `btn btn-sm ${mode === 'list' ? 'btn-primary' : 'btn-ghost'}`;
        }
        
        // Re-render agents
        this.renderAgents();
    }
    
    setFilter(filter) {
        this.filterBy = filter;
        this.renderAgents();
    }
    
    setSortBy(sortBy) {
        this.sortBy = sortBy;
        this.renderAgents();
    }
    
    async showTaskDelegationModal(agentId) {
        const agent = this.agents.get(agentId);
        if (!agent) return;
        
        // Create modal for task delegation
        const modal = this.createTaskDelegationModal(agent);
        document.body.appendChild(modal);
        
        // Show modal
        modal.style.display = 'flex';
        
        // Setup form submission
        const form = modal.querySelector('#task-delegation-form');
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.delegateTask(agentId, new FormData(form));
            modal.remove();
        });
        
        // Setup close button
        modal.querySelector('.modal-close').addEventListener('click', () => {
            modal.remove();
        });
    }
    
    createTaskDelegationModal(agent) {
        const modal = document.createElement('div');
        modal.className = 'modal task-delegation-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Delegate Task to ${agent.name}</h2>
                    <button class="modal-close btn btn-ghost">
                        <span class="icon icon-close"></span>
                    </button>
                </div>
                <div class="modal-body">
                    <form id="task-delegation-form">
                        <div class="form-group">
                            <label for="task-description">Task Description</label>
                            <textarea id="task-description" name="task_description" 
                                      placeholder="Describe the task you want to delegate..." 
                                      required rows="4"></textarea>
                        </div>
                        <div class="form-group">
                            <label for="task-priority">Priority</label>
                            <select id="task-priority" name="priority">
                                <option value="1">Low</option>
                                <option value="5" selected>Medium</option>
                                <option value="9">High</option>
                                <option value="10">Critical</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="task-deadline">Deadline (optional)</label>
                            <input type="datetime-local" id="task-deadline" name="deadline">
                        </div>
                        <div class="form-group">
                            <label for="task-skills">Required Skills</label>
                            <input type="text" id="task-skills" name="required_skills" 
                                   placeholder="Comma-separated skills (e.g., analysis, communication)">
                        </div>
                        <div class="agent-compatibility">
                            <h4>Agent Compatibility</h4>
                            <div class="compatibility-score">
                                <span class="score">${this.calculateCompatibilityScore(agent)}%</span>
                                <span class="label">Match Score</span>
                            </div>
                            <div class="agent-skills-preview">
                                <strong>Agent Skills:</strong>
                                ${Object.entries(agent.skills || {})
                                    .map(([skill, level]) => `<span class="skill">${skill}: ${level}/10</span>`)
                                    .join(', ')}
                            </div>
                        </div>
                        <div class="form-actions">
                            <button type="button" class="btn btn-ghost modal-close">Cancel</button>
                            <button type="submit" class="btn btn-primary">
                                <span class="icon icon-delegate"></span>
                                Delegate Task
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        `;
        return modal;
    }
    
    calculateCompatibilityScore(agent) {
        // Simple compatibility calculation based on performance and activity
        const performanceScore = agent.performance_score || 0;
        const activityBonus = agent.status === 'active' ? 10 : 0;
        return Math.min(100, Math.round(performanceScore * 8 + activityBonus));
    }
    
    async delegateTask(agentId, formData) {
        try {
            const taskData = {
                task_description: formData.get('task_description'),
                priority: parseInt(formData.get('priority')),
                deadline: formData.get('deadline') || null,
                required_skills: formData.get('required_skills')
                    .split(',')
                    .map(skill => skill.trim())
                    .filter(skill => skill.length > 0),
                task_type: 'delegated',
                task_id: `task_${Date.now()}`
            };
            
            const response = await api.post(`/api/agents/${agentId}/tasks/assign`, taskData);
            
            if (response.success) {
                this.showSuccess(`Task successfully delegated to ${this.agents.get(agentId).name}`);
                this.refreshAgentData();
            } else {
                this.showError('Failed to delegate task');
            }
        } catch (error) {
            console.error('Error delegating task:', error);
            this.showError('Failed to delegate task');
        }
    }
    
    async showAgentDetail(agentId) {
        try {
            const response = await api.get(`/api/agents/${agentId}`);
            if (response.success) {
                this.openAgentDetailModal(response.data);
            }
        } catch (error) {
            console.error('Error fetching agent details:', error);
            this.showError('Failed to load agent details');
        }
    }
    
    openAgentDetailModal(agentData) {
        const modal = document.createElement('div');
        modal.className = 'modal agent-detail-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>${agentData.profile.name} - Agent Details</h2>
                    <button class="modal-close btn btn-ghost">
                        <span class="icon icon-close"></span>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="agent-detail-content">
                        <div class="detail-section">
                            <h3>Profile</h3>
                            <div class="profile-info">
                                <div class="info-item">
                                    <label>Role:</label>
                                    <span>${agentData.profile.role}</span>
                                </div>
                                <div class="info-item">
                                    <label>Department:</label>
                                    <span>${agentData.profile.department}</span>
                                </div>
                                <div class="info-item">
                                    <label>Authority Level:</label>
                                    <span>${agentData.profile.authority_level}</span>
                                </div>
                                <div class="info-item">
                                    <label>Communication Style:</label>
                                    <span>${agentData.profile.communication_style}</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="detail-section">
                            <h3>Performance Metrics</h3>
                            <div class="performance-metrics">
                                ${this.renderPerformanceMetrics(agentData.performance)}
                            </div>
                        </div>
                        
                        <div class="detail-section">
                            <h3>Learning Progress</h3>
                            <div class="learning-progress">
                                ${this.renderLearningProgress(agentData.learning_progress)}
                            </div>
                        </div>
                        
                        <div class="detail-section">
                            <h3>Expertise Domains</h3>
                            <div class="expertise-domains">
                                ${agentData.profile.expertise_domains.map(domain => 
                                    `<span class="domain-tag">${domain.replace('_', ' ')}</span>`
                                ).join('')}
                            </div>
                        </div>
                        
                        <div class="detail-section">
                            <h3>Skills</h3>
                            <div class="skills-breakdown">
                                ${this.renderSkillsBreakdown(agentData.profile.skills)}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        modal.style.display = 'flex';
        
        modal.querySelector('.modal-close').addEventListener('click', () => {
            modal.remove();
        });
    }
    
    renderPerformanceMetrics(performance) {
        if (!performance) return '<p>No performance data available</p>';
        
        return `
            <div class="metrics-grid">
                <div class="metric">
                    <label>Overall Score</label>
                    <div class="metric-value">${performance.overall_score || 0}/10</div>
                </div>
                <div class="metric">
                    <label>Tasks Completed</label>
                    <div class="metric-value">${performance.tasks_completed || 0}</div>
                </div>
                <div class="metric">
                    <label>Success Rate</label>
                    <div class="metric-value">${Math.round((performance.success_rate || 0) * 100)}%</div>
                </div>
                <div class="metric">
                    <label>Avg. Completion Time</label>
                    <div class="metric-value">${performance.avg_completion_time || 0}h</div>
                </div>
            </div>
        `;
    }
    
    renderLearningProgress(learning) {
        if (!learning) return '<p>No learning data available</p>';
        
        return `
            <div class="learning-items">
                ${learning.recent_learnings ? learning.recent_learnings.map(item => `
                    <div class="learning-item">
                        <span class="learning-topic">${item.topic}</span>
                        <span class="learning-progress">${item.progress}%</span>
                    </div>
                `).join('') : '<p>No recent learning activity</p>'}
            </div>
        `;
    }
    
    renderSkillsBreakdown(skills) {
        if (!skills) return '<p>No skills data available</p>';
        
        return Object.entries(skills)
            .sort(([,a], [,b]) => b - a)
            .map(([skill, level]) => `
                <div class="skill-item">
                    <div class="skill-info">
                        <span class="skill-name">${skill.replace('_', ' ')}</span>
                        <span class="skill-level">${level}/10</span>
                    </div>
                    <div class="skill-bar">
                        <div class="skill-fill" style="width: ${level * 10}%"></div>
                    </div>
                </div>
            `).join('');
    }
    
    async createFullOrganization() {
        try {
            const response = await api.post('/api/agents/create-organization');
            if (response.success) {
                this.showSuccess(`Created organization with ${Object.keys(response.data).length} agents`);
                this.refreshAgentData();
            } else {
                this.showError('Failed to create organization');
            }
        } catch (error) {
            console.error('Error creating organization:', error);
            this.showError('Failed to create organization');
        }
    }
    
    updateSystemStatus() {
        // Update system status display
        const statusElement = document.getElementById('agent-system-status');
        if (statusElement) {
            const totalAgents = this.agents.size;
            const activeAgents = Array.from(this.agents.values())
                .filter(agent => agent.status === 'active').length;
            
            statusElement.innerHTML = `
                <div class="system-status">
                    <span class="status-item">
                        <strong>${totalAgents}</strong> Total Agents
                    </span>
                    <span class="status-item">
                        <strong>${activeAgents}</strong> Active
                    </span>
                    <span class="status-item">
                        Last Updated: ${this.lastUpdate ? this.lastUpdate.toLocaleTimeString() : 'Never'}
                    </span>
                </div>
            `;
        }
    }
    
    handleAgentStatusUpdate(data) {
        const agent = this.agents.get(data.agent_id);
        if (agent) {
            agent.status = data.status;
            agent.last_active = data.timestamp;
            this.renderAgents();
        }
    }
    
    handleTaskCompletion(data) {
        const agent = this.agents.get(data.agent_id);
        if (agent) {
            agent.tasks_completed = (agent.tasks_completed || 0) + 1;
            agent.performance_score = data.performance_score;
            this.renderAgents();
        }
        
        // Show notification
        this.showNotification(`Task completed by ${agent ? agent.name : 'Agent'}`, data.task_description);
    }
    
    handleCollaborationUpdate(data) {
        this.activeCollaborations.set(data.session_id, data);
        // Update collaboration displays if visible
    }
    
    handlePerformanceUpdate(data) {
        const agent = this.agents.get(data.agent_id);
        if (agent) {
            agent.performance_score = data.performance_score;
            this.renderAgents();
        }
    }
    
    isVisible() {
        const agentsPage = document.getElementById('agents-page');
        return agentsPage && agentsPage.classList.contains('active');
    }
    
    showError(message) {
        if (window.notifications) {
            window.notifications.showError(message);
        } else {
            console.error(message);
        }
    }
    
    showSuccess(message) {
        if (window.notifications) {
            window.notifications.showSuccess(message);
        } else {
            console.log(message);
        }
    }
    
    showNotification(title, message) {
        if (window.notifications) {
            window.notifications.show({
                title: title,
                message: message,
                type: 'info'
            });
        }
    }
    
    // Public methods for external access
    onPageShow() {
        this.refreshAgentData();
    }
    
    onPageHide() {
        // Cleanup if needed
    }
    
    destroy() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
    }
}

// Initialize agents manager when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.agentsManager = new AgentsManager();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AgentsManager;
}