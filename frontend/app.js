//GLOBAL CONFIGURATION
const API_URL = window.location.hostname === 'localhost' ? 'http://localhost:5000/api' : '/api';
let currentUser = null;

// UTILITY FUNCTIONS

// Check authentication status
function checkAuth() {
    const token = localStorage.getItem('token');
    const username = localStorage.getItem('username');
    
    if (token && username) {
        currentUser = { token, username };
        return true;
    }
    return false;
}

// Update navigation based on auth status
function updateNavigation() {
    const loginBtn = document.getElementById('loginBtn');
    const registerBtn = document.getElementById('registerBtn');
    const accountBtn = document.getElementById('accountBtn');
    const logoutBtn = document.getElementById('logoutBtn');
    
    if (checkAuth()) {
        if (loginBtn) loginBtn.classList.add('hidden');
        if (registerBtn) registerBtn.classList.add('hidden');
        if (accountBtn) accountBtn.classList.remove('hidden');
        if (logoutBtn) logoutBtn.classList.remove('hidden');
    }
}

// Logout function
function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    window.location.href = 'index.html';
}

// Show error message
function showError(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = message;
        element.classList.remove('hidden');
    }
}

// Hide error message
function hideError(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.classList.add('hidden');
    }
}

// INDEX.HTML FUNCTIONS

// Load recipes from API
async function loadRecipes(searchQuery = '') {
    const grid = document.getElementById('recipeGrid');
    const loading = document.getElementById('loading');
    
    if (!grid || !loading) return;
    
    loading.classList.remove('hidden');
    grid.innerHTML = '';

    try {
        const url = searchQuery 
            ? `${API_URL}/recipes/search?q=${encodeURIComponent(searchQuery)}`
            : `${API_URL}/recipes`;
        
        const response = await fetch(url);
        const recipes = await response.json();

        recipes.forEach(recipe => {
            const card = createRecipeCard(recipe);
            grid.appendChild(card);
        });

        if (recipes.length === 0) {
            grid.innerHTML = '<div class="col-span-full text-center py-12 text-gray-500">No recipes found. Try a different search!</div>';
        }
    } catch (error) {
        console.error('Error loading recipes:', error);
        grid.innerHTML = '<div class="col-span-full text-center py-12 text-red-500">Error loading recipes. Please try again.</div>';
    } finally {
        loading.classList.add('hidden');
    }
}

// Create recipe card element
function createRecipeCard(recipe) {
    const card = document.createElement('div');
    card.className = 'recipe-card bg-white rounded-xl shadow-md overflow-hidden cursor-pointer';
    card.innerHTML = `
        <div class="h-48 bg-gradient-to-br from-green-100 to-emerald-100 flex items-center justify-center text-6xl">
            ${recipe.emoji}
        </div>
        <div class="p-6">
            <h3 class="text-xl font-bold text-gray-800 mb-2">${recipe.name}</h3>
            <div class="flex justify-between text-sm text-gray-600 mb-3">
                <span>⏱️ ${recipe.time}</span>
                <span>📊 ${recipe.difficulty}</span>
            </div>
            <div class="flex justify-between items-center">
                <span class="text-2xl font-bold text-emerald-600">$${recipe.total_cost.toFixed(2)}</span>
                <button class="px-4 py-2 bg-emerald-500 text-white rounded-lg hover:bg-emerald-600 transition">
                    View Recipe
                </button>
            </div>
        </div>
    `;
    
    card.addEventListener('click', () => showRecipeModal(recipe));
    return card;
}

