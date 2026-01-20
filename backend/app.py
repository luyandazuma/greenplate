from flask import Flask, request, jsonify
from flask_cors import CORS
import jwt
import datetime
import hashlib
import secrets
import random
import os

app = Flask(__name__)
CORS(app)

# Secret key for JWT
# Generate a random secret key if not set
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    # Generate a random secret key for development
    SECRET_KEY = secrets.token_hex(32)
    print(f"   WARNING: Using auto-generated SECRET_KEY for development")
    print(f"    For production, set SECRET_KEY environment variable")

app.config['SECRET_KEY'] = SECRET_KEY

# In-memory database (will be replaced with DynamoDB in AWS deployment)
users_db = {}
saved_recipes_db = {}
liked_recipes_db = {}

# Sample recipe database (will be in DynamoDB in production)
# Initialize with counter for new recipes
recipe_id_counter = 7

recipes_db = [
    {
        'id': 1,
        'name': 'Creamy Pasta Carbonara',
        'emoji': '🍝',
        'time': '25 min',
        'difficulty': 'Medium',
        'servings': 4,
        'total_cost': 12.50,
        'ingredients': [
            {'name': 'Spaghetti', 'amount': '400g', 'cost': 2.50},
            {'name': 'Bacon', 'amount': '200g', 'cost': 4.00},
            {'name': 'Eggs', 'amount': '4 large', 'cost': 3.00},
            {'name': 'Parmesan cheese', 'amount': '100g', 'cost': 2.50},
            {'name': 'Black pepper', 'amount': '1 tsp', 'cost': 0.50}
        ],
        'instructions': [
            'Bring a large pot of salted water to boil and cook spaghetti according to package directions',
            'While pasta cooks, fry bacon in a large skillet until crispy',
            'In a bowl, whisk together eggs, grated parmesan, and black pepper',
            'Drain pasta, reserving 1 cup of pasta water',
            'Add hot pasta to the skillet with bacon, remove from heat',
            'Quickly stir in egg mixture, adding pasta water to create a creamy sauce',
            'Serve immediately with extra parmesan and black pepper'
        ]
    },
    {
        'id': 2,
        'name': 'Classic Beef Burger',
        'emoji': '🍔',
        'time': '20 min',
        'difficulty': 'Easy',
        'servings': 4,
        'total_cost': 15.20,
        'ingredients': [
            {'name': 'Ground beef', 'amount': '500g', 'cost': 8.00},
            {'name': 'Burger buns', 'amount': '4 pieces', 'cost': 2.50},
            {'name': 'Lettuce', 'amount': '4 leaves', 'cost': 1.00},
            {'name': 'Tomato', 'amount': '2 medium', 'cost': 1.50},
            {'name': 'Cheese slices', 'amount': '4 slices', 'cost': 2.20}
        ],
        'instructions': [
            'Divide ground beef into 4 equal portions and shape into patties',
            'Season both sides generously with salt and pepper',
            'Heat a grill or skillet over medium-high heat',
            'Cook patties for 4-5 minutes per side for medium doneness',
            'Add cheese slices in the last minute of cooking',
            'Toast burger buns lightly on the grill',
            'Assemble burgers with lettuce, tomato, patty, and your favorite condiments'
        ]
    },
    {
        'id': 3,
        'name': 'Fresh Garden Salad',
        'emoji': '🥗',
        'time': '15 min',
        'difficulty': 'Easy',
        'servings': 4,
        'total_cost': 8.30,
        'ingredients': [
            {'name': 'Mixed greens', 'amount': '300g', 'cost': 3.00},
            {'name': 'Cherry tomatoes', 'amount': '200g', 'cost': 2.50},
            {'name': 'Cucumber', 'amount': '1 large', 'cost': 1.20},
            {'name': 'Red onion', 'amount': '1/2 medium', 'cost': 0.60},
            {'name': 'Olive oil', 'amount': '3 tbsp', 'cost': 1.00}
        ],
        'instructions': [
            'Wash and dry all vegetables thoroughly',
            'Tear or chop mixed greens into bite-sized pieces',
            'Halve cherry tomatoes and slice cucumber',
            'Thinly slice red onion',
            'Combine all vegetables in a large bowl',
            'Drizzle with olive oil and your choice of vinegar',
            'Season with salt and pepper, toss well and serve immediately'
        ]
    },
    {
        'id': 4,
        'name': 'Chicken Teriyaki Bowl',
        'emoji': '🍱',
        'time': '35 min',
        'difficulty': 'Medium',
        'servings': 4,
        'total_cost': 14.80,
        'ingredients': [
            {'name': 'Chicken breast', 'amount': '500g', 'cost': 7.00},
            {'name': 'Rice', 'amount': '2 cups', 'cost': 2.00},
            {'name': 'Soy sauce', 'amount': '1/4 cup', 'cost': 1.50},
            {'name': 'Honey', 'amount': '2 tbsp', 'cost': 1.80},
            {'name': 'Broccoli', 'amount': '300g', 'cost': 2.50}
        ],
        'instructions': [
            'Cook rice according to package instructions',
            'Cut chicken into bite-sized pieces',
            'Mix soy sauce, honey, garlic, and ginger for teriyaki sauce',
            'Cook chicken in a hot pan until golden brown',
            'Add teriyaki sauce and simmer until chicken is glazed',
            'Steam broccoli until tender-crisp',
            'Serve chicken and broccoli over rice, drizzle with extra sauce'
        ]
    },
    {
        'id': 5,
        'name': 'Margherita Pizza',
        'emoji': '🍕',
        'time': '30 min',
        'difficulty': 'Medium',
        'servings': 4,
        'total_cost': 11.50,
        'ingredients': [
            {'name': 'Pizza dough', 'amount': '500g', 'cost': 3.00},
            {'name': 'Tomato sauce', 'amount': '1 cup', 'cost': 2.00},
            {'name': 'Mozzarella cheese', 'amount': '300g', 'cost': 4.50},
            {'name': 'Fresh basil', 'amount': '1 bunch', 'cost': 1.50},
            {'name': 'Olive oil', 'amount': '2 tbsp', 'cost': 0.50}
        ],
        'instructions': [
            'Preheat oven to 475°F (245°C)',
            'Roll out pizza dough into desired shape',
            'Spread tomato sauce evenly over dough',
            'Tear mozzarella and distribute over sauce',
            'Drizzle with olive oil and season with salt',
            'Bake for 12-15 minutes until crust is golden and cheese is bubbly',
            'Top with fresh basil leaves and serve hot'
        ]
    },
    {
        'id': 6,
        'name': 'Chocolate Chip Cookies',
        'emoji': '🍪',
        'time': '40 min',
        'difficulty': 'Easy',
        'servings': 24,
        'total_cost': 9.20,
        'ingredients': [
            {'name': 'Flour', 'amount': '2 cups', 'cost': 1.50},
            {'name': 'Butter', 'amount': '200g', 'cost': 3.00},
            {'name': 'Sugar', 'amount': '1 cup', 'cost': 1.20},
            {'name': 'Eggs', 'amount': '2 large', 'cost': 1.50},
            {'name': 'Chocolate chips', 'amount': '2 cups', 'cost': 2.00}
        ],
        'instructions': [
            'Preheat oven to 350°F (175°C)',
            'Cream together butter and sugar until fluffy',
            'Beat in eggs one at a time',
            'Mix in flour, baking soda, and salt',
            'Fold in chocolate chips',
            'Drop spoonfuls of dough onto baking sheets',
            'Bake for 10-12 minutes until edges are golden',
            'Cool on baking sheet for 5 minutes before transferring'
        ]
    }
]

