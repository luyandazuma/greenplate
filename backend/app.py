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

# Secret key for JWT (use environment variable in production)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# In-memory database (will be replaced with DynamoDB in AWS deployment)
users_db = {}
saved_recipes_db = {}
liked_recipes_db = {}

# Sample recipe database (will be in DynamoDB in production)
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
    recipe = random.choice(recipes_db)
    return jsonify(recipe), 200


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