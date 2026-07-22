// EA Tutorial Hub - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Search functionality
    const searchForm = document.querySelector('form[action*="/search"]');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            const query = searchForm.querySelector('input[name="q"]').value.trim();
            if (!query) {
                e.preventDefault();
                alert('Please enter search terms');
            }
        });
    }

    // File upload preview
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const fileName = file.name;
                const fileSize = (file.size / (1024 * 1024)).toFixed(2);
                console.log(`File selected: ${fileName} (${fileSize} MB)`);
            }
        });
    });

    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Logout confirmation
    const logoutLinks = document.querySelectorAll('a[href*="/logout"]');
    logoutLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to logout?')) {
                e.preventDefault();
            }
        });
    });

    // Active navigation highlight
    const currentLocation = location.pathname;
    const menuItems = document.querySelectorAll('.nav-link, .dropdown-item');
    menuItems.forEach(item => {
        if (item.getAttribute('href') === currentLocation) {
            item.classList.add('active');
        }
    });

    // Quiz timer countdown
    const timerElement = document.getElementById('timer');
    if (timerElement) {
        // Timer is handled in the quiz template
    }

    // Progress tracking
    const progressBar = document.getElementById('progressBar');
    if (progressBar) {
        document.querySelectorAll('input[type="radio"], input[type="text"]').forEach(input => {
            input.addEventListener('change', updateQuizProgress);
        });
    }
});

// Update quiz progress
function updateQuizProgress() {
    const form = document.getElementById('quizForm');
    if (!form) return;

    const questions = document.querySelectorAll('[data-question-id]');
    let answered = 0;

    questions.forEach(q => {
        const qId = q.getAttribute('data-question-id');
        const checked = document.querySelector(`input[name="q${qId}"]:checked`);
        if (checked) {
            answered++;
            // Highlight answered question in sidebar
            const qLink = document.querySelector(`[data-question-id="${qId}"].question-link`);
            if (qLink) {
                qLink.classList.add('answered');
            }
        }
    });

    const total = questions.length;
    const percentage = (answered / total) * 100;
    if (document.getElementById('progressBar')) {
        document.getElementById('progressBar').style.width = percentage + '%';
    }
    if (document.getElementById('answeredCount')) {
        document.getElementById('answeredCount').textContent = answered;
    }
}

// Utility function for AJAX requests
async function makeRequest(url, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        }
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(url, options);
        return await response.json();
    } catch (error) {
        console.error('Request failed:', error);
        alert('An error occurred. Please try again.');
        return null;
    }
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Show loading spinner
function showLoading(element) {
    element.innerHTML = '<div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div>';
}

// Show notification
function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.insertBefore(alertDiv, document.body.firstChild);

    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// Debounce function for search
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Mobile sidebar toggle — handled by inline JS in base.html (class-based .mobile-open / .active)

// Theme switching
function toggleTheme() {
    const body = document.body;
    const isLight = body.classList.toggle('light-mode');
    localStorage.setItem('ea_theme', isLight ? 'light' : 'dark');
    updateThemeButton(isLight);
}

function updateThemeButton(isLight) {
    const btn = document.getElementById('themeToggleBtn');
    if (!btn) return;
    const icon = btn.querySelector('i');
    const text = btn.querySelector('.sidebar-link-text');
    if (icon) icon.className = isLight ? 'fas fa-moon' : 'fas fa-sun';
    if (text) text.textContent = isLight ? 'Dark Mode' : 'Light Mode';
    // Sync mobile topbar theme button
    const mobileBtn = document.getElementById('mobileThemeBtn');
    if (mobileBtn) {
        const mIcon = mobileBtn.querySelector('i');
        if (mIcon) mIcon.className = isLight ? 'fas fa-moon' : 'fas fa-sun';
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const savedTheme = localStorage.getItem('ea_theme') || 'dark';
    if (savedTheme === 'light') {
        document.body.classList.add('light-mode');
    }
    updateThemeButton(savedTheme === 'light');

    // Sidebar toggle (desktop collapse)
    const sidebar = document.getElementById('appSidebar');
    const toggleBtn = document.getElementById('sidebarToggle');

    if (sidebar && toggleBtn) {
        var mcw = document.getElementById('mainContentWrapper');
        if (localStorage.getItem('ea_sidebar_collapsed') === 'true') {
            document.body.classList.add('sidebar-collapsed');
        }
        function setWillChange() {
            if (sidebar) sidebar.style.willChange = 'width';
            if (mcw) mcw.style.willChange = 'margin-left, width';
        }
        function clearWillChange() {
            if (sidebar) sidebar.style.willChange = 'auto';
            if (mcw) mcw.style.willChange = 'auto';
        }
        toggleBtn.addEventListener('click', function() {
            if (document.body.classList.contains('sidebar-collapsed')) {
                // Expanding: remove all collapse classes at once so open curve wins
                setWillChange();
                document.body.classList.remove('sb-closing', 'sidebar-collapsed');
                localStorage.setItem('ea_sidebar_collapsed', 'false');
                // Fallback cleanup
                setTimeout(clearWillChange, 220);
            } else {
                // Collapsing: add sb-closing first so close curve applies
                setWillChange();
                document.body.classList.add('sb-closing');
                requestAnimationFrame(function() {
                    document.body.classList.add('sidebar-collapsed');
                    localStorage.setItem('ea_sidebar_collapsed', 'true');
                    // Fallback cleanup
                    setTimeout(function() {
                        document.body.classList.remove('sb-closing');
                        clearWillChange();
                    }, 200);
                });
            }
        });
        // Clean up sb-closing and will-change after transition ends
        sidebar.addEventListener('transitionend', function(e) {
            if (e.propertyName === 'width' || e.propertyName === 'margin-left') {
                document.body.classList.remove('sb-closing');
                clearWillChange();
            }
        });
    }
});

