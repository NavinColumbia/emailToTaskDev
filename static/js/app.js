// Main JavaScript functionality for Taskflow app

// Utility functions
const utils = {
    // Show alert messages
    showAlert: function(message, type = 'info', duration = 5000) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('main.container');
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-dismiss after specified duration
        setTimeout(() => {
            const alert = bootstrap.Alert.getOrCreateInstance(alertDiv);
            alert.close();
        }, duration);
    },

    // Save settings to localStorage
    saveSettings: function(settings) {
        localStorage.setItem('emailToTaskSettings', JSON.stringify(settings));
    },

    // Load settings from localStorage
    loadSettings: function() {
        const savedSettings = localStorage.getItem('emailToTaskSettings');
        return savedSettings ? JSON.parse(savedSettings) : {};
    },

    // Apply settings to form elements
    applySettings: function(settings) {
        Object.keys(settings).forEach(key => {
            const element = document.getElementById(key);
            if (element) {
                element.value = settings[key];
            }
        });
    },

    // Get form data as object
    getFormData: function(formId) {
        const form = document.getElementById(formId);
        const formData = new FormData(form);
        return Object.fromEntries(formData);
    },

    // Format date
    formatDate: function(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    },

    // Debounce function
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};

// Settings management
const settingsManager = {
    show: function() {
        const modal = new bootstrap.Modal(document.getElementById('settingsModal'));
        modal.show();
    },

    save: function() {
        const form = document.getElementById('settingsForm');
        const settings = utils.getFormData('settingsForm');
        
        utils.saveSettings(settings);
        
        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('settingsModal'));
        modal.hide();
        
        utils.showAlert('Settings saved successfully!', 'success');
    },

    load: function() {
        const settings = utils.loadSettings();
        utils.applySettings(settings);
        return settings;
    }
};

// Email processing
const emailProcessor = {
    fetch: async function(params) {
        const queryString = new URLSearchParams(params).toString();
        
        try {
            const response = await fetch(`/api/fetch-emails?${queryString}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json, text/html'
                }
            });
            
            // Check if response is a redirect (status 302)
            if (response.redirected || response.status === 302) {
                window.location.href = response.url;
                return { success: true, redirect: true };
            }
            
            const data = await response.json();
            
            if (response.ok) {
                if (data.processed === 0) {
                    // Redirect to no emails found page
                    window.location.href = '/no-emails-found';
                    return { success: true, data: data, redirect: true };
                }
                return { success: true, data: data };
            } else {
                return { success: false, error: data.error || 'An error occurred while processing emails' };
            }
        } catch (error) {
            return { success: false, error: 'Network error: ' + error.message };
        }
    },

    displayResults: function(data) {
        const resultsDiv = document.getElementById('resultsContent');
        
        let html = `
            <div class="row mb-3">
                <div class="col-md-6">
                    <div class="card bg-light">
                        <div class="card-body">
                            <h6 class="card-title"><i class="bi bi-search"></i> Query Used</h6>
                            <code>${data.query}</code>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card bg-light">
                        <div class="card-body">
                            <h6 class="card-title"><i class="bi bi-check-circle"></i> Tasks Created</h6>
                            <span class="badge bg-success fs-6">${data.processed}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        if (data.created && data.created.length > 0) {
            html += '<h6><i class="bi bi-list-ul"></i> Created Tasks</h6>';
            html += '<div class="table-responsive">';
            html += '<table class="table table-striped">';
            html += '<thead><tr><th>Subject</th><th>Provider</th><th>Status</th><th>Created</th></tr></thead>';
            html += '<tbody>';
            
            data.created.forEach(task => {
                const subject = task.task.content || task.task.subject || 'No subject';
                const createdDate = task.task.created_at ? utils.formatDate(task.task.created_at) : 'Just now';
                html += `
                    <tr>
                        <td>${subject}</td>
                        <td><span class="badge bg-primary">${task.provider}</span></td>
                        <td><span class="badge bg-success">Created</span></td>
                        <td><small class="text-muted">${createdDate}</small></td>
                    </tr>
                `;
            });
            
            html += '</tbody></table></div>';
        } else {
            html += '<div class="alert alert-info"><i class="bi bi-info-circle"></i> No new emails found to process.</div>';
        }
        
        resultsDiv.innerHTML = html;
        document.getElementById('results').style.display = 'block';
    },

    displayError: function(message) {
        document.getElementById('errorContent').textContent = message;
        document.getElementById('error').style.display = 'block';
    },

    showLoading: function() {
        document.getElementById('loadingIndicator').style.display = 'block';
        document.getElementById('results').style.display = 'none';
        document.getElementById('error').style.display = 'none';
    },

    hideLoading: function() {
        document.getElementById('loadingIndicator').style.display = 'none';
    }
};

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    // Load saved settings
    settingsManager.load();
    
    // Set up form handlers
    const fetchForm = document.getElementById('fetchForm');
    if (fetchForm) {
        fetchForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = utils.getFormData('fetchForm');
            
            // Show loading state
            emailProcessor.showLoading();
            document.getElementById('fetchBtn').disabled = true;
            
            // Process emails
            const result = await emailProcessor.fetch(formData);
            
            if (result.success) {
                if (result.redirect) {
                    // Already redirected, do nothing
                    return;
                }
                emailProcessor.displayResults(result.data);
            } else {
                emailProcessor.displayError(result.error);
            }
            
            // Hide loading state
            emailProcessor.hideLoading();
            document.getElementById('fetchBtn').disabled = false;
        });
    }
    
    // Set up settings modal handlers
    const settingsModal = document.getElementById('settingsModal');
    if (settingsModal) {
        const saveBtn = settingsModal.querySelector('button[onclick="saveSettings()"]');
        if (saveBtn) {
            saveBtn.onclick = settingsManager.save;
        }
    }
    
    // Auto-save form data as user types (debounced)
    const formInputs = document.querySelectorAll('#fetchForm input, #fetchForm select');
    formInputs.forEach(input => {
        const debouncedSave = utils.debounce(() => {
            const formData = utils.getFormData('fetchForm');
            utils.saveSettings(formData);
        }, 1000);
        
        input.addEventListener('input', debouncedSave);
        input.addEventListener('change', debouncedSave);
    });
});

// Global functions for backward compatibility
function showSettings() {
    settingsManager.show();
}

function saveSettings() {
    settingsManager.save();
}

function loadSettings() {
    settingsManager.load();
    utils.showAlert('Settings loaded successfully!', 'success');
}

function showAlert(message, type = 'info') {
    utils.showAlert(message, type);
}