// Show recipe modal with details
async function showRecipeModal(recipe) {
    const modal = document.getElementById('recipeModal');
    const content = document.getElementById('modalContent');
    
    if (!modal || !content) return;
    
    try {
        const response = await fetch(`${API_URL}/recipes/${recipe.id}`);
        const fullRecipe = await response.json();
        
        const ingredientsList = fullRecipe.ingredients.map(ing => 
            `<li class="flex justify-between py-2 border-b border-gray-100">
                <span>${ing.name} - ${ing.amount}</span>
                <span class="font-semibold text-emerald-600">$${ing.cost.toFixed(2)}</span>
            </li>`
        ).join('');

        const instructionsList = fullRecipe.instructions.map((inst, idx) => 
            `<li class="mb-3"><span class="font-semibold text-emerald-600">${idx + 1}.</span> ${inst}</li>`
        ).join('');

        content.innerHTML = `
            <div class="text-center mb-6">
                <div class="text-6xl mb-4">${fullRecipe.emoji}</div>
                <h2 class="text-3xl font-bold text-gray-800">${fullRecipe.name}</h2>
                <div class="flex justify-center gap-6 mt-4 text-gray-600">
                    <span>⏱️ ${fullRecipe.time}</span>
                    <span>📊 ${fullRecipe.difficulty}</span>
                    <span>🍴 ${fullRecipe.servings} servings</span>
                </div>
            </div>

            <div class="mb-6">
                <h3 class="text-xl font-bold text-gray-800 mb-3">Ingredients</h3>
                <ul class="bg-green-50 rounded-lg p-4">${ingredientsList}</ul>
                <div class="text-right mt-2">
                    <span class="text-2xl font-bold text-emerald-600">Total: $${fullRecipe.total_cost.toFixed(2)}</span>
                </div>
            </div>

            <div class="mb-6">
                <h3 class="text-xl font-bold text-gray-800 mb-3">Instructions</h3>
                <ol class="space-y-2">${instructionsList}</ol>
            </div>

            ${currentUser ? `
                <div class="flex gap-4">
                    <button onclick="saveRecipe(${fullRecipe.id})" class="flex-1 px-6 py-3 bg-emerald-500 text-white rounded-lg hover:bg-emerald-600 transition">
                        💾 Save Recipe
                    </button>
                    <button onclick="likeRecipe(${fullRecipe.id})" class="flex-1 px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition">
                        ❤️ Like Recipe
                    </button>
                </div>
            ` : `
                <div class="text-center p-4 bg-yellow-50 rounded-lg">
                    <p class="text-gray-600">Please <a href="login.html" class="text-emerald-600 font-semibold">log in</a> to save and like recipes!</p>
                </div>
            `}
        `;
        
        modal.classList.remove('hidden');
    } catch (error) {
        console.error('Error loading recipe details:', error);
    }
}

// Close recipe modal
function closeRecipeModal() {
    const modal = document.getElementById('recipeModal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

// Save recipe to user account
async function saveRecipe(recipeId) {
    try {
        const response = await fetch(`${API_URL}/user/saved`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentUser.token}`
            },
            body: JSON.stringify({ recipe_id: recipeId })
        });
        
        if (response.ok) {
            alert('Recipe saved successfully!');
        }
    } catch (error) {
        console.error('Error saving recipe:', error);
        alert('Failed to save recipe. Please try again.');
    }
}

// Like recipe
async function likeRecipe(recipeId) {
    try {
        const response = await fetch(`${API_URL}/user/liked`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentUser.token}`
            },
            body: JSON.stringify({ recipe_id: recipeId })
        });
        
        if (response.ok) {
            alert('Recipe liked successfully!');
        }
    } catch (error) {
        console.error('Error liking recipe:', error);
        alert('Failed to like recipe. Please try again.');
    }
}

// Load random recipe
async function loadRandomRecipe() {
    try {
        const response = await fetch(`${API_URL}/recipes/random`);
        const recipe = await response.json();
        showRecipeModal(recipe);
    } catch (error) {
        console.error('Error loading random recipe:', error);
        alert('Failed to load random recipe. Please try again.');
    }
}

// Initialize index page
function initIndexPage() {
    checkAuth();
    updateNavigation();
    
    // Set up logout button
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }
    
    // Set up close modal button
    const closeModal = document.getElementById('closeModal');
    if (closeModal) {
        closeModal.addEventListener('click', closeRecipeModal);
    }
    
    // Set up search functionality
    const searchBtn = document.getElementById('searchBtn');
    const searchInput = document.getElementById('searchInput');
    
    if (searchBtn) {
        searchBtn.addEventListener('click', () => {
            const query = searchInput.value;
            loadRecipes(query);
        });
    }
    
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const query = searchInput.value;
                loadRecipes(query);
            }
        });
    }
    
    // Set up random recipe button
    const randomBtn = document.getElementById('randomBtn');
    if (randomBtn) {
        randomBtn.addEventListener('click', loadRandomRecipe);
    }
    
    // Set up generate recipe button
    const generateBtn = document.getElementById('generateBtn');
    const generateInput = document.getElementById('generateInput');
    
    if (generateBtn) {
        generateBtn.addEventListener('click', generateRecipe);
    }
    
    if (generateInput) {
        generateInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                generateRecipe();
            }
        });
    }
    
    // Load initial recipes
    loadRecipes();
}

// LOGIN.HTML FUNCTIONS

