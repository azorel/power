/**
 * PALOS Web Dashboard - Calendar Manager
 * Handles calendar functionality and event management
 */

class CalendarManager {
    constructor() {
        this.currentDate = new Date();
        this.events = [];
        this.selectedDate = null;
        this.viewMode = 'month'; // month, week, day
        
        this.init();
    }
    
    init() {
        console.log('📅 Initializing Calendar Manager...');
        
        this.setupCalendar();
        this.setupEventListeners();
        this.loadCalendarData();
        
        console.log('✅ Calendar Manager initialized');
    }
    
    setupCalendar() {
        this.renderCalendar();
    }
    
    setupEventListeners() {
        // Navigation buttons
        const prevBtn = document.getElementById('prev-month');
        const nextBtn = document.getElementById('next-month');
        
        if (prevBtn) {
            prevBtn.addEventListener('click', () => this.previousMonth());
        }
        
        if (nextBtn) {
            nextBtn.addEventListener('click', () => this.nextMonth());
        }
        
        // Add event button
        const addEventBtn = document.getElementById('add-event-btn');
        if (addEventBtn) {
            addEventBtn.addEventListener('click', () => this.showAddEventModal());
        }
        
        // Calendar date clicks
        document.addEventListener('click', (e) => {
            if (e.target.closest('.calendar-date')) {
                const dateElement = e.target.closest('.calendar-date');
                const date = dateElement.getAttribute('data-date');
                this.selectDate(date);
            }
        });
    }
    
    async loadCalendarData() {
        try {
            const startDate = new Date(this.currentDate.getFullYear(), this.currentDate.getMonth(), 1);
            const endDate = new Date(this.currentDate.getFullYear(), this.currentDate.getMonth() + 1, 0);
            
            const response = await API.getCalendarEvents(
                startDate.toISOString().split('T')[0],
                endDate.toISOString().split('T')[0]
            );
            
            if (response.success) {
                this.events = response.data;
                this.renderEvents();
            }
        } catch (error) {
            console.error('Failed to load calendar data:', error);
            showToast('Failed to load calendar events', 'error');
        }
    }
    
    renderCalendar() {
        const calendarGrid = document.getElementById('calendar-grid');
        const currentMonthElement = document.getElementById('current-month');
        
        if (!calendarGrid || !currentMonthElement) return;
        
        // Update month/year display
        currentMonthElement.textContent = this.currentDate.toLocaleDateString('en-US', {
            month: 'long',
            year: 'numeric'
        });
        
        // Clear existing calendar
        calendarGrid.innerHTML = '';
        
        // Add day headers
        const dayHeaders = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        dayHeaders.forEach(day => {
            const dayHeader = document.createElement('div');
            dayHeader.className = 'calendar-day-header';
            dayHeader.textContent = day;
            calendarGrid.appendChild(dayHeader);
        });
        
        // Get first day of month and days in month
        const firstDay = getFirstDayOfMonth(this.currentDate.getFullYear(), this.currentDate.getMonth());
        const daysInMonth = getDaysInMonth(this.currentDate.getFullYear(), this.currentDate.getMonth());
        
        // Add empty cells for days before month starts
        for (let i = 0; i < firstDay; i++) {
            const emptyDay = document.createElement('div');
            emptyDay.className = 'calendar-date empty';
            calendarGrid.appendChild(emptyDay);
        }
        
        // Add days of the month
        for (let day = 1; day <= daysInMonth; day++) {
            const dateElement = document.createElement('div');
            dateElement.className = 'calendar-date';
            
            const currentDate = new Date(this.currentDate.getFullYear(), this.currentDate.getMonth(), day);
            const dateString = currentDate.toISOString().split('T')[0];
            
            dateElement.setAttribute('data-date', dateString);
            dateElement.innerHTML = `
                <span class="date-number">${day}</span>
                <div class="date-events"></div>
            `;
            
            // Highlight today
            if (isToday(currentDate)) {
                dateElement.classList.add('today');
            }
            
            // Highlight selected date
            if (this.selectedDate === dateString) {
                dateElement.classList.add('selected');
            }
            
            calendarGrid.appendChild(dateElement);
        }
        
        // Render events on calendar
        this.renderEvents();
    }
    
