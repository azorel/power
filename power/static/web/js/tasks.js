/**
 * PALOS Web Dashboard - Tasks Manager
 * Handles task management and productivity tracking
 */

class TasksManager {
    constructor() {
        this.tasks = [];
        this.currentFilter = 'all';
        this.draggedTask = null;
        
        this.init();
    }
    
    init() {
        console.log('✅ Initializing Tasks Manager...');
        
        this.setupEventListeners();
        this.loadTasks();
        
        console.log('✅ Tasks Manager initialized');
    }
    
    setupEventListeners() {
        // Add task button
        const addTaskBtn = document.getElementById('add-task-btn');
        if (addTaskBtn) {
            addTaskBtn.addEventListener('click', () => this.showAddTaskModal());
        }
        
        // Filter buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('filter-btn')) {
                const filter = e.target.getAttribute('data-filter');
                this.setFilter(filter);
            }
        });
        
        // Task actions
        document.addEventListener('click', (e) => {
            if (e.target.closest('[data-task-action]')) {
                const action = e.target.getAttribute('data-task-action');
                const taskId = parseInt(e.target.closest('[data-task-id]').getAttribute('data-task-id'));
                this.handleTaskAction(action, taskId);
            }
        });
    }
    
    async loadTasks() {
        try {
            const response = await API.getTasks({ status: this.currentFilter === 'all' ? undefined : this.currentFilter });
            
            if (response.success) {
                this.tasks = response.data;
                this.renderTasks();
            }
        } catch (error) {
            console.error('Failed to load tasks:', error);
            showToast('Failed to load tasks', 'error');
        }
    }
    
    renderTasks() {
        const taskList = document.getElementById('task-list');
        if (!taskList) return;
        
        const filteredTasks = this.getFilteredTasks();
        
        if (filteredTasks.length === 0) {
            taskList.innerHTML = `
                <div class="no-tasks">
                    <p>No tasks found</p>
                    <button class="btn btn-primary btn-sm" onclick="window.tasksManager.showAddTaskModal()">
                        Add Your First Task
                    </button>
                </div>
            `;
            return;
        }
        
        taskList.innerHTML = filteredTasks.map(task => `
            <div class="task-item ${task.status}" data-task-id="${task.id}" draggable="true">
                <div class="task-checkbox">
                    <input type="checkbox" ${task.status === 'completed' ? 'checked' : ''} 
                           data-task-action="toggle" />
                </div>
                <div class="task-content">
                    <div class="task-title">${task.title}</div>
                    ${task.description ? `<div class="task-description">${truncateString(task.description, 80)}</div>` : ''}
                    <div class="task-meta">
                        ${task.due_date ? `<span class="task-due">Due: ${formatDate(task.due_date)}</span>` : ''}
                        ${task.category ? `<span class="task-category">${task.category}</span>` : ''}
                        <span class="task-priority priority-${task.priority}">Priority ${task.priority}</span>
                    </div>
                </div>
                <div class="task-actions">
                    <button class="btn btn-ghost btn-sm" data-task-action="edit" title="Edit">✏️</button>
                    <button class="btn btn-ghost btn-sm" data-task-action="delete" title="Delete">🗑️</button>
                </div>
            </div>
        `).join('');
        
        // Setup drag and drop
        this.setupDragAndDrop();
    }
    
    getFilteredTasks() {
        if (this.currentFilter === 'all') {
            return this.tasks;
        }
        return this.tasks.filter(task => task.status === this.currentFilter);
    }
    
    setFilter(filter) {
        this.currentFilter = filter;
        
        // Update filter button states
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.toggle('active', btn.getAttribute('data-filter') === filter);
        });
        
        this.renderTasks();
    }
    
    setupDragAndDrop() {
        const taskItems = document.querySelectorAll('.task-item');
        
        taskItems.forEach(item => {
            item.addEventListener('dragstart', (e) => {
                this.draggedTask = parseInt(item.getAttribute('data-task-id'));
                item.classList.add('dragging');
            });
            
            item.addEventListener('dragend', (e) => {
                item.classList.remove('dragging');
                this.draggedTask = null;
            });
            
            item.addEventListener('dragover', (e) => {
                e.preventDefault();
            });
            
            item.addEventListener('drop', (e) => {
                e.preventDefault();
                if (this.draggedTask) {
                    this.reorderTasks(this.draggedTask, parseInt(item.getAttribute('data-task-id')));
                }
            });
        });
    }
    
    async reorderTasks(draggedId, targetId) {
        // Implementation for reordering tasks
        console.log('Reorder task', draggedId, 'to position of', targetId);
        showToast('Task reordering coming soon', 'info');
    }
    
    async handleTaskAction(action, taskId) {
        const task = this.tasks.find(t => t.id === taskId);
        if (!task) return;
        
        switch (action) {
            case 'toggle':
                await this.toggleTask(taskId);
                break;
            case 'edit':
                this.editTask(taskId);
                break;
            case 'delete':
                await this.deleteTask(taskId);
                break;
        }
    }
    
    async toggleTask(taskId) {
        const task = this.tasks.find(t => t.id === taskId);
        if (!task) return;
        
        const newStatus = task.status === 'completed' ? 'pending' : 'completed';
        
        try {
            const response = await API.updateTask(taskId, { status: newStatus });
            
            if (response.success) {
                task.status = newStatus;
                this.renderTasks();
                showToast(`Task ${newStatus}`, 'success');
            }
        } catch (error) {
            console.error('Failed to update task:', error);
            showToast('Failed to update task', 'error');
        }
    }
    
    showAddTaskModal() {
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Add Task</h2>
                    <button class="btn btn-ghost btn-sm" onclick="this.closest('.modal').remove()">✕</button>
                </div>
                <div class="modal-body">
                    <form id="add-task-form">
                        <div class="form-group">
                            <label for="task-title">Title</label>
                            <input type="text" id="task-title" name="title" required>
                        </div>
                        <div class="form-group">
                            <label for="task-description">Description</label>
                            <textarea id="task-description" name="description"></textarea>
                        </div>
                        <div class="form-group">
                            <label for="task-category">Category</label>
                            <select id="task-category" name="category">
                                <option value="">Select category</option>
                                <option value="work">Work</option>
                                <option value="personal">Personal</option>
                                <option value="health">Health</option>
                                <option value="finance">Finance</option>
                                <option value="other">Other</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="task-priority">Priority</label>
                            <select id="task-priority" name="priority">
                                <option value="1">Low (1)</option>
                                <option value="2">Medium-Low (2)</option>
                                <option value="3" selected>Medium (3)</option>
                                <option value="4">Medium-High (4)</option>
                                <option value="5">High (5)</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="task-due-date">Due Date</label>
                            <input type="date" id="task-due-date" name="due_date">
                        </div>
                        <div class="form-group">
                            <label for="task-duration">Estimated Duration (minutes)</label>
                            <input type="number" id="task-duration" name="estimated_duration" min="1">
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="this.closest('.modal').remove()">Cancel</button>
                    <button class="btn btn-primary" onclick="window.tasksManager.createTask()">Add Task</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Focus title input
        setTimeout(() => {
            document.getElementById('task-title')?.focus();
        }, 100);
    }
    
    async createTask() {
        const form = document.getElementById('add-task-form');
        if (!form) return;
        
        const formData = new FormData(form);
        const taskData = {
            title: formData.get('title'),
            description: formData.get('description'),
            category: formData.get('category'),
            priority: parseInt(formData.get('priority')),
            due_date: formData.get('due_date') || null,
            estimated_duration: formData.get('estimated_duration') ? parseInt(formData.get('estimated_duration')) : null
        };
        
        if (!taskData.title) {
            showToast('Please enter a task title', 'error');
            return;
        }
        
        try {
            const response = await API.createTask(taskData);
            
            if (response.success) {
                showToast('Task created successfully', 'success');
                form.closest('.modal').remove();
                await this.loadTasks();
            } else {
                throw new Error(response.error || 'Failed to create task');
            }
        } catch (error) {
            console.error('Failed to create task:', error);
            showToast(error.message, 'error');
        }
    }
    
    editTask(taskId) {
        // Similar to add modal but with pre-filled data
        console.log('Edit task:', taskId);
        showToast('Edit functionality coming soon', 'info');
    }
    
    async deleteTask(taskId) {
        if (!confirm('Are you sure you want to delete this task?')) {
            return;
        }
        
        try {
            const response = await API.deleteTask(taskId);
            
            if (response.success) {
                showToast('Task deleted successfully', 'success');
                this.tasks = this.tasks.filter(t => t.id !== taskId);
                this.renderTasks();
            } else {
                throw new Error(response.error || 'Failed to delete task');
            }
        } catch (error) {
            console.error('Failed to delete task:', error);
            showToast(error.message, 'error');
        }
    }
    
    async refreshTasks() {
        await this.loadTasks();
    }
}

window.TasksManager = TasksManager;