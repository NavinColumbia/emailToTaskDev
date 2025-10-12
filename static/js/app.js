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
        console.log('🚀 Starting email fetch with params:', params);
        const queryString = new URLSearchParams(params).toString();
        console.log('📝 Query string:', queryString);
        
        try {
            console.log('🌐 Making fetch request to:', `/api/fetch-emails?${queryString}`);
            const response = await fetch(`/api/fetch-emails?${queryString}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json, text/html'
                }
            });
            
            console.log('📡 Response received:', {
                status: response.status,
                statusText: response.statusText,
                ok: response.ok,
                redirected: response.redirected,
                url: response.url
            });
            
            // Check if response is a redirect (status 302)
            if (response.redirected || response.status === 302) {
                console.log('🔄 Redirect detected, letting browser handle navigation to:', response.url);
                // Let the browser handle the redirect naturally - no JavaScript navigation
                return { success: true, redirect: true };
            }
            
            console.log('📄 Parsing JSON response...');
            const data = await response.json();
            console.log('📊 Parsed response data:', data);
            
            if (response.ok) {
                console.log('✅ Response OK - data.processed:', data.processed);
                // This shouldn't happen with current backend since it redirects
                console.log('⚠️ Unexpected JSON response - backend should have redirected');
                return { success: false, error: 'Unexpected response format' };
            } else {
                console.log('❌ Response not OK - error:', data.error);
                return { success: false, error: data.error || 'An error occurred while processing emails' };
            }
        } catch (error) {
            console.log('💥 Fetch error:', error);
            return { success: false, error: 'Network error: ' + error.message };
        }
    },


    displayError: function(message) {
        const errorContent = document.getElementById('errorContent');
        const error = document.getElementById('error');
        
        if (errorContent) errorContent.textContent = message;
        if (error) {
            error.classList.remove('notion-hidden');
            error.style.display = 'block';
        }
    },

    showLoading: function() {
        const error = document.getElementById('error');
        const fetchBtn = document.getElementById('fetchBtn');
        
        if (error) {
            error.classList.add('notion-hidden');
            error.style.display = 'none';
        }
        if (fetchBtn) {
            fetchBtn.disabled = true;
        }
    },

    hideLoading: function() {
        const fetchBtn = document.getElementById('fetchBtn');
        if (fetchBtn) {
            fetchBtn.disabled = false;
        }
    }
};

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    // Load saved settings
    settingsManager.load();
    
    // Set up form handlers
    const fetchForm = document.getElementById('fetchForm');
    if (fetchForm) {
        fetchForm.addEventListener('submit', function(e) {
            console.log('📋 Form submitted');
            
            const formData = utils.getFormData('fetchForm');
            console.log('📝 Form data extracted:', formData);
            
            // Show loading state
            console.log('⏳ Showing loading state');
            emailProcessor.showLoading();
            
            // Let the form submit naturally - browser will handle redirect
            console.log('🔄 Form submitting naturally, browser will handle redirect');
            // Don't prevent default - let the browser submit the form and handle the redirect
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