    renderEvents() {
        // Clear existing event displays
        document.querySelectorAll('.date-events').forEach(container => {
            container.innerHTML = '';
        });
        
        // Add events to calendar dates
        this.events.forEach(event => {
            const eventDate = new Date(event.start_time).toISOString().split('T')[0];
            const dateElement = document.querySelector(`[data-date="${eventDate}"]`);
            
            if (dateElement) {
                const eventsContainer = dateElement.querySelector('.date-events');
                const eventElement = document.createElement('div');
                eventElement.className = `event-dot ${event.category || 'default'}`;
                eventElement.title = event.title;
                eventsContainer.appendChild(eventElement);
            }
        });
        
        // Update events list
        this.renderEventsList();
    }
    
    renderEventsList() {
        const eventsList = document.getElementById('events-list');
        if (!eventsList) return;
        
        // Filter events for current month
        const monthStart = new Date(this.currentDate.getFullYear(), this.currentDate.getMonth(), 1);
        const monthEnd = new Date(this.currentDate.getFullYear(), this.currentDate.getMonth() + 1, 0);
        
        const monthEvents = this.events.filter(event => {
            const eventDate = new Date(event.start_time);
            return eventDate >= monthStart && eventDate <= monthEnd;
        });
        
        if (monthEvents.length === 0) {
            eventsList.innerHTML = `
                <div class="no-events">
                    <p>No events this month</p>
                    <button class="btn btn-primary btn-sm" onclick="window.calendarManager.showAddEventModal()">
                        Add Event
                    </button>
                </div>
            `;
            return;
        }
        
        // Sort events by date
        monthEvents.sort((a, b) => new Date(a.start_time) - new Date(b.start_time));
        
        eventsList.innerHTML = monthEvents.map(event => `
            <div class="event-item" data-event-id="${event.id}">
                <div class="event-time">
                    ${formatDateTime(event.start_time, { 
                        month: 'short', 
                        day: 'numeric', 
                        hour: 'numeric', 
                        minute: '2-digit' 
                    })}
                </div>
                <div class="event-details">
                    <div class="event-title">${event.title}</div>
                    ${event.description ? `<div class="event-description">${truncateString(event.description, 60)}</div>` : ''}
                    ${event.location ? `<div class="event-location">📍 ${event.location}</div>` : ''}
                </div>
                <div class="event-actions">
                    <button class="btn btn-ghost btn-sm" onclick="window.calendarManager.editEvent(${event.id})">
                        Edit
                    </button>
                    <button class="btn btn-ghost btn-sm" onclick="window.calendarManager.deleteEvent(${event.id})">
                        Delete
                    </button>
                </div>
            </div>
        `).join('');
    }
    
    previousMonth() {
        this.currentDate.setMonth(this.currentDate.getMonth() - 1);
        this.renderCalendar();
        this.loadCalendarData();
    }
    
    nextMonth() {
        this.currentDate.setMonth(this.currentDate.getMonth() + 1);
        this.renderCalendar();
        this.loadCalendarData();
    }
    
    selectDate(dateString) {
        // Remove previous selection
        document.querySelectorAll('.calendar-date.selected').forEach(el => {
            el.classList.remove('selected');
        });
        
        // Add selection to new date
        const dateElement = document.querySelector(`[data-date="${dateString}"]`);
        if (dateElement) {
            dateElement.classList.add('selected');
            this.selectedDate = dateString;
        }
        
        // Show events for selected date
        this.showDayEvents(dateString);
    }
    
    showDayEvents(dateString) {
        const dayEvents = this.events.filter(event => {
            return new Date(event.start_time).toISOString().split('T')[0] === dateString;
        });
        
        // You could show a modal or sidebar with day events here
        console.log('Events for', dateString, dayEvents);
    }
    