# Helper function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Helper function to generate JWT token
def generate_token(username):
    payload = {
        'username': username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

# Helper function to verify JWT token
def verify_token(token):
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload['username']
    except:
        return None

# Authentication middleware
def auth_required(f):
    def decorator(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        token = token.replace('Bearer ', '')
        username = verify_token(token)
        
        if not username:
            return jsonify({'message': 'Invalid token'}), 401
        
        return f(username, *args, **kwargs)
    decorator.__name__ = f.__name__
    return decorator


# ============= CORS PREFLIGHT HANDLER =============
@app.route('/', methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def handle_options(path=''):
    return '', 204


# ============= ROOT/HEALTH CHECK =============
@app.route('/', methods=['GET'])
def root():
    return jsonify({
        'message': 'GreenPlate Recipe API',
        'status': 'running',
        'version': '1.0.0'
    }), 200

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.datetime.utcnow().isoformat()
    }), 200


# ============= AUTH ROUTES =============

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')
    
    if not email or not username or not password:
        return jsonify({'message': 'All fields are required'}), 400
    
    # Check if user already exists
    for user_id, user in users_db.items():
        if user['email'] == email:
            return jsonify({'message': 'Email already registered'}), 400
        if user['username'] == username:
            return jsonify({'message': 'Username already taken'}), 400
    
    # Create new user
    user_id = str(len(users_db) + 1)
    users_db[user_id] = {
        'id': user_id,
        'email': email,
        'username': username,
        'password': hash_password(password),
        'created_at': datetime.datetime.utcnow().isoformat()
    }
    
    return jsonify({'message': 'User registered successfully'}), 201


@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    email_or_username = data.get('email_or_username')
    password = data.get('password')
    
    if not email_or_username or not password:
        return jsonify({'message': 'Email/username and password are required'}), 400
    
    hashed_password = hash_password(password)
    
    # Find user
    for user_id, user in users_db.items():
        if (user['email'] == email_or_username or user['username'] == email_or_username) and user['password'] == hashed_password:
            token = generate_token(user['username'])
            return jsonify({
                'token': token,
                'username': user['username'],
                'message': 'Login successful'
            }), 200
    
    return jsonify({'message': 'Invalid credentials'}), 401


@app.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    data = request.json
    email = data.get('email')
    
    if not email:
        return jsonify({'message': 'Email is required'}), 400
    
    # Check if email exists
    user_exists = any(user['email'] == email for user in users_db.values())
    
    # Always return success for security (don't reveal if email exists)
    reset_token = secrets.token_urlsafe(32)
    
    return jsonify({
        'message': 'If this email is registered, you will receive a password reset link',
        'reset_token': reset_token  # In production, send this via email, not in response
    }), 200


# ============= RECIPE ROUTES =============

@app.route('/api/recipes', methods=['GET'])
def get_recipes():
    return jsonify(recipes_db), 200


@app.route('/api/recipes/<int:recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    recipe = next((r for r in recipes_db if r['id'] == recipe_id), None)
    if not recipe:
        return jsonify({'message': 'Recipe not found'}), 404
    return jsonify(recipe), 200


@app.route('/api/recipes/search', methods=['GET'])
def search_recipes():
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify(recipes_db), 200
    results = [r for r in recipes_db if query in r['name'].lower()]
    return jsonify(results), 200


@app.route('/api/recipes/random', methods=['GET'])
def random_recipe():
    if not recipes_db:
        return jsonify({'message': 'No recipes available'}), 404
    recipe = random.choice(recipes_db)
    return jsonify(recipe), 200


# ============= RECIPE GENERATION ROUTES =============

@app.route('/api/recipes/generate', methods=['POST'])
def generate_recipe():
    """
    Generate a recipe based on user input
    Accepts: dish name, ingredients list, or description
    """
    global recipe_id_counter
    
    data = request.json
    user_input = data.get('input', '').strip()
    
    if not user_input:
        return jsonify({'message': 'Please provide a recipe name or description'}), 400
    
    # Generate recipe based on user input
    new_recipe = create_recipe_from_input(user_input, recipe_id_counter)
    
    # Add to database
    recipes_db.append(new_recipe)
    recipe_id_counter += 1
    
    return jsonify(new_recipe), 201


def create_recipe_from_input(user_input, recipe_id):
    """
    Create a recipe structure based on user input
    In production, this would use AI/ML service like Bedrock or OpenAI
    For now, generates a structured recipe based on keywords
    """
    
    # Parse input to determine recipe type
    input_lower = user_input.lower()
    
    # Determine emoji based on keywords
    emoji = determine_emoji(input_lower)
    
    # Generate recipe name
    recipe_name = user_input.title() if len(user_input.split()) <= 5 else user_input.title()[:50]
    
    # Determine difficulty
    difficulty = determine_difficulty(input_lower)
    
    # Determine cooking time
    time = determine_time(input_lower, difficulty)
    
    # Generate ingredients based on input
    ingredients = generate_ingredients(input_lower)
    
    # Calculate total cost
    total_cost = sum(ing['cost'] for ing in ingredients)
    
    # Generate instructions
    instructions = generate_instructions(input_lower, ingredients)
    
    # Determine servings
    servings = determine_servings(input_lower)
    
    return {
        'id': recipe_id,
        'name': recipe_name,
        'emoji': emoji,
        'time': time,
        'difficulty': difficulty,
        'servings': servings,
        'total_cost': round(total_cost, 2),
        'ingredients': ingredients,
        'instructions': instructions,
        'user_generated': True
    }


def determine_emoji(text):
    """Determine emoji based on recipe keywords"""
    emoji_map = {
        'pasta': '🍝', 'spaghetti': '🍝', 'noodle': '🍜',
        'burger': '🍔', 'beef': '🍔',
        'pizza': '🍕',
        'salad': '🥗', 'vegetables': '🥗', 'greens': '🥗',
        'soup': '🍲', 'stew': '🍲',
        'chicken': '🍗', 'poultry': '🍗',
        'fish': '🐟', 'seafood': '🦐', 'shrimp': '🦐',
        'rice': '🍚', 'bowl': '🍱',
        'taco': '🌮', 'burrito': '🌯',
        'sandwich': '🥪',
        'curry': '🍛',
        'cake': '🎂', 'cookie': '🍪', 'dessert': '🍰',
        'bread': '🍞', 'toast': '🍞',
        'egg': '🥚', 'omelette': '🥚',
        'bacon': '🥓',
        'breakfast': '🍳',
        'smoothie': '🥤', 'drink': '🥤',
        'steak': '🥩', 'meat': '🥩'
    }
    
    for keyword, emoji in emoji_map.items():
        if keyword in text:
            return emoji
    
    return '🍽️'  # Default


def determine_difficulty(text):
    """Determine difficulty based on keywords"""
    if any(word in text for word in ['easy', 'simple', 'quick', 'basic']):
        return 'Easy'
    elif any(word in text for word in ['hard', 'complex', 'advanced', 'gourmet']):
        return 'Hard'
    else:
        return 'Medium'


def determine_time(text, difficulty):
    """Estimate cooking time"""
    if 'quick' in text or difficulty == 'Easy':
        return f"{random.randint(10, 25)} min"
    elif difficulty == 'Hard':
        return f"{random.randint(45, 90)} min"
    else:
        return f"{random.randint(25, 50)} min"


def determine_servings(text):
    """Determine number of servings"""
    if 'one' in text or 'single' in text or 'solo' in text:
        return 1
    elif 'two' in text or 'couple' in text:
        return 2
    elif 'family' in text or 'large' in text:
        return 6
    else:
        return 4


def generate_ingredients(text):
    """Generate ingredient list based on recipe type"""
    
    # Common ingredients database
    ingredient_database = {
        'pasta': [
            {'name': 'Pasta', 'amount': '400g', 'cost': 2.50},
            {'name': 'Olive oil', 'amount': '3 tbsp', 'cost': 1.00},
            {'name': 'Garlic', 'amount': '3 cloves', 'cost': 0.50},
            {'name': 'Parmesan cheese', 'amount': '100g', 'cost': 3.50},
            {'name': 'Salt and pepper', 'amount': 'To taste', 'cost': 0.30}
        ],
        'chicken': [
            {'name': 'Chicken breast', 'amount': '500g', 'cost': 7.00},
            {'name': 'Olive oil', 'amount': '2 tbsp', 'cost': 0.80},
            {'name': 'Garlic powder', 'amount': '1 tsp', 'cost': 0.50},
            {'name': 'Paprika', 'amount': '1 tsp', 'cost': 0.60},
            {'name': 'Salt and pepper', 'amount': 'To taste', 'cost': 0.30}
        ],
        'salad': [
            {'name': 'Mixed greens', 'amount': '300g', 'cost': 3.00},
            {'name': 'Cherry tomatoes', 'amount': '200g', 'cost': 2.50},
            {'name': 'Cucumber', 'amount': '1 large', 'cost': 1.20},
            {'name': 'Olive oil', 'amount': '3 tbsp', 'cost': 1.00},
            {'name': 'Lemon juice', 'amount': '2 tbsp', 'cost': 0.50}
        ],
        'rice': [
            {'name': 'Rice', 'amount': '2 cups', 'cost': 2.00},
            {'name': 'Chicken broth', 'amount': '4 cups', 'cost': 2.50},
            {'name': 'Onion', 'amount': '1 medium', 'cost': 0.80},
            {'name': 'Garlic', 'amount': '2 cloves', 'cost': 0.40},
            {'name': 'Butter', 'amount': '2 tbsp', 'cost': 0.90}
        ],
        'soup': [
            {'name': 'Vegetable broth', 'amount': '6 cups', 'cost': 3.00},
            {'name': 'Mixed vegetables', 'amount': '500g', 'cost': 4.00},
            {'name': 'Onion', 'amount': '1 large', 'cost': 1.00},
            {'name': 'Garlic', 'amount': '3 cloves', 'cost': 0.50},
            {'name': 'Herbs', 'amount': '1 tbsp', 'cost': 1.00}
        ],
        'sandwich': [
            {'name': 'Bread', 'amount': '8 slices', 'cost': 2.50},
            {'name': 'Deli meat', 'amount': '300g', 'cost': 5.00},
            {'name': 'Cheese', 'amount': '4 slices', 'cost': 2.00},
            {'name': 'Lettuce', 'amount': '4 leaves', 'cost': 0.80},
            {'name': 'Tomato', 'amount': '1 large', 'cost': 1.20}
        ]
    }
    
    # Find matching category
    for category, ingredients in ingredient_database.items():
        if category in text:
            return ingredients
    
    # Default generic ingredients
    return [
        {'name': 'Main ingredient', 'amount': '500g', 'cost': 6.00},
        {'name': 'Olive oil', 'amount': '2 tbsp', 'cost': 0.80},
        {'name': 'Garlic', 'amount': '2 cloves', 'cost': 0.40},
        {'name': 'Onion', 'amount': '1 medium', 'cost': 0.80},
        {'name': 'Herbs and spices', 'amount': 'To taste', 'cost': 1.50}
    ]


def generate_instructions(text, ingredients):
    """Generate cooking instructions"""
    
    # Extract ingredient names for instructions
    ingredient_names = [ing['name'].lower() for ing in ingredients]
    
    instructions = [
        f"Gather all ingredients: {', '.join(ingredient_names[:3])} and others",
        "Prepare your cooking area and preheat if needed"
    ]
    
    # Add cooking steps based on recipe type
    if 'pasta' in text or 'spaghetti' in text:
        instructions.extend([
            "Bring a large pot of salted water to boil",
            "Cook pasta according to package directions until al dente",
            "While pasta cooks, prepare the sauce in a separate pan",
            "Drain pasta, reserving some pasta water",
            "Combine pasta with sauce, adding pasta water if needed",
            "Serve hot with grated cheese on top"
        ])
    elif 'salad' in text:
        instructions.extend([
            "Wash and dry all vegetables thoroughly",
            "Chop vegetables into bite-sized pieces",
            "Combine all vegetables in a large bowl",
            "Prepare dressing by whisking oil and seasonings",
            "Toss salad with dressing just before serving"
        ])
    elif 'soup' in text or 'stew' in text:
        instructions.extend([
            "Heat oil in a large pot over medium heat",
            "Sauté aromatics until fragrant",
            "Add main ingredients and cook briefly",
            "Pour in broth and bring to a boil",
            "Reduce heat and simmer for 20-30 minutes",
            "Season to taste and serve hot"
        ])
    elif 'chicken' in text or 'meat' in text:
        instructions.extend([
            "Season the protein with salt, pepper, and spices",
            "Heat oil in a pan over medium-high heat",
            "Cook until golden brown on both sides",
            "Reduce heat and continue cooking until done",
            "Let rest for 5 minutes before serving"
        ])
    else:
        # Generic instructions
        instructions.extend([
            "Prepare all ingredients as specified",
            "Heat cooking oil in a pan over medium heat",
            "Add ingredients in order of cooking time needed",
            "Cook until everything is done to your preference",
            "Season with salt and pepper to taste",
            "Serve immediately while hot and enjoy"
        ])
    
    return instructions


# ============= USER ROUTES =============

@app.route('/api/user/saved', methods=['GET'])
@auth_required
def get_saved_recipes(username):
    user_saved = saved_recipes_db.get(username, [])
    recipes = [r for r in recipes_db if r['id'] in user_saved]
    return jsonify(recipes), 200


@app.route('/api/user/saved', methods=['POST'])
@auth_required
def save_recipe(username):
    data = request.json
    recipe_id = data.get('recipe_id')
    
    if username not in saved_recipes_db:
        saved_recipes_db[username] = []
    
    if recipe_id not in saved_recipes_db[username]:
        saved_recipes_db[username].append(recipe_id)
    
    return jsonify({'message': 'Recipe saved successfully'}), 200


@app.route('/api/user/saved/<int:recipe_id>', methods=['DELETE'])
@auth_required
def remove_saved_recipe(username, recipe_id):
    if username in saved_recipes_db and recipe_id in saved_recipes_db[username]:
        saved_recipes_db[username].remove(recipe_id)
    return jsonify({'message': 'Recipe removed from saved'}), 200


@app.route('/api/user/liked', methods=['GET'])
@auth_required
def get_liked_recipes(username):
    user_liked = liked_recipes_db.get(username, [])
    recipes = [r for r in recipes_db if r['id'] in user_liked]
    return jsonify(recipes), 200


@app.route('/api/user/liked', methods=['POST'])
@auth_required
def like_recipe(username):
    data = request.json
    recipe_id = data.get('recipe_id')
    
    if username not in liked_recipes_db:
        liked_recipes_db[username] = []
    
    if recipe_id not in liked_recipes_db[username]:
        liked_recipes_db[username].append(recipe_id)
    
    return jsonify({'message': 'Recipe liked successfully'}), 200


@app.route('/api/user/liked/<int:recipe_id>', methods=['DELETE'])
@auth_required
def remove_liked_recipe(username, recipe_id):
    if username in liked_recipes_db and recipe_id in liked_recipes_db[username]:
        liked_recipes_db[username].remove(recipe_id)
    return jsonify({'message': 'Recipe removed from liked'}), 200


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'message': 'Internal server error'}), 500


