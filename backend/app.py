from flask import Flask, request, jsonify
from flask_cors import CORS
import jwt
import datetime
import hashlib
import secrets
import random
import os
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal
import json
from io import BytesIO

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# ============= CONFIGURATION =============

SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['SECRET_KEY'] = SECRET_KEY

# DynamoDB Configuration
REGION = os.environ.get('AWS_REGION_NAME', 'af-south-1')
IS_LAMBDA = os.environ.get('AWS_EXECUTION_ENV') is not None

dynamodb = boto3.resource('dynamodb', region_name=REGION)

# Table names from environment
USERS_TABLE = os.environ.get('USERS_TABLE', 'greenplate-users-dev')
RECIPES_TABLE = os.environ.get('RECIPES_TABLE', 'greenplate-recipes-dev')
SAVED_RECIPES_TABLE = os.environ.get('SAVED_RECIPES_TABLE', 'greenplate-saved-recipes-dev')
LIKED_RECIPES_TABLE = os.environ.get('LIKED_RECIPES_TABLE', 'greenplate-liked-recipes-dev')

# Get table references
users_table = dynamodb.Table(USERS_TABLE)
recipes_table = dynamodb.Table(RECIPES_TABLE)
saved_recipes_table = dynamodb.Table(SAVED_RECIPES_TABLE)
liked_recipes_table = dynamodb.Table(LIKED_RECIPES_TABLE)

# ============= HELPER FUNCTIONS =============