    showAddEventModal() {
        // Create modal for adding events
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Add Event</h2>
                    <button class="btn btn-ghost btn-sm" onclick="this.closest('.modal').remove()">✕</button>
                </div>
                <div class="modal-body">
                    <form id="add-event-form">
                        <div class="form-group">
                            <label for="event-title">Title</label>
                            <input type="text" id="event-title" name="title" required>
                        </div>
                        <div class="form-group">
                            <label for="event-description">Description</label>
                            <textarea id="event-description" name="description"></textarea>
                        </div>
                        <div class="form-group">
                            <label for="event-location">Location</label>
                            <input type="text" id="event-location" name="location">
                        </div>
                        <div class="form-group">
                            <label for="event-start">Start Date & Time</label>
                            <input type="datetime-local" id="event-start" name="start_time" required>
                        </div>
                        <div class="form-group">
                            <label for="event-end">End Date & Time</label>
                            <input type="datetime-local" id="event-end" name="end_time" required>
                        </div>
                        <div class="form-group">
                            <label for="event-category">Category</label>
                            <select id="event-category" name="category">
                                <option value="">Select category</option>
                                <option value="work">Work</option>
                                <option value="personal">Personal</option>
                                <option value="health">Health</option>
                                <option value="social">Social</option>
                                <option value="other">Other</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label class="checkbox-label">
                                <input type="checkbox" id="event-all-day" name="all_day">
                                <span class="checkmark"></span>
                                All day event
                            </label>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="this.closest('.modal').remove()">Cancel</button>
                    <button class="btn btn-primary" onclick="window.calendarManager.createEvent()">Add Event</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Set default date to selected date or today
        const defaultDate = this.selectedDate || new Date().toISOString().split('T')[0];
        const startInput = document.getElementById('event-start');
        const endInput = document.getElementById('event-end');
        
        if (startInput && endInput) {
            startInput.value = `${defaultDate}T09:00`;
            endInput.value = `${defaultDate}T10:00`;
        }
        
        // Focus title input
        setTimeout(() => {
            document.getElementById('event-title')?.focus();
        }, 100);
    }
    
    async createEvent() {
        const form = document.getElementById('add-event-form');
        if (!form) return;
        
        const formData = new FormData(form);
        const eventData = {
            title: formData.get('title'),
            description: formData.get('description'),
            location: formData.get('location'),
            start_time: formData.get('start_time'),
            end_time: formData.get('end_time'),
            category: formData.get('category'),
            all_day: formData.get('all_day') === 'on'
        };
        
        // Validate required fields
        if (!eventData.title || !eventData.start_time || !eventData.end_time) {
            showToast('Please fill in all required fields', 'error');
            return;
        }
        
        try {
            const response = await API.createCalendarEvent(eventData);
            
            if (response.success) {
                showToast('Event created successfully', 'success');
                
                // Close modal
                form.closest('.modal').remove();
                
                // Refresh calendar
                await this.loadCalendarData();
            } else {
                throw new Error(response.error || 'Failed to create event');
            }
        } catch (error) {
            console.error('Failed to create event:', error);
            showToast(error.message, 'error');
        }
    }
    
    async editEvent(eventId) {
        const event = this.events.find(e => e.id === eventId);
        if (!event) return;
        
        // Similar to showAddEventModal but with pre-filled data
        // Implementation would be similar to add modal but with edit functionality
        console.log('Edit event:', event);
        showToast('Edit functionality coming soon', 'info');
    }
    
    async deleteEvent(eventId) {
        if (!confirm('Are you sure you want to delete this event?')) {
            return;
        }
        
        try {
            const response = await API.deleteCalendarEvent(eventId);
            
            if (response.success) {
                showToast('Event deleted successfully', 'success');
                
                // Remove from local events array
                this.events = this.events.filter(e => e.id !== eventId);
                
                // Re-render calendar
                this.renderEvents();
            } else {
                throw new Error(response.error || 'Failed to delete event');
            }
        } catch (error) {
            console.error('Failed to delete event:', error);
            showToast(error.message, 'error');
        }
    }
    
    async refreshCalendar() {
        await this.loadCalendarData();
    }
    
    // View mode switching (for future enhancement)
    setViewMode(mode) {
        this.viewMode = mode;
        // Implement different view modes (week, day, agenda)
    }
    
    // Export calendar data
    exportCalendar() {
        // Implementation for exporting calendar to ICS format
        showToast('Export functionality coming soon', 'info');
    }
    
    // Import calendar data
    importCalendar() {
        // Implementation for importing ICS files
        showToast('Import functionality coming soon', 'info');
    }
}

// Export for use in other modules
window.CalendarManager = CalendarManager;