async function handleLogin(event) {
    event.preventDefault();
    
    const emailOrUsername = document.getElementById('emailOrUsername').value;
    const password = document.getElementById('password').value;
    const errorMsg = document.getElementById('errorMsg');
    const loginBtn = document.getElementById('loginBtn');

    hideError('errorMsg');
    loginBtn.disabled = true;
    loginBtn.textContent = 'Logging in...';

    try {
        const response = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email_or_username: emailOrUsername,
                password: password
            })
        });

        const data = await response.json();

        if (response.ok) {
            localStorage.setItem('token', data.token);
            localStorage.setItem('username', data.username);
            window.location.href = 'index.html';
        } else {
            showError('errorMsg', data.message || 'Login failed. Please check your credentials.');
        }
    } catch (error) {
        console.error('Login error:', error);
        showError('errorMsg', 'An error occurred. Please try again later.');
    } finally {
        loginBtn.disabled = false;
        loginBtn.textContent = 'Log In';
    }
}

function initLoginPage() {
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
}

// REGISTER.HTML FUNCTIONS

async function handleRegister(event) {
    event.preventDefault();
    
    const email = document.getElementById('email').value;
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    const errorMsg = document.getElementById('errorMsg');
    const successMsg = document.getElementById('successMsg');
    const registerBtn = document.getElementById('registerBtn');

    hideError('errorMsg');
    hideError('successMsg');

    // Validation
    if (password !== confirmPassword) {
        showError('errorMsg', 'Passwords do not match!');
        return;
    }

    if (password.length < 8) {
        showError('errorMsg', 'Password must be at least 8 characters long!');
        return;
    }

    if (username.length < 3 || username.length > 20) {
        showError('errorMsg', 'Username must be between 3 and 20 characters!');
        return;
    }

    if (!/^[a-zA-Z0-9]+$/.test(username)) {
        showError('errorMsg', 'Username can only contain letters and numbers!');
        return;
    }

    registerBtn.disabled = true;
    registerBtn.textContent = 'Creating account...';

    try {
        const response = await fetch(`${API_URL}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email,
                username: username,
                password: password
            })
        });

        const data = await response.json();

        if (response.ok) {
            const successEl = document.getElementById('successMsg');
            if (successEl) {
                successEl.textContent = 'Account created successfully! Redirecting to login...';
                successEl.classList.remove('hidden');
            }
            
            setTimeout(() => {
                window.location.href = 'login.html';
            }, 2000);
        } else {
            showError('errorMsg', data.message || 'Registration failed. Please try again.');
        }
    } catch (error) {
        console.error('Registration error:', error);
        showError('errorMsg', 'An error occurred. Please try again later.');
    } finally {
        registerBtn.disabled = false;
        registerBtn.textContent = 'Create Account';
    }
}

function initRegisterPage() {
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }
}

// FORGOT-PASSWORD.HTML FUNCTIONS

async function handleForgotPassword(event) {
    event.preventDefault();
    
    const email = document.getElementById('email').value;
    const errorMsg = document.getElementById('errorMsg');
    const successMsg = document.getElementById('successMsg');
    const resetBtn = document.getElementById('resetBtn');

    hideError('errorMsg');
    hideError('successMsg');

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showError('errorMsg', 'Please enter a valid email address!');
        return;
    }

    resetBtn.disabled = true;
    resetBtn.textContent = 'Sending...';

    try {
        const response = await fetch(`${API_URL}/auth/forgot-password`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email: email })
        });

        const data = await response.json();

        if (response.ok) {
            const successEl = document.getElementById('successMsg');
            if (successEl) {
                successEl.innerHTML = `
                    <div class="flex items-start">
                        <div class="text-xl mr-2">✅</div>
                        <div>
                            <p class="font-semibold mb-1">Email Sent Successfully!</p>
                            <p class="text-sm">Check your inbox for password reset instructions. The link will expire in 1 hour.</p>
                        </div>
                    </div>
                `;
                successEl.classList.remove('hidden');
            }
            document.getElementById('resetForm').reset();
            
            // Redirect to login after 5 seconds
            setTimeout(() => {
                window.location.href = 'login.html';
            }, 5000);
        } else {
            showError('errorMsg', data.message || 'Unable to send reset email. Please try again.');
        }
    } catch (error) {
        console.error('Password reset error:', error);
        showError('errorMsg', 'An error occurred. Please try again later.');
    } finally {
        resetBtn.disabled = false;
        resetBtn.textContent = 'Send Reset Link';
    }
}

function initForgotPasswordPage() {
    const resetForm = document.getElementById('resetForm');
    if (resetForm) {
        resetForm.addEventListener('submit', handleForgotPassword);
    }
}

// ACCOUNT.HTML FUNCTIONS

function initAccountPage() {
    // Check if user is logged in
    if (!checkAuth()) {
        window.location.href = 'login.html';
        return;
    }
    
    // Display username
    const usernameDisplay = document.getElementById('usernameDisplay');
    if (usernameDisplay) {
        usernameDisplay.textContent = currentUser.username;
    }
    
    // Set up logout button
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }
    
    // Set up tab switching
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.dataset.tab;
            
            tabButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            tabContents.forEach(content => {
                if (content.id === `${tabName}Tab`) {
                    content.classList.remove('hidden');
                } else {
                    content.classList.add('hidden');
                }
            });
        });
    });
    
    // Load user recipes
    loadSavedRecipes();
    loadLikedRecipes();
}

async function loadSavedRecipes() {
    const container = document.getElementById('savedRecipes');
    const empty = document.getElementById('savedEmpty');
    const loading = document.getElementById('loading');
    
    if (!container) return;
    
    loading.classList.remove('hidden');
    
    try {
        const response = await fetch(`${API_URL}/user/saved`, {
            headers: {
                'Authorization': `Bearer ${currentUser.token}`
            }
        });
        
        const recipes = await response.json();
        document.getElementById('savedCount').textContent = recipes.length;
        
        if (recipes.length === 0) {
            container.classList.add('hidden');
            empty.classList.remove('hidden');
        } else {
            container.classList.remove('hidden');
            empty.classList.add('hidden');
            container.innerHTML = '';
            
            recipes.forEach(recipe => {
                const card = createAccountRecipeCard(recipe, 'saved');
                container.appendChild(card);
            });
        }
    } catch (error) {
        console.error('Error loading saved recipes:', error);
    } finally {
        loading.classList.add('hidden');
    }
}

async function loadLikedRecipes() {
    const container = document.getElementById('likedRecipes');
    const empty = document.getElementById('likedEmpty');
    
    if (!container) return;
    
    try {
        const response = await fetch(`${API_URL}/user/liked`, {
            headers: {
                'Authorization': `Bearer ${currentUser.token}`
            }
        });
        
        const recipes = await response.json();
        document.getElementById('likedCount').textContent = recipes.length;
        
        if (recipes.length === 0) {
            container.classList.add('hidden');
            empty.classList.remove('hidden');
        } else {
            container.classList.remove('hidden');
            empty.classList.add('hidden');
            container.innerHTML = '';
            
            recipes.forEach(recipe => {
                const card = createAccountRecipeCard(recipe, 'liked');
                container.appendChild(card);
            });
        }
    } catch (error) {
        console.error('Error loading liked recipes:', error);
    }
}

function createAccountRecipeCard(recipe, type) {
    const card = document.createElement('div');
    card.className = 'recipe-card bg-white rounded-xl shadow-md overflow-hidden relative';
    card.innerHTML = `
        <div class="h-40 bg-gradient-to-br from-green-100 to-emerald-100 flex items-center justify-center text-5xl">
            ${recipe.emoji}
        </div>
        <div class="p-4">
            <h3 class="text-lg font-bold text-gray-800 mb-2">${recipe.name}</h3>
            <div class="flex justify-between text-sm text-gray-600 mb-2">
                <span>⏱️ ${recipe.time}</span>
                <span class="font-bold text-emerald-600">$${recipe.total_cost.toFixed(2)}</span>
            </div>
            <div class="flex gap-2">
                <a href="index.html" class="flex-1 px-3 py-2 bg-emerald-500 text-white text-sm rounded-lg hover:bg-emerald-600 transition text-center">
                    View Recipe
                </a>
                <button onclick="removeRecipe(${recipe.id}, '${type}')" 
                        class="px-3 py-2 bg-red-500 text-white text-sm rounded-lg hover:bg-red-600 transition">
                    Remove
                </button>
            </div>
        </div>
    `;
    return card;
}

async function removeRecipe(recipeId, type) {
    if (!confirm('Are you sure you want to remove this recipe?')) return;
    
    try {
        const response = await fetch(`${API_URL}/user/${type}/${recipeId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${currentUser.token}`
            }
        });
        
        if (response.ok) {
            if (type === 'saved') {
                loadSavedRecipes();
            } else {
                loadLikedRecipes();
            }
        }
    } catch (error) {
        console.error('Error removing recipe:', error);
        alert('Failed to remove recipe. Please try again.');
    }
}

// PAGE INITIALIZATION

// Detect which page the user is on and initialize accordingly
document.addEventListener('DOMContentLoaded', () => {
    const path = window.location.pathname;
    const page = path.substring(path.lastIndexOf('/') + 1) || 'index.html';
    
    switch(page) {
        case 'index.html':
        case '':
            initIndexPage();
            break;
        case 'login.html':
            initLoginPage();
            break;
        case 'register.html':
            initRegisterPage();
            break;
        case 'forgot-password.html':
            initForgotPasswordPage();
            break;
        case 'account.html':
            initAccountPage();
            break;
    }
});