def decimal_to_float(obj):
    """Convert Decimal objects to float for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_float(i) for i in obj]
    return obj

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token(username):
    """Generate JWT token"""
    payload = {
        'username': username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

def verify_token(token):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload['username']
    except:
        return None

def auth_required(f):
    """Authentication decorator"""
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

# ============= SAMPLE DATA =============

SAMPLE_RECIPES = [
    {
        'recipe_id': 1,
        'name': 'Creamy Pasta Carbonara',
        'emoji': '🍝',
        'time': '25 min',
        'difficulty': 'Medium',
        'servings': 4,
        'total_cost': Decimal('12.50'),
        'ingredients': [
            {'name': 'Spaghetti', 'amount': '400g', 'cost': Decimal('2.50')},
            {'name': 'Bacon', 'amount': '200g', 'cost': Decimal('4.00')},
            {'name': 'Eggs', 'amount': '4 large', 'cost': Decimal('3.00')},
            {'name': 'Parmesan', 'amount': '100g', 'cost': Decimal('2.50')},
            {'name': 'Black pepper', 'amount': '1 tsp', 'cost': Decimal('0.50')}
        ],
        'instructions': [
            'Boil water and cook spaghetti until al dente',
            'Fry bacon until crispy',
            'Whisk eggs with parmesan and pepper',
            'Drain pasta and mix with bacon',
            'Remove from heat and stir in egg mixture',
            'Serve immediately with extra parmesan'
        ]
    },
    {
        'recipe_id': 2,
        'name': 'Classic Beef Burger',
        'emoji': '🍔',
        'time': '20 min',
        'difficulty': 'Easy',
        'servings': 4,
        'total_cost': Decimal('15.20'),
        'ingredients': [
            {'name': 'Ground beef', 'amount': '500g', 'cost': Decimal('8.00')},
            {'name': 'Burger buns', 'amount': '4 pieces', 'cost': Decimal('2.50')},
            {'name': 'Lettuce', 'amount': '4 leaves', 'cost': Decimal('1.00')},
            {'name': 'Tomato', 'amount': '2 medium', 'cost': Decimal('1.50')},
            {'name': 'Cheese', 'amount': '4 slices', 'cost': Decimal('2.20')}
        ],
        'instructions': [
            'Shape beef into 4 equal patties',
            'Season with salt and pepper',
            'Grill or pan-fry for 4-5 minutes per side',
            'Add cheese in the last minute',
            'Toast the buns',
            'Assemble with lettuce and tomato'
        ]
    },
    {
        'recipe_id': 3,
        'name': 'Fresh Garden Salad',
        'emoji': '🥗',
        'time': '15 min',
        'difficulty': 'Easy',
        'servings': 4,
        'total_cost': Decimal('8.30'),
        'ingredients': [
            {'name': 'Mixed greens', 'amount': '300g', 'cost': Decimal('3.00')},
            {'name': 'Cherry tomatoes', 'amount': '200g', 'cost': Decimal('2.50')},
            {'name': 'Cucumber', 'amount': '1 large', 'cost': Decimal('1.20')},
            {'name': 'Red onion', 'amount': '1/2 medium', 'cost': Decimal('0.60')},
            {'name': 'Olive oil', 'amount': '3 tbsp', 'cost': Decimal('1.00')}
        ],
        'instructions': [
            'Wash and dry all vegetables',
            'Chop vegetables into bite-sized pieces',
            'Combine in a large bowl',
            'Drizzle with olive oil and vinegar',
            'Toss well and serve fresh'
        ]
    },
    {
        'recipe_id': 4,
        'name': 'Chicken Stir Fry',
        'emoji': '🍗',
        'time': '30 min',
        'difficulty': 'Medium',
        'servings': 4,
        'total_cost': Decimal('18.50'),
        'ingredients': [
            {'name': 'Chicken breast', 'amount': '600g', 'cost': Decimal('10.00')},
            {'name': 'Mixed vegetables', 'amount': '400g', 'cost': Decimal('4.50')},
            {'name': 'Soy sauce', 'amount': '3 tbsp', 'cost': Decimal('1.50')},
            {'name': 'Garlic', 'amount': '4 cloves', 'cost': Decimal('0.50')},
            {'name': 'Rice', 'amount': '2 cups', 'cost': Decimal('2.00')}
        ],
        'instructions': [
            'Cut chicken into bite-sized pieces',
            'Heat oil in wok or large pan',
            'Cook chicken until golden brown',
            'Add vegetables and stir fry for 5 minutes',
            'Add soy sauce and garlic',
            'Serve hot over steamed rice'
        ]
    },
    {
        'recipe_id': 5,
        'name': 'Margherita Pizza',
        'emoji': '🍕',
        'time': '40 min',
        'difficulty': 'Medium',
        'servings': 4,
        'total_cost': Decimal('14.00'),
        'ingredients': [
            {'name': 'Pizza dough', 'amount': '500g', 'cost': Decimal('3.00')},
            {'name': 'Tomato sauce', 'amount': '200ml', 'cost': Decimal('2.50')},
            {'name': 'Mozzarella', 'amount': '300g', 'cost': Decimal('6.00')},
            {'name': 'Fresh basil', 'amount': '1 bunch', 'cost': Decimal('1.50')},
            {'name': 'Olive oil', 'amount': '2 tbsp', 'cost': Decimal('1.00')}
        ],
        'instructions': [
            'Preheat oven to 250°C (480°F)',
            'Roll out pizza dough on floured surface',
            'Spread tomato sauce evenly',
            'Add torn mozzarella pieces',
            'Bake for 12-15 minutes until crispy',
            'Top with fresh basil and drizzle olive oil'
        ]
    },
    {
        'recipe_id': 6,
        'name': 'Chocolate Brownies',
        'emoji': '🍫',
        'time': '45 min',
        'difficulty': 'Easy',
        'servings': 9,
        'total_cost': Decimal('9.50'),
        'ingredients': [
            {'name': 'Butter', 'amount': '200g', 'cost': Decimal('3.00')},
            {'name': 'Dark chocolate', 'amount': '200g', 'cost': Decimal('3.50')},
            {'name': 'Sugar', 'amount': '1 cup', 'cost': Decimal('1.00')},
            {'name': 'Flour', 'amount': '1 cup', 'cost': Decimal('0.50')},
            {'name': 'Eggs', 'amount': '3 large', 'cost': Decimal('1.50')}
        ],
        'instructions': [
            'Preheat oven to 180°C (350°F)',
            'Melt butter and chocolate together',
            'Whisk eggs and sugar until fluffy',
            'Fold in chocolate mixture and flour',
            'Pour into baking pan',
            'Bake for 25-30 minutes'
        ]
    }
]

def init_sample_recipes():
    """Sync sample recipes to DynamoDB"""
    try:
        print("Syncing sample recipes...")
        for recipe in SAMPLE_RECIPES:
            recipes_table.put_item(Item=recipe)
            
        print(f"{len(SAMPLE_RECIPES)} sample recipes synced successfully")
        return True
    except Exception as e:
        print(f"Recipe init error: {e}")
        return False

# ============= ROUTES =============

@app.route('/', methods=['GET'])
def root():
    return jsonify({
        'message': 'GreenPlate Recipe API',
        'status': 'running',
        'version': '2.0.0',
        'endpoints': {
            'health': '/health',
            'recipes': '/api/recipes',
            'register': '/api/auth/register',
            'login': '/api/auth/login'
        }
    }), 200

@app.route('/health', methods=['GET'])
def health_check():
    try:
        response = recipes_table.scan(Limit=1)
        db_status = 'connected'
        recipe_count = response['Count']
    except Exception as e:
        db_status = f'error: {str(e)}'
        recipe_count = 0
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.datetime.utcnow().isoformat(),
        'dynamodb': db_status,
        'tables': {
            'users': USERS_TABLE,
            'recipes': RECIPES_TABLE,
            'saved': SAVED_RECIPES_TABLE,
            'liked': LIKED_RECIPES_TABLE
        },
        'recipe_count': recipe_count
    }), 200

# ============= AUTH ROUTES =============

@app.route('/api/auth/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({'message': 'No data provided'}), 400
        
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')
        
        if not all([email, username, password]):
            return jsonify({'message': 'All fields required'}), 400
        
        # Check if user exists
        response = users_table.get_item(Key={'username': username})
        if 'Item' in response:
            return jsonify({'message': 'Username already taken'}), 400
        
        # Create user
        users_table.put_item(Item={
            'username': username,
            'email': email,
            'password': hash_password(password),
            'created_at': datetime.datetime.utcnow().isoformat()
        })
        
        print(f"User registered: {username}")
        return jsonify({
            'message': 'User registered successfully',
            'username': username
        }), 201
        
    except Exception as e:
        print(f"Register error: {e}")
        return jsonify({'message': f'Registration failed: {str(e)}'}), 500

@app.route('/api/auth/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({'message': 'No data provided'}), 400
        
        email_or_username = data.get('email_or_username')
        password = data.get('password')
        
        if not all([email_or_username, password]):
            return jsonify({'message': 'Credentials required'}), 400
        
        # Try username first
        response = users_table.get_item(Key={'username': email_or_username})
        user = response.get('Item')
        
        # Try email if username not found
        if not user:
            response = users_table.query(
                IndexName='EmailIndex',
                KeyConditionExpression=Key('email').eq(email_or_username)
            )
            if response['Items']:
                user = response['Items'][0]
        
        if user and user['password'] == hash_password(password):
            token = generate_token(user['username'])
            print(f"Login successful: {user['username']}")
            return jsonify({
                'token': token,
                'username': user['username'],
                'message': 'Login successful'
            }), 200
        
        return jsonify({'message': 'Invalid credentials'}), 401
        
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'message': f'Login failed: {str(e)}'}), 500

@app.route('/api/auth/forgot-password', methods=['POST', 'OPTIONS'])
def forgot_password():
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.get_json(force=True, silent=True)
    email = data.get('email') if data else None
    
    if not email:
        return jsonify({'message': 'Email required'}), 400
    
    # In production, send actual reset email
    reset_token = secrets.token_urlsafe(32)
    return jsonify({
        'message': 'Password reset instructions sent to email',
        'reset_token': reset_token  # Remove in production
    }), 200

# ============= RECIPE ROUTES =============

@app.route('/api/recipes', methods=['GET', 'OPTIONS'])
def get_recipes():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        response = recipes_table.scan()
        recipes = decimal_to_float(response['Items'])
        print(f"Returning {len(recipes)} recipes")
        return jsonify(recipes), 200
    except Exception as e:
        print(f"Get recipes error: {e}")
        return jsonify([]), 500

@app.route('/api/recipes/<int:recipe_id>', methods=['GET', 'OPTIONS'])
def get_recipe(recipe_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        response = recipes_table.get_item(Key={'recipe_id': recipe_id})
        if 'Item' in response:
            return jsonify(decimal_to_float(response['Item'])), 200
        return jsonify({'message': 'Recipe not found'}), 404
    except Exception as e:
        print(f"Get recipe error: {e}")
        return jsonify({'message': 'Error loading recipe'}), 500

@app.route('/api/recipes/search', methods=['GET', 'OPTIONS'])
def search_recipes():
    if request.method == 'OPTIONS':
        return '', 200
    
    query = request.args.get('q', '').lower()
    try:
        response = recipes_table.scan()
        recipes = response['Items']
        if query:
            recipes = [r for r in recipes if query in r.get('name', '').lower()]
        return jsonify(decimal_to_float(recipes)), 200
    except Exception as e:
        print(f"Search error: {e}")
        return jsonify([]), 500

@app.route('/api/recipes/random', methods=['GET', 'OPTIONS'])
def random_recipe():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        response = recipes_table.scan()
        recipes = response['Items']
        if recipes:
            return jsonify(decimal_to_float(random.choice(recipes))), 200
        return jsonify({'message': 'No recipes available'}), 404
    except Exception as e:
        print(f"Random recipe error: {e}")
        return jsonify({'message': 'Error'}), 500

@app.route('/api/recipes/generate', methods=['POST', 'OPTIONS'])
def generate_recipe():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json(force=True, silent=True)
        user_input = data.get('input', '').strip() if data else ''
        
        if not user_input:
            return jsonify({'message': 'Recipe name required'}), 400
        
        # Get max recipe_id
        response = recipes_table.scan()
        max_id = max([r.get('recipe_id', 0) for r in response['Items']], default=0)
        new_id = max_id + 1
        
        # Generate simple recipe
        new_recipe = {
            'recipe_id': new_id,
            'name': user_input.title(),
            'emoji': '🍽️',
            'time': '30 min',
            'difficulty': 'Medium',
            'servings': 4,
            'total_cost': Decimal('12.00'),
            'ingredients': [
                {'name': 'Main ingredient', 'amount': '500g', 'cost': Decimal('8.00')},
                {'name': 'Seasonings', 'amount': 'To taste', 'cost': Decimal('2.00')},
                {'name': 'Cooking oil', 'amount': '2 tbsp', 'cost': Decimal('2.00')}
            ],
            'instructions': [
                'Prepare all ingredients',
                'Cook the main ingredient',
                'Add seasonings to taste',
                'Serve hot and enjoy'
            ]
        }
        
        recipes_table.put_item(Item=new_recipe)
        print(f"Recipe generated: {new_recipe['name']}")
        return jsonify(decimal_to_float(new_recipe)), 201
        
    except Exception as e:
        print(f"Generate error: {e}")
        return jsonify({'message': 'Generation failed'}), 500

# ============= USER ROUTES =============

@app.route('/api/user/saved', methods=['GET', 'POST', 'OPTIONS'])
@auth_required
def handle_saved_recipes(username):
    if request.method == 'OPTIONS':
        return '', 200
    
    if request.method == 'GET':
        try:
            response = saved_recipes_table.query(
                KeyConditionExpression=Key('username').eq(username)
            )
            recipe_ids = [int(item['recipe_id']) for item in response['Items']]
            
            recipes = []
            for rid in recipe_ids:
                r = recipes_table.get_item(Key={'recipe_id': rid})
                if 'Item' in r:
                    recipes.append(r['Item'])
            
            return jsonify(decimal_to_float(recipes)), 200
        except Exception as e:
            print(f"Get saved error: {e}")
            return jsonify([]), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json(force=True, silent=True)
            recipe_id = data.get('recipe_id') if data else None
            
            if not recipe_id:
                return jsonify({'message': 'Recipe ID required'}), 400
            
            saved_recipes_table.put_item(Item={
                'username': username,
                'recipe_id': recipe_id,
                'saved_at': datetime.datetime.utcnow().isoformat()
            })
            return jsonify({'message': 'Recipe saved'}), 200
        except Exception as e:
            print(f"Save error: {e}")
            return jsonify({'message': 'Save failed'}), 500

@app.route('/api/user/saved/<int:recipe_id>', methods=['DELETE', 'OPTIONS'])
@auth_required
def remove_saved_recipe(username, recipe_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        saved_recipes_table.delete_item(Key={
            'username': username,
            'recipe_id': recipe_id
        })
        return jsonify({'message': 'Recipe removed'}), 200
    except Exception as e:
        print(f"Remove error: {e}")
        return jsonify({'message': 'Remove failed'}), 500

@app.route('/api/user/liked', methods=['GET', 'POST', 'OPTIONS'])
@auth_required
def handle_liked_recipes(username):
    if request.method == 'OPTIONS':
        return '', 200
    
    if request.method == 'GET':
        try:
            response = liked_recipes_table.query(
                KeyConditionExpression=Key('username').eq(username)
            )
            recipe_ids = [int(item['recipe_id']) for item in response['Items']]
            
            recipes = []
            for rid in recipe_ids:
                r = recipes_table.get_item(Key={'recipe_id': rid})
                if 'Item' in r:
                    recipes.append(r['Item'])
            
            return jsonify(decimal_to_float(recipes)), 200
        except Exception as e:
            print(f"Get liked error: {e}")
            return jsonify([]), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json(force=True, silent=True)
            recipe_id = data.get('recipe_id') if data else None
            
            if not recipe_id:
                return jsonify({'message': 'Recipe ID required'}), 400
            
            liked_recipes_table.put_item(Item={
                'username': username,
                'recipe_id': recipe_id,
                'liked_at': datetime.datetime.utcnow().isoformat()
            })
            return jsonify({'message': 'Recipe liked'}), 200
        except Exception as e:
            print(f"Like error: {e}")
            return jsonify({'message': 'Like failed'}), 500

@app.route('/api/user/liked/<int:recipe_id>', methods=['DELETE', 'OPTIONS'])
@auth_required
def remove_liked_recipe(username, recipe_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        liked_recipes_table.delete_item(Key={
            'username': username,
            'recipe_id': recipe_id
        })
        return jsonify({'message': 'Recipe unliked'}), 200
    except Exception as e:
        print(f"Unlike error: {e}")
        return jsonify({'message': 'Unlike failed'}), 500

# ============= LAMBDA HANDLER =============

def lambda_handler(event, context):
    """AWS Lambda handler for API Gateway proxy integration"""
    print(f"Request: {event.get('httpMethod')} {event.get('path')}")
    
    try:
        # Handle OPTIONS for CORS
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization'
                },
                'body': ''
            }
        
        # Build WSGI environ
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        query_params = event.get('queryStringParameters') or {}
        query_string = '&'.join([f"{k}={v}" for k, v in query_params.items()])
        
        body = event.get('body') or ''
        if event.get('isBase64Encoded'):
            import base64
            body = base64.b64decode(body).decode('utf-8')
        
        environ = {
            'REQUEST_METHOD': http_method,
            'SCRIPT_NAME': '',
            'PATH_INFO': path,
            'QUERY_STRING': query_string,
            'CONTENT_TYPE': event.get('headers', {}).get('content-type', 'application/json'),
            'CONTENT_LENGTH': str(len(body)),
            'SERVER_NAME': 'lambda',
            'SERVER_PORT': '443',
            'SERVER_PROTOCOL': 'HTTP/1.1',
            'wsgi.version': (1, 0),
            'wsgi.url_scheme': 'https',
            'wsgi.input': BytesIO(body.encode('utf-8')),
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
        
        # Process request through Flask
        with app.request_context(environ):
            response = app.full_dispatch_request()
        
        # Build Lambda response
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Content-Type': 'application/json'
        }
        headers.update(dict(response.headers))
        
        result = {
            'statusCode': response.status_code,
            'headers': headers,
            'body': response.get_data(as_text=True)
        }
        
        print(f"Response: {response.status_code}")
        return result
        
    except Exception as e:
        print(f" Lambda error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'message': f'Internal error: {str(e)}'})
        }

# Initialize recipes on Lambda cold start
if IS_LAMBDA:
    print("Lambda cold start - initializing...")
    init_sample_recipes()
    print("Lambda ready")

# Local development server
if __name__ == '__main__':
    print("Starting local development server...")
    init_sample_recipes()
    app.run(debug=True, host='0.0.0.0', port=5000)