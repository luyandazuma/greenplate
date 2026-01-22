const API_URL = (window.config && window.config.apiUrl) 
    || (window.location.hostname === 'localhost' ? 'http://localhost:5000/api' : 'https://b89r22hza7.execute-api.af-south-1.amazonaws.com/dev/api');

let currentUser = null;

console.log('Using API URL:', API_URL);

// ============= UTILITY FUNCTIONS =============

// Check authentication status
function checkAuth() {
    const token = localStorage.getItem('token');
    const username = localStorage.getItem('username');
    
    if (token && username) {
        currentUser = { token, username };
        return true;
    }
    currentUser = null;
    return false;
}

// Update navigation based on auth status
function updateNavigation() {
    const loginBtn = document.getElementById('loginBtn');
    const registerBtn = document.getElementById('registerBtn');
    const accountBtn = document.getElementById('accountBtn');
    const logoutBtn = document.getElementById('logoutBtn');
    const isLoggedIn = checkAuth();
    
    if (isLoggedIn) {
        if (loginBtn) loginBtn.classList.add('hidden');
        if (registerBtn) registerBtn.classList.add('hidden');
        if (accountBtn) accountBtn.classList.remove('hidden');
        if (logoutBtn) logoutBtn.classList.remove('hidden');
    } else {
        if (loginBtn) loginBtn.classList.remove('hidden');
        if (registerBtn) registerBtn.classList.remove('hidden');
        if (accountBtn) accountBtn.classList.add('hidden');
        if (logoutBtn) logoutBtn.classList.add('hidden');
    }
}

// Logout function
function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    currentUser = null;
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

// ============= INDEX.HTML FUNCTIONS =============

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
        if (!response.ok) throw new Error('Network response was not ok');
        
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
        grid.innerHTML = '<div class="col-span-full text-center py-12 text-red-500">Error loading recipes. Is the backend running?</div>';
    } finally {
        loading.classList.add('hidden');
    }
}

// Create recipe card element
function createRecipeCard(recipe) {
    const card = document.createElement('div');
    card.className = 'recipe-card bg-white rounded-xl shadow-md overflow-hidden cursor-pointer transform hover:scale-105 transition duration-200';
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
        const response = await fetch(`${API_URL}/recipes/${recipe.recipe_id}`);
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

        const isLoggedIn = checkAuth();

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

            ${isLoggedIn ? `
                <div class="flex gap-4">
                    <button onclick="saveRecipe(${fullRecipe.recipe_id})" class="flex-1 px-6 py-3 bg-emerald-500 text-white rounded-lg hover:bg-emerald-600 transition">
                        💾 Save Recipe
                    </button>
                    <button onclick="likeRecipe(${fullRecipe.recipe_id})" class="flex-1 px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition">
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
        content.innerHTML = '<p class="text-center text-red-500">Failed to load recipe details.</p>';
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
    if (!checkAuth()) return;

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
        } else {
            const data = await response.json();
            alert(data.message || 'Failed to save recipe');
        }
    } catch (error) {
        console.error('Error saving recipe:', error);
        alert('Failed to save recipe. Please try again.');
    }
}

// Like recipe
async function likeRecipe(recipeId) {
    if (!checkAuth()) return;

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
        } else {
            const data = await response.json();
            alert(data.message || 'Failed to like recipe');
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
        if (!response.ok) throw new Error('Failed to fetch');
        
        const recipe = await response.json();
        showRecipeModal(recipe);
    } catch (error) {
        console.error('Error loading random recipe:', error);
        alert('Failed to load random recipe. Please try again.');
    }
}

// Generate new recipe (AI Mock)
async function generateRecipe() {
    const input = document.getElementById('generateInput');
    const btn = document.getElementById('generateBtn');
    
    if (!input || !input.value.trim()) return;
    
    const originalText = btn.innerText;
    btn.innerText = 'Cooking...';
    btn.disabled = true;

    try {
        const response = await fetch(`${API_URL}/recipes/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ input: input.value })
        });

        if (response.ok) {
            const recipe = await response.json();
            input.value = '';
            showRecipeModal(recipe);
            // Refresh grid to show new recipe
            loadRecipes();
        } else {
            alert('Failed to generate recipe');
        }
    } catch (e) {
        console.error(e);
        alert('Error generating recipe');
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
    }
}