# Lambda handler for AWS deployment
def lambda_handler(event, context):
    """
    AWS Lambda handler function
    This allows the Flask app to run on AWS Lambda with API Gateway
    """
    from werkzeug.wrappers import Request, Response
    from io import BytesIO
    
    # Convert API Gateway event to Flask request
    environ = {
        'REQUEST_METHOD': event['httpMethod'],
        'SCRIPT_NAME': '',
        'PATH_INFO': event['path'],
        'QUERY_STRING': '&'.join([f"{k}={v}" for k, v in event.get('queryStringParameters', {}).items()]) if event.get('queryStringParameters') else '',
        'SERVER_NAME': 'lambda',
        'SERVER_PORT': '443',
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'https',
        'wsgi.input': BytesIO(event.get('body', '').encode('utf-8')),
        'wsgi.errors': BytesIO(),
        'wsgi.multiprocess': False,
        'wsgi.multithread': False,
        'wsgi.run_once': False,
    }
    
    # Add headers
    for key, value in event.get('headers', {}).items():
        key = key.upper().replace('-', '_')
        if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
            key = f'HTTP_{key}'
        environ[key] = value
    
    # Get response from Flask app
    request = Request(environ)
    with app.request_context(environ):
        try:
            response = app.full_dispatch_request()
        except Exception as e:
            response = Response(str(e), status=500)
    
    # Convert Flask response to API Gateway format
    return {
        'statusCode': response.status_code,
        'headers': dict(response.headers),
        'body': response.get_data(as_text=True)
    }


if __name__ == '__main__':
    # For local development
    app.run(debug=True, host='0.0.0.0', port=5000)