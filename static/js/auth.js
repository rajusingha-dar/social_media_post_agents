// static/js/auth.js

// Form validation
function setupFormValidation(formId) {
    const form = document.getElementById(formId);
    
    if (!form) return;
    
    // Add nice focus effects to inputs
    const inputs = form.querySelectorAll('input');
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('input-focus');
        });
        
        input.addEventListener('blur', function() {
            this.parentElement.classList.remove('input-focus');
        });
    });
    
    form.addEventListener('submit', function(event) {
        let isValid = true;
        
        // Clear previous errors
        const errorElements = form.querySelectorAll('.error-text');
        errorElements.forEach(el => el.remove());
        
        inputs.forEach(input => input.classList.remove('input-error'));
        
        // Validate username
        const usernameInput = form.querySelector('#username');
        if (usernameInput && usernameInput.value.trim().length < 3) {
            showError(usernameInput, 'Username must be at least 3 characters');
            isValid = false;
        }
        
        // Validate email
        const emailInput = form.querySelector('#email');
        if (emailInput && !isValidEmail(emailInput.value.trim())) {
            showError(emailInput, 'Please enter a valid email address');
            isValid = false;
        }
        
        // Validate password
        const passwordInput = form.querySelector('#password');
        if (passwordInput && passwordInput.value.length < 8) {
            showError(passwordInput, 'Password must be at least 8 characters');
            isValid = false;
        }
        
        if (!isValid) {
            event.preventDefault();
            // Scroll to first error
            const firstError = form.querySelector('.input-error');
            if (firstError) {
                firstError.focus();
            }
        } else {
            // Add loading state to button
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.innerHTML = '<span class="loading-spinner"></span> Processing...';
                submitButton.disabled = true;
            }
        }
    });
}

// Email validation helper
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Show error message
function showError(input, message) {
    input.classList.add('input-error');
    
    const errorElement = document.createElement('div');
    errorElement.className = 'error-text';
    errorElement.textContent = message;
    
    const parent = input.parentElement;
    parent.appendChild(errorElement);
    
    // Add shake animation
    input.classList.add('shake');
    setTimeout(() => {
        input.classList.remove('shake');
    }, 500);
}

// Token handling
function getToken() {
    return localStorage.getItem('access_token');
}

function setToken(token) {
    localStorage.setItem('access_token', token);
}

function removeToken() {
    localStorage.removeItem('access_token');
}

// API calls
async function loginAPI(username, password) {
    try {
        const response = await fetch('/api/token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                'username': username,
                'password': password,
            })
        });
        
        if (!response.ok) {
            throw new Error('Login failed');
        }
        
        const data = await response.json();
        return data.access_token;
    } catch (error) {
        console.error('Error during login:', error);
        throw error;
    }
}

async function registerAPI(username, email, password) {
    try {
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username,
                email,
                password
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Registration failed');
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error during registration:', error);
        throw error;
    }
}

// Dark mode toggle function
function toggleDarkMode() {
    const body = document.body;
    body.classList.toggle('light-mode');
    const isDarkMode = !body.classList.contains('light-mode');
    localStorage.setItem('darkMode', isDarkMode ? 'true' : 'false');
}

// Initialize any auth-related functionality
document.addEventListener('DOMContentLoaded', function() {
    // Check for saved dark mode preference
    const savedDarkMode = localStorage.getItem('darkMode');
    if (savedDarkMode === 'false') {
        document.body.classList.add('light-mode');
    }
    
    // Add animation classes after page load
    setTimeout(() => {
        document.querySelectorAll('.auth-container, .dashboard-card, .stat-card').forEach(el => {
            el.classList.add('fade-in');
        });
    }, 100);
    
    // Add CSS for animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
            20%, 40%, 60%, 80% { transform: translateX(5px); }
        }
        
        .fade-in {
            animation: fadeIn 0.5s ease-out forwards;
        }
        
        .shake {
            animation: shake 0.5s ease-in-out;
        }
        
        .loading-spinner {
            display: inline-block;
            width: 1rem;
            height: 1rem;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 0.8s linear infinite;
            margin-right: 0.5rem;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .input-focus {
            position: relative;
        }
        
        .input-focus::after {
            content: "";
            position: absolute;
            left: 0;
            bottom: -2px;
            width: 100%;
            height: 2px;
            background-color: var(--primary-color);
            animation: inputFocus 0.3s ease forwards;
        }
        
        @keyframes inputFocus {
            from { transform: scaleX(0); }
            to { transform: scaleX(1); }
        }
    `;
    document.head.appendChild(style);
});