// Initialize index page
function initIndexPage() {
    updateNavigation();
    
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) logoutBtn.addEventListener('click', logout);
    
    const closeModal = document.getElementById('closeModal');
    if (closeModal) closeModal.addEventListener('click', closeRecipeModal);
    
    // Close modal on outside click
    const modal = document.getElementById('recipeModal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeRecipeModal();
        });
    }
    
    const searchBtn = document.getElementById('searchBtn');
    const searchInput = document.getElementById('searchInput');
    
    if (searchBtn) {
        searchBtn.addEventListener('click', () => {
            loadRecipes(searchInput.value);
        });
    }
    
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') loadRecipes(searchInput.value);
        });
    }
    
    const randomBtn = document.getElementById('randomBtn');
    if (randomBtn) randomBtn.addEventListener('click', loadRandomRecipe);
    
    const generateBtn = document.getElementById('generateBtn');
    const generateInput = document.getElementById('generateInput');
    
    if (generateBtn) generateBtn.addEventListener('click', generateRecipe);
    if (generateInput) {
        generateInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') generateRecipe();
        });
    }
    
    loadRecipes();
}

// ============= LOGIN.HTML FUNCTIONS =============

async function handleLogin(event) {
    event.preventDefault();
    
    const emailOrUsername = document.getElementById('emailOrUsername').value;
    const password = document.getElementById('password').value;
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
        showError('errorMsg', 'Network error. Please try again later.');
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

// ============= REGISTER.HTML FUNCTIONS =============

async function handleRegister(event) {
    event.preventDefault();
    
    const email = document.getElementById('email').value;
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    const registerBtn = document.getElementById('registerBtn');

    hideError('errorMsg');
    hideError('successMsg');

    if (password !== confirmPassword) {
        showError('errorMsg', 'Passwords do not match!');
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
                successEl.textContent = 'Account created successfully! Redirecting...';
                successEl.classList.remove('hidden');
            }
            setTimeout(() => {
                window.location.href = 'login.html';
            }, 2000);
        } else {
            showError('errorMsg', data.message || 'Registration failed.');
        }
    } catch (error) {
        console.error('Registration error:', error);
        showError('errorMsg', 'Network error. Please try again later.');
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

// ============= FORGOT-PASSWORD.HTML FUNCTIONS =============

async function handleForgotPassword(event) {
    event.preventDefault();
    
    const email = document.getElementById('email').value;
    const resetBtn = document.getElementById('resetBtn');

    hideError('errorMsg');
    hideError('successMsg');

    resetBtn.disabled = true;
    resetBtn.textContent = 'Sending...';

    try {
        const response = await fetch(`${API_URL}/auth/forgot-password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: email })
        });

        if (response.ok) {
            const successEl = document.getElementById('successMsg');
            if (successEl) {
                successEl.textContent = 'Reset link sent! Redirecting...';
                successEl.classList.remove('hidden');
            }
            setTimeout(() => {
                window.location.href = 'login.html';
            }, 3000);
        } else {
            const data = await response.json();
            showError('errorMsg', data.message || 'Failed to send reset email.');
        }
    } catch (error) {
        showError('errorMsg', 'Network error.');
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

// ============= ACCOUNT.HTML FUNCTIONS =============

function initAccountPage() {
    if (!checkAuth()) {
        window.location.href = 'login.html';
        return;
    }
    
    const usernameDisplay = document.getElementById('usernameDisplay');
    if (usernameDisplay) usernameDisplay.textContent = currentUser.username;
    
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) logoutBtn.addEventListener('click', logout);
    
    // Tab switching
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.dataset.tab;
            tabButtons.forEach(b => b.classList.remove('active', 'text-emerald-600', 'border-emerald-600'));
            btn.classList.add('active', 'text-emerald-600', 'border-emerald-600');
            
            tabContents.forEach(content => {
                content.classList.add('hidden');
                if (content.id === `${tabName}Tab`) content.classList.remove('hidden');
            });
        });
    });
    
    loadSavedRecipes();
    loadLikedRecipes();
}

async function loadSavedRecipes() {
    const container = document.getElementById('savedRecipes');
    const empty = document.getElementById('savedEmpty');
    
    try {
        const response = await fetch(`${API_URL}/user/saved`, {
            headers: { 'Authorization': `Bearer ${currentUser.token}` }
        });
        
        const recipes = await response.json();
        const countEl = document.getElementById('savedCount');
        if (countEl) countEl.textContent = recipes.length;
        
        if (!recipes.length) {
            container.classList.add('hidden');
            empty.classList.remove('hidden');
        } else {
            container.classList.remove('hidden');
            empty.classList.add('hidden');
            container.innerHTML = '';
            recipes.forEach(recipe => {
                container.appendChild(createAccountRecipeCard(recipe, 'saved'));
            });
        }
    } catch (error) {
        console.error('Error loading saved recipes:', error);
    }
}

async function loadLikedRecipes() {
    const container = document.getElementById('likedRecipes');
    const empty = document.getElementById('likedEmpty');
    
    try {
        const response = await fetch(`${API_URL}/user/liked`, {
            headers: { 'Authorization': `Bearer ${currentUser.token}` }
        });
        
        const recipes = await response.json();
        const countEl = document.getElementById('likedCount');
        if (countEl) countEl.textContent = recipes.length;
        
        if (!recipes.length) {
            container.classList.add('hidden');
            empty.classList.remove('hidden');
        } else {
            container.classList.remove('hidden');
            empty.classList.add('hidden');
            container.innerHTML = '';
            recipes.forEach(recipe => {
                container.appendChild(createAccountRecipeCard(recipe, 'liked'));
            });
        }
    } catch (error) {
        console.error('Error loading liked recipes:', error);
    }
}

function createAccountRecipeCard(recipe, type) {
    const card = document.createElement('div');
    card.className = 'recipe-card bg-white rounded-xl shadow-md overflow-hidden relative border border-gray-100';
    card.innerHTML = `
        <div class="h-40 bg-gradient-to-br from-green-100 to-emerald-100 flex items-center justify-center text-5xl">
            ${recipe.emoji}
        </div>
        <div class="p-4">
            <h3 class="text-lg font-bold text-gray-800 mb-2 truncate">${recipe.name}</h3>
            <div class="flex justify-between text-sm text-gray-600 mb-4">
                <span>⏱️ ${recipe.time}</span>
                <span class="font-bold text-emerald-600">$${recipe.total_cost.toFixed(2)}</span>
            </div>
            <div class="flex gap-2">
                <button onclick="showRecipeModal({recipe_id: ${recipe.recipe_id}})" class="flex-1 px-3 py-2 bg-emerald-100 text-emerald-700 text-sm rounded-lg hover:bg-emerald-200 transition text-center font-semibold">
                    View
                </button>
                <button onclick="removeRecipe(${recipe.recipe_id}, '${type}')" 
                        class="px-3 py-2 bg-red-100 text-red-600 text-sm rounded-lg hover:bg-red-200 transition font-semibold">
                    Remove
                </button>
            </div>
        </div>
    `;
    return card;
}

// Updated: Uses recipeId 
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
            if (type === 'saved') loadSavedRecipes();
            else loadLikedRecipes();
        } else {
            alert('Failed to remove recipe.');
        }
    } catch (error) {
        console.error('Error removing recipe:', error);
    }
}

// ============= MAIN INIT =============

document.addEventListener('DOMContentLoaded', () => {
    window.saveRecipe = saveRecipe;
    window.likeRecipe = likeRecipe;
    window.showRecipeModal = showRecipeModal;
    window.removeRecipe = removeRecipe;

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