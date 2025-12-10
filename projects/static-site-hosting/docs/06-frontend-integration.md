# Module 6: Frontend Integration

## Introduction

In this module, we'll integrate our FastAPI backend with a frontend using Jinja2 templates, HTML, CSS, and JavaScript. This will create a complete web application where users can register, login, and perform calculations using a user-friendly interface.

## Objectives

- Set up Jinja2 templates with FastAPI
- Create a responsive layout with CSS
- Implement client-side JavaScript for API interactions
- Create HTML templates for different pages
- Implement form validation on the client side

## Setting Up Jinja2 Templates

First, let's configure FastAPI to use Jinja2 templates in `app/main.py`:

```python
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Mount the static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up Jinja2 templates directory
templates = Jinja2Templates(directory="templates")
```

This allows us to:
1. Serve static files (CSS, JavaScript, images) from the `static` directory
2. Render Jinja2 templates from the `templates` directory

## Creating a Base Layout Template

Let's create a base layout template that all other templates will extend:

```html
<!-- templates/layout.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Calculator App{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', path='/css/style.css') }}">
    <script src="{{ url_for('static', path='/js/script.js') }}" defer></script>
    {% block head %}{% endblock %}
</head>
<body>
    <header>
        <nav>
            <div class="logo">Calculator App</div>
            <div class="nav-links">
                <a href="/">Home</a>
                <span id="auth-links">
                    <a href="/login">Login</a>
                    <a href="/register">Register</a>
                </span>
                <span id="user-links" style="display: none;">
                    <a href="/dashboard">Dashboard</a>
                    <a href="#" id="logout-link">Logout</a>
                </span>
            </div>
        </nav>
    </header>
    
    <main>
        {% block content %}{% endblock %}
    </main>
    
    <footer>
        <p>&copy; 2023 Calculator App - A FastAPI Project</p>
    </footer>
    
    <script>
        // Check if user is logged in
        document.addEventListener('DOMContentLoaded', function() {
            const token = localStorage.getItem('access_token');
            const authLinks = document.getElementById('auth-links');
            const userLinks = document.getElementById('user-links');
            
            if (token) {
                authLinks.style.display = 'none';
                userLinks.style.display = 'inline';
            } else {
                authLinks.style.display = 'inline';
                userLinks.style.display = 'none';
            }
            
            // Logout functionality
            document.getElementById('logout-link').addEventListener('click', function(e) {
                e.preventDefault();
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                localStorage.removeItem('user_info');
                window.location.href = '/';
            });
        });
    </script>
</body>
</html>
```

## Creating Page Templates

Now, let's create templates for each page in our application:

### Home Page

```html
<!-- templates/index.html -->
{% extends "layout.html" %}

{% block title %}Home - Calculator App{% endblock %}

{% block content %}
<section class="hero">
    <div class="hero-content">
        <h1>Welcome to Calculator App</h1>
        <p>A simple yet powerful calculator application built with FastAPI.</p>
        <div class="cta-buttons">
            <a href="/register" class="btn primary">Register</a>
            <a href="/login" class="btn secondary">Login</a>
        </div>
    </div>
</section>

<section class="features">
    <h2>Features</h2>
    <div class="feature-grid">
        <div class="feature-card">
            <h3>Basic Operations</h3>
            <p>Perform addition, subtraction, multiplication, and division.</p>
        </div>
        <div class="feature-card">
            <h3>Save Calculations</h3>
            <p>Save your calculations for future reference.</p>
        </div>
        <div class="feature-card">
            <h3>Secure Authentication</h3>
            <p>Secure user authentication using JWT tokens.</p>
        </div>
        <div class="feature-card">
            <h3>API Access</h3>
            <p>Access calculations via RESTful API endpoints.</p>
        </div>
    </div>
</section>
{% endblock %}
```

### Login Page

```html
<!-- templates/login.html -->
{% extends "layout.html" %}

{% block title %}Login - Calculator App{% endblock %}

{% block content %}
<section class="auth-form">
    <h1>Login</h1>
    
    <div id="error-message" class="error" style="display: none;"></div>
    
    <form id="login-form">
        <div class="form-group">
            <label for="username">Username or Email</label>
            <input type="text" id="username" name="username" required>
        </div>
        
        <div class="form-group">
            <label for="password">Password</label>
            <input type="password" id="password" name="password" required>
        </div>
        
        <button type="submit" class="btn primary">Login</button>
    </form>
    
    <p class="auth-link">
        Don't have an account? <a href="/register">Register here</a>
    </p>
</section>

<script>
    document.getElementById('login-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const errorMessage = document.getElementById('error-message');
        
        try {
            const response = await fetch('/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });
            
            if (response.ok) {
                const data = await response.json();
                
                // Store tokens and user info
                localStorage.setItem('access_token', data.access_token);
                localStorage.setItem('refresh_token', data.refresh_token);
                localStorage.setItem('user_info', JSON.stringify({
                    id: data.user_id,
                    username: data.username,
                    email: data.email,
                    first_name: data.first_name,
                    last_name: data.last_name
                }));
                
                // Redirect to dashboard
                window.location.href = '/dashboard';
            } else {
                const error = await response.json();
                errorMessage.textContent = error.detail || 'Login failed. Please check your credentials.';
                errorMessage.style.display = 'block';
            }
        } catch (error) {
            errorMessage.textContent = 'An error occurred. Please try again.';
            errorMessage.style.display = 'block';
            console.error('Login error:', error);
        }
    });
</script>
{% endblock %}
```

### Registration Page

```html
<!-- templates/register.html -->
{% extends "layout.html" %}

{% block title %}Register - Calculator App{% endblock %}

{% block content %}
<section class="auth-form">
    <h1>Create Account</h1>
    
    <div id="error-message" class="error" style="display: none;"></div>
    
    <form id="register-form">
        <div class="form-group">
            <label for="first_name">First Name</label>
            <input type="text" id="first_name" name="first_name" required>
        </div>
        
        <div class="form-group">
            <label for="last_name">Last Name</label>
            <input type="text" id="last_name" name="last_name" required>
        </div>
        
        <div class="form-group">
            <label for="username">Username</label>
            <input type="text" id="username" name="username" required>
        </div>
        
        <div class="form-group">
            <label for="email">Email</label>
            <input type="email" id="email" name="email" required>
        </div>
        
        <div class="form-group">
            <label for="password">Password</label>
            <input type="password" id="password" name="password" required minlength="6">
            <small>Password must be at least 6 characters long.</small>
        </div>
        
        <div class="form-group">
            <label for="confirm_password">Confirm Password</label>
            <input type="password" id="confirm_password" name="confirm_password" required>
        </div>
        
        <button type="submit" class="btn primary">Register</button>
    </form>
    
    <p class="auth-link">
        Already have an account? <a href="/login">Login here</a>
    </p>
</section>

<script>
    document.getElementById('register-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const form = e.target;
        const errorMessage = document.getElementById('error-message');
        
        // Basic validation
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirm_password').value;
        
        if (password !== confirmPassword) {
            errorMessage.textContent = 'Passwords do not match.';
            errorMessage.style.display = 'block';
            return;
        }
        
        const userData = {
            first_name: document.getElementById('first_name').value,
            last_name: document.getElementById('last_name').value,
            username: document.getElementById('username').value,
            email: document.getElementById('email').value,
            password: password,
            confirm_password: confirmPassword
        };
        
        try {
            const response = await fetch('/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(userData)
            });
            
            if (response.ok) {
                // Registration successful, redirect to login
                window.location.href = '/login?registered=true';
            } else {
                const error = await response.json();
                errorMessage.textContent = error.detail || 'Registration failed. Please try again.';
                errorMessage.style.display = 'block';
            }
        } catch (error) {
            errorMessage.textContent = 'An error occurred. Please try again.';
            errorMessage.style.display = 'block';
            console.error('Registration error:', error);
        }
    });
</script>
{% endblock %}
```

### Dashboard Page

```html
<!-- templates/dashboard.html -->
{% extends "layout.html" %}

{% block title %}Dashboard - Calculator App{% endblock %}

{% block content %}
<section class="dashboard">
    <h1>Dashboard</h1>
    
    <div class="dashboard-grid">
        <div class="calculator-card">
            <h2>New Calculation</h2>
            
            <form id="calculation-form">
                <div class="form-group">
                    <label for="calculation-type">Operation</label>
                    <select id="calculation-type" name="type" required>
                        <option value="addition">Addition</option>
                        <option value="subtraction">Subtraction</option>
                        <option value="multiplication">Multiplication</option>
                        <option value="division">Division</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="calculation-inputs">Numbers (comma-separated)</label>
                    <input type="text" id="calculation-inputs" name="inputs" 
                           placeholder="e.g. 5, 10, 15" required>
                    <small>Enter at least two numbers, separated by commas.</small>
                </div>
                
                <button type="submit" class="btn primary">Calculate</button>
            </form>
            
            <div id="calculation-result" class="result-box" style="display: none;">
                <h3>Result</h3>
                <p id="result-value"></p>
            </div>
        </div>
        
        <div class="calculations-list">
            <h2>Your Calculations</h2>
            
            <div id="calculations-container">
                <p>Loading your calculations...</p>
            </div>
        </div>
    </div>
</section>

<script>
    // Check if user is logged in
    document.addEventListener('DOMContentLoaded', async function() {
        const token = localStorage.getItem('access_token');
        if (!token) {
            window.location.href = '/login';
            return;
        }
        
        // Load user's calculations
        loadCalculations();
        
        // Handle new calculation form
        document.getElementById('calculation-form').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const type = document.getElementById('calculation-type').value;
            const inputsString = document.getElementById('calculation-inputs').value;
            const inputs = inputsString.split(',').map(num => parseFloat(num.trim()));
            
            try {
                const response = await fetch('/calculations', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        type: type,
                        inputs: inputs
                    })
                });
                
                if (response.ok) {
                    const data = await response.json();
                    
                    // Display result
                    document.getElementById('result-value').textContent = data.result;
                    document.getElementById('calculation-result').style.display = 'block';
                    
                    // Reload calculations list
                    loadCalculations();
                } else {
                    const error = await response.json();
                    alert(`Error: ${error.detail || 'Something went wrong'}`);
                }
            } catch (error) {
                console.error('Calculation error:', error);
                alert('An error occurred. Please try again.');
            }
        });
    });
    
    async function loadCalculations() {
        const token = localStorage.getItem('access_token');
        const container = document.getElementById('calculations-container');
        
        try {
            const response = await fetch('/calculations', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.ok) {
                const calculations = await response.json();
                
                if (calculations.length === 0) {
                    container.innerHTML = '<p>No calculations yet. Create your first one!</p>';
                    return;
                }
                
                let html = '<div class="calculations-grid">';
                
                calculations.forEach(calc => {
                    const date = new Date(calc.created_at).toLocaleDateString();
                    const time = new Date(calc.created_at).toLocaleTimeString();
                    
                    html += `
                        <div class="calculation-item">
                            <div class="calc-type ${calc.type}">${calc.type}</div>
                            <div class="calc-inputs">${calc.inputs.join(' , ')}</div>
                            <div class="calc-result">${calc.result}</div>
                            <div class="calc-date">${date} ${time}</div>
                            <div class="calc-actions">
                                <a href="/dashboard/view/${calc.id}" class="btn small">View</a>
                                <a href="/dashboard/edit/${calc.id}" class="btn small secondary">Edit</a>
                                <button class="btn small danger" onclick="deleteCalculation('${calc.id}')">Delete</button>
                            </div>
                        </div>
                    `;
                });
                
                html += '</div>';
                container.innerHTML = html;
            } else {
                container.innerHTML = '<p>Error loading calculations. Please try again.</p>';
            }
        } catch (error) {
            console.error('Error loading calculations:', error);
            container.innerHTML = '<p>Error loading calculations. Please try again.</p>';
        }
    }
    
    async function deleteCalculation(id) {
        if (!confirm('Are you sure you want to delete this calculation?')) {
            return;
        }
        
        const token = localStorage.getItem('access_token');
        
        try {
            const response = await fetch(`/calculations/${id}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.ok) {
                loadCalculations();
            } else {
                alert('Error deleting calculation. Please try again.');
            }
        } catch (error) {
            console.error('Delete error:', error);
            alert('An error occurred. Please try again.');
        }
    }
</script>
{% endblock %}
```

## Adding CSS Styles

Let's create a basic CSS file for styling our application:

```css
/* static/css/style.css */
:root {
    --primary-color: #3498db;
    --secondary-color: #2ecc71;
    --danger-color: #e74c3c;
    --background-color: #f5f5f5;
    --text-color: #333;
    --border-color: #ddd;
    --shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: var(--text-color);
    background-color: var(--background-color);
    display: flex;
    flex-direction: column;
    min-height: 100vh;
}

header {
    background-color: white;
    box-shadow: var(--shadow);
    padding: 1rem 2rem;
}

nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    max-width: 1200px;
    margin: 0 auto;
}

.logo {
    font-size: 1.5rem;
    font-weight: bold;
    color: var(--primary-color);
}

.nav-links a {
    margin-left: 1.5rem;
    text-decoration: none;
    color: var(--text-color);
    transition: color 0.3s;
}

.nav-links a:hover {
    color: var(--primary-color);
}

main {
    flex: 1;
    padding: 2rem;
    max-width: 1200px;
    margin: 0 auto;
    width: 100%;
}

footer {
    background-color: white;
    padding: 1rem;
    text-align: center;
    box-shadow: 0 -2px 5px rgba(0, 0, 0, 0.05);
}

/* Form styles */
.auth-form {
    max-width: 500px;
    margin: 0 auto;
    background-color: white;
    padding: 2rem;
    border-radius: 5px;
    box-shadow: var(--shadow);
}

.form-group {
    margin-bottom: 1.5rem;
}

label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
}

input, select {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    font-size: 1rem;
}

small {
    display: block;
    margin-top: 0.25rem;
    color: #666;
}

.btn {
    display: inline-block;
    padding: 0.75rem 1.5rem;
    background-color: var(--primary-color);
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    text-decoration: none;
    font-size: 1rem;
    transition: background-color 0.3s;
}

.btn.secondary {
    background-color: var(--secondary-color);
}

.btn.danger {
    background-color: var(--danger-color);
}

.btn.small {
    padding: 0.25rem 0.5rem;
    font-size: 0.875rem;
}

.btn:hover {
    opacity: 0.9;
}

.error {
    background-color: #f8d7da;
    color: #721c24;
    padding: 0.75rem;
    margin-bottom: 1rem;
    border-radius: 4px;
    border: 1px solid #f5c6cb;
}

.auth-link {
    margin-top: 1.5rem;
    text-align: center;
}

/* Dashboard styles */
.dashboard-grid {
    display: grid;
    grid-template-columns: 1fr 2fr;
    gap: 2rem;
}

.calculator-card {
    background-color: white;
    padding: 1.5rem;
    border-radius: 5px;
    box-shadow: var(--shadow);
}

.result-box {
    margin-top: 1.5rem;
    padding: 1rem;
    background-color: #f8f9fa;
    border-radius: 5px;
    border-left: 4px solid var(--primary-color);
}

.calculations-list {
    background-color: white;
    padding: 1.5rem;
    border-radius: 5px;
    box-shadow: var(--shadow);
}

.calculations-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1rem;
    margin-top: 1rem;
}

.calculation-item {
    border: 1px solid var(--border-color);
    border-radius: 5px;
    padding: 1rem;
    background-color: #f8f9fa;
}

.calc-type {
    display: inline-block;
    padding: 0.25rem 0.5rem;
    border-radius: 3px;
    color: white;
    font-size: 0.875rem;
    margin-bottom: 0.5rem;
}

.calc-type.addition {
    background-color: var(--primary-color);
}

.calc-type.subtraction {
    background-color: var(--secondary-color);
}

.calc-type.multiplication {
    background-color: #9b59b6;
}

.calc-type.division {
    background-color: #f39c12;
}

.calc-result {
    font-size: 1.5rem;
    font-weight: bold;
    margin: 0.5rem 0;
}

.calc-date {
    font-size: 0.875rem;
    color: #666;
    margin-bottom: 0.5rem;
}

.calc-actions {
    margin-top: 1rem;
    display: flex;
    gap: 0.5rem;
}

/* Hero section */
.hero {
    background-color: white;
    padding: 4rem 2rem;
    text-align: center;
    border-radius: 5px;
    box-shadow: var(--shadow);
    margin-bottom: 2rem;
}

.hero-content h1 {
    font-size: 2.5rem;
    margin-bottom: 1rem;
    color: var(--primary-color);
}

.hero-content p {
    font-size: 1.25rem;
    max-width: 600px;
    margin: 0 auto 2rem;
    color: #666;
}

.cta-buttons {
    display: flex;
    gap: 1rem;
    justify-content: center;
}

/* Features section */
.features {
    padding: 2rem 0;
}

.features h2 {
    text-align: center;
    margin-bottom: 2rem;
}

.feature-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 2rem;
}

.feature-card {
    background-color: white;
    padding: 1.5rem;
    border-radius: 5px;
    box-shadow: var(--shadow);
    transition: transform 0.3s;
}

.feature-card:hover {
    transform: translateY(-5px);
}

.feature-card h3 {
    color: var(--primary-color);
    margin-bottom: 1rem;
}

/* Responsive styles */
@media (max-width: 768px) {
    .dashboard-grid {
        grid-template-columns: 1fr;
    }
    
    nav {
        flex-direction: column;
        gap: 1rem;
    }
    
    .nav-links {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 1rem;
    }
    
    .nav-links a {
        margin-left: 0;
    }
}
```

## Adding JavaScript Functionality

Let's create a JavaScript file for common functionality:

```javascript
// static/js/script.js

// Utility functions
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

function getAuthToken() {
    return localStorage.getItem('access_token');
}

function isLoggedIn() {
    return !!getAuthToken();
}

function redirectToLogin() {
    window.location.href = '/login';
}

// API request helper
async function apiRequest(url, method = 'GET', data = null) {
    const token = getAuthToken();
    
    if (!token && url !== '/auth/login' && url !== '/auth/register') {
        redirectToLogin();
        return null;
    }
    
    const headers = {
        'Content-Type': 'application/json'
    };
    
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    const options = {
        method: method,
        headers: headers
    };
    
    if (data && (method === 'POST' || method === 'PUT')) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(url, options);
        
        // Handle 401 (Unauthorized) by redirecting to login
        if (response.status === 401 && url !== '/auth/login') {
            localStorage.removeItem('access_token');
            localStorage.removeItem('user_info');
            redirectToLogin();
            return null;
        }
        
        // For DELETE operations (204 No Content)
        if (method === 'DELETE' && response.status === 204) {
            return true;
        }
        
        // Parse JSON response
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.detail || 'API request failed');
        }
        
        return result;
    } catch (error) {
        console.error('API request error:', error);
        throw error;
    }
}

// Check auth status when page loads
document.addEventListener('DOMContentLoaded', function() {
    updateAuthUI();
});

function updateAuthUI() {
    const authLinks = document.getElementById('auth-links');
    const userLinks = document.getElementById('user-links');
    
    if (isLoggedIn()) {
        if (authLinks) authLinks.style.display = 'none';
        if (userLinks) userLinks.style.display = 'inline';
        
        // Set up logout handler
        const logoutLink = document.getElementById('logout-link');
        if (logoutLink) {
            logoutLink.addEventListener('click', function(e) {
                e.preventDefault();
                logout();
            });
        }
    } else {
        if (authLinks) authLinks.style.display = 'inline';
        if (userLinks) userLinks.style.display = 'none';
    }
}

function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_info');
    window.location.href = '/';
}
```

## Connecting FastAPI Routes with Templates

Now, let's create the web routes in `app/main.py`:

```python
# Web (HTML) Routes
@app.get("/", response_class=HTMLResponse, tags=["web"])
def read_index(request: Request):
    """Landing page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse, tags=["web"])
def login_page(request: Request):
    """Login page."""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse, tags=["web"])
def register_page(request: Request):
    """Registration page."""
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse, tags=["web"])
def dashboard_page(request: Request):
    """Dashboard page, listing calculations & new calculation form."""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/dashboard/view/{calc_id}", response_class=HTMLResponse, tags=["web"])
def view_calculation_page(request: Request, calc_id: str):
    """
    Page for viewing a single calculation (Read).
    Renders 'view_calculation.html' and passes calc_id to the template.
    """
    return templates.TemplateResponse("view_calculation.html", {"request": request, "calc_id": calc_id})

@app.get("/dashboard/edit/{calc_id}", response_class=HTMLResponse, tags=["web"])
def edit_calculation_page(request: Request, calc_id: str):
    """
    Page for editing a calculation (Update).
    Renders 'edit_calculation.html' and passes calc_id to the template.
    """
    return templates.TemplateResponse("edit_calculation.html", {"request": request, "calc_id": calc_id})
```

## Client-Side vs. Server-Side Rendering

In our implementation, we're using a hybrid approach:

1. **Server-side rendering**: Using Jinja2 templates to render the initial HTML
2. **Client-side JavaScript**: Using JavaScript to fetch data from the API and update the DOM

This approach gives us the benefits of both worlds:
- Initial page load is fast with server-rendered HTML
- Dynamic updates happen without page refreshes using JavaScript
- SEO benefits from server-rendered content
- Better user experience with client-side interactivity

## Next Steps

In the next module, we'll implement testing for our application, including unit tests, integration tests, and end-to-end tests.

## Additional Resources

- [FastAPI Templates](https://fastapi.tiangolo.com/advanced/templates/)
- [Jinja2 Documentation](https://jinja.palletsprojects.com/)
- [Frontend Best Practices](https://developers.google.com/web/fundamentals)
- [Modern CSS Guide](https://moderncss.dev/)