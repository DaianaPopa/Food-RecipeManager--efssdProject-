# This code imports the Flask library and some functions from it.
from flask import Flask, render_template, url_for, request, flash, redirect, session
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf

from db.db import *


# Create a Flask application instance
app = Flask(__name__)

app.secret_key = 'your_secret_key'  # Required for CSRF protection
csrf = CSRFProtect(app)  # This automatically protects all POST routes

@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf())


# Global variable for site name: Used in templates to display the site name
siteName = "KitchenHub"
# Set the site name in the app context
@app.context_processor
def inject_site_name():
    return dict(siteName=siteName)


# Routes
#===================
# These define which template is loaded, or action is taken, depending on the URL requested
#===================


# Home Page - Only for logged-in users
@app.route('/')
def home():
    # Check if user is NOT logged in
    if 'user_id' not in session:
        # If not logged in, show public welcome page
        return render_template('public_welcome.html', title="Welcome to KitchenHub")
    
    # If logged in, show the real home page
    userName = session.get('username', 'Guest')
    return render_template('home.html', title="Welcome", username=userName)

# About Page
@app.route('/about/')
def about():
    #check if yser is logged in
    if 'user_id' not in session:
        flash('please login to access the About page', 'warning')
    # Render HTML with the name in a H1 tag
    return render_template('about.html', title="About KitchenHub")






# Register Page
@app.route('/register/', methods=('GET', 'POST'))
def register():

    # If the request method is POST, process the form submission
    if request.method == 'POST':

        # Get the username and password from the form
        username = request.form['username']
        password = request.form['password']
        repassword = request.form['repassword']

        # Simple validation checks
        error = None
        if not username:
            error = 'Username is required!'
        elif not password or not repassword:
            error = 'Password is required!'
        elif password != repassword:
            error = 'Passwords do not match!'

        # Display appropriate flash messages
        if error is None:
            flash(category='success', message=f"The Form Was Posted Successfully! Well Done {username}")
        else:
            flash(category='danger', message=error)

      
        # Check if username already exists
        if get_user_by_username(username):
            error = 'Username already exists! Please choose a different one.'

        # If no errors, insert the new user
        if error is None:
            create_user(username, password)
            flash(category='success', message=f"Registration successful! Welcome {username}!")
            return redirect(url_for('login'))
        else:
            # Else, re-render the registration form with error messages
            flash(category='danger', message=f"Registration failed: {error}")
            return render_template('register.html', title="Register")


    # If the request method is GET, just render the registration form
    return render_template('register.html', title="Register")


# Login - THIS ALREADY EXISTS IN YOUR app.py
@app.route('/login/', methods=('GET', 'POST'))
def login():
    # If the request method is POST, process the login form
    if request.method == 'POST':
        # Get the username and password from the form
        username = request.form['username']
        password = request.form['password']

        # Simple validation checks
        error = None
        if not username:
            error = 'Username is required!'
        elif not password:
            error = 'Password is required!'
        
        # Validate user credentials
        if error is None:
            user = validate_login(username, password)
            if user is None:
                error = 'Invalid username or password!'
            else:
                session.clear()
                session['user_id'] = user['id']
                session['username'] = user['username']

        # Display appropriate flash messages
        if error is None:
            flash(category='success', message=f"Login successful! Welcome back {username}!")
            return redirect(url_for('home'))
        else:
            flash(category='danger', message=f"Login failed: {error}")
   
    # If the request method is GET, render the login form
    return render_template('login.html', title="Log In")

# =============================================================================
# SHOPPING LIST ROUTES - Fully Interactive with Database
# =============================================================================

import sqlite3
from datetime import datetime

def get_db_connection():
    """Connect to the SQLite database"""
    conn = sqlite3.connect('kitchenhub.db')
    conn.row_factory = sqlite3.Row  # This allows us to access columns by name
    return conn

def init_shoppingList_db():
    """Initialize the shopping list database table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create shopping_items table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shopping_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item TEXT NOT NULL,
            quantity TEXT,
            category TEXT,
            completed BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert some sample data if table is empty
    cursor.execute("SELECT COUNT(*) FROM shopping_items")
    if cursor.fetchone()[0] == 0:
        sample_items = [
            ('Rice', '3 cups', 'grains', False),
            ('Tomatoes', '4 pieces', 'vegetables', True),
            ('Onions', '2 pieces', 'vegetables', False),
            ('Chicken', '1 kg', 'meat', False),
            ('Olive Oil', '1 bottle', 'other', True)
        ]
        cursor.executemany('''
            INSERT INTO shopping_items (item, quantity, category, completed)
            VALUES (?, ?, ?, ?)
        ''', sample_items)
    
    conn.commit()
    conn.close()

# Initialize the database when app starts
init_shoppingList_db()

@app.route('/shopping/')
def shopping():
    # Check if user is NOT logged in
    if 'user_id' not in session:
        flash('Please login to access your shopping list', 'warning')
        return redirect(url_for('login'))
    
    # Rest of your shopping list code...
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM shopping_items ORDER BY completed ASC, created_at DESC').fetchall()
    
    # Calculate live statistics - USING PYTHON!
    total_items = len(items)  # NUMBER - total count
    
    # Using LIST COMPREHENSION and BOOLEAN check
    completed_items = len([item for item in items if item['completed']])  # Count completed items
    
    remaining_items = total_items - completed_items  # NUMBER calculation
    
    # Calculate progress percentage
    if total_items > 0:
        progress_percentage = (completed_items / total_items) * 100  # MATH operation
        progress_percentage = round(progress_percentage)  # NUMBER rounding
    else:
        progress_percentage = 0
    
    conn.close()
    
    # USING F-STRING for logging
    print(f"Shopping List: {completed_items}/{total_items} completed ({progress_percentage}%)")
    
    return render_template(
        'shoppingList.html',
        title="Shopping List",
        items=items,
        total_items=total_items,
        completed_items=completed_items,
        remaining_items=remaining_items,
        progress_percentage=progress_percentage
    )

@app.route('/shopping/add', methods=['POST'])
def add_shopping_item():
    """
    Add new item to shopping list - handles form submission
    """
    # Get form data - these are STRINGS from the form
    item_name = request.form.get('item_name')
    item_quantity = request.form.get('item_quantity', '1 item')  # Default value
    item_category = request.form.get('item_category', 'other')   # Default value
    
    # Validate input - STRING validation
    if not item_name or not item_name.strip():
        flash('Item name is required!', 'danger')
        return redirect(url_for('shopping'))
    
    # Clean the input
    item_name = item_name.strip()
    
    conn = get_db_connection()
    
    # INSERT into database - using SQL with user input
    conn.execute('''
        INSERT INTO shopping_items (item, quantity, category, completed)
        VALUES (?, ?, ?, ?)
    ''', (item_name, item_quantity, item_category, False))  # BOOLEAN value False
    
    conn.commit()
    conn.close()
    
    # USING F-STRING for success message
    flash(f'✅ "{item_name}" added to shopping list!', 'success')
    
    return redirect(url_for('shopping'))

@app.route('/shopping/update/<int:item_id>', methods=['POST'])
def update_shopping_item(item_id):
    """
    Toggle item completion status - mark as complete/incomplete
    """
    conn = get_db_connection()
    
    # First get the current item to know its name for the flash message
    item = conn.execute('SELECT * FROM shopping_items WHERE id = ?', (item_id,)).fetchone()
    
    if item:
        # TOGGLE the boolean value - if True becomes False, if False becomes True
        new_status = not item['completed']  # BOOLEAN operation
        
        # UPDATE the database
        conn.execute('''
            UPDATE shopping_items 
            SET completed = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (new_status, item_id))
        
        conn.commit()
        
        # USING F-STRING for status message
        status_text = "completed" if new_status else "marked as todo"
        flash(f'🔄 "{item["item"]}" {status_text}!', 'info')
    else:
        flash('Item not found!', 'danger')
    
    conn.close()
    return redirect(url_for('shopping'))

@app.route('/shopping/edit/<int:item_id>', methods=['POST'])
def edit_shopping_item(item_id):
    """
    Edit an existing shopping item
    """
    # Get form data - STRINGS from form
    new_name = request.form.get('item_name')
    new_quantity = request.form.get('item_quantity')
    new_category = request.form.get('item_category')
    
    # Validate input
    if not new_name or not new_name.strip():
        flash('Item name is required!', 'danger')
        return redirect(url_for('shopping'))
    
    new_name = new_name.strip()
    
    conn = get_db_connection()
    
    # Get old item data for the flash message
    old_item = conn.execute('SELECT * FROM shopping_items WHERE id = ?', (item_id,)).fetchone()
    
    if old_item:
        # UPDATE the item in database
        conn.execute('''
            UPDATE shopping_items 
            SET item = ?, quantity = ?, category = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (new_name, new_quantity, new_category, item_id))
        
        conn.commit()
        
        # USING F-STRING for edit message
        flash(f'✏️ Updated "{old_item["item"]}" to "{new_name}"!', 'info')
    else:
        flash('Item not found!', 'danger')
    
    conn.close()
    return redirect(url_for('shopping'))

@app.route('/shopping/delete/<int:item_id>', methods=['POST'])
def delete_shopping_item(item_id):
    """
    Delete an item from shopping list
    """
    conn = get_db_connection()
    
    # Get item name before deleting for the flash message
    item = conn.execute('SELECT * FROM shopping_items WHERE id = ?', (item_id,)).fetchone()
    
    if item:
        # DELETE from database
        conn.execute('DELETE FROM shopping_items WHERE id = ?', (item_id,))
        conn.commit()
        
        # USING F-STRING for delete message
        flash(f'🗑️ "{item["item"]}" removed from shopping list!', 'warning')
    else:
        flash('Item not found!', 'danger')
    
    conn.close()
    return redirect(url_for('shopping'))

@app.route('/shopping/complete_all', methods=['POST'])
def complete_all_items():
    """
    Mark all items as completed
    """
    conn = get_db_connection()
    
    # COUNT how many items will be updated
    total_count = conn.execute('SELECT COUNT(*) FROM shopping_items WHERE completed = ?', (False,)).fetchone()[0]
    
    if total_count > 0:
        # UPDATE all incomplete items
        conn.execute('''
            UPDATE shopping_items 
            SET completed = TRUE, updated_at = CURRENT_TIMESTAMP 
            WHERE completed = FALSE
        ''')
        conn.commit()
        
        # USING F-STRING for completion message
        flash(f'🎉 All {total_count} items marked as completed!', 'success')
    else:
        flash('All items are already completed!', 'info')
    
    conn.close()
    return redirect(url_for('shopping'))

@app.route('/shopping/clear_completed', methods=['POST'])
def clear_completed_items():
    """
    Remove all completed items from the list
    """
    conn = get_db_connection()
    
    # COUNT how many completed items will be deleted
    completed_count = conn.execute('SELECT COUNT(*) FROM shopping_items WHERE completed = ?', (True,)).fetchone()[0]
    
    if completed_count > 0:
        # DELETE all completed items
        conn.execute('DELETE FROM shopping_items WHERE completed = ?', (True,))
        conn.commit()
        
        # USING F-STRING for clear message
        flash(f'🧹 {completed_count} completed items cleared!', 'info')
    else:
        flash('No completed items to clear!', 'info')
    
    conn.close()
    return redirect(url_for('shopping'))

@app.route('/shopping/quick_add/<item_name>')
def quick_add_item(item_name):
    """
    Quick add common items (like Milk, Bread, etc.)
    """
    # Map common items to categories
    common_items = {
        'milk': ('Milk', 'dairy', '1 liter'),
        'bread': ('Bread', 'grains', '1 loaf'),
        'eggs': ('Eggs', 'dairy', '6 pieces'),
        'bananas': ('Bananas', 'fruits', '4 pieces'),
        'potatoes': ('Potatoes', 'vegetables', '5 pieces')
    }
    
    if item_name in common_items:
        item_data = common_items[item_name]
        
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO shopping_items (item, quantity, category, completed)
            VALUES (?, ?, ?, ?)
        ''', (item_data[0], item_data[2], item_data[1], False))
        conn.commit()
        conn.close()
        
        flash(f'⚡ {item_data[0]} added to shopping list!', 'success')
    else:
        flash('Invalid quick add item!', 'danger')
    
    return redirect(url_for('shopping'))

# =============================================================================
# RECIPES PAGE - Shows all available recipes
# =============================================================================
@app.route('/recipes/')
def recipes():
    if 'user_id' not in session:
        flash('Please login to browse recipes', 'warning')
        return redirect(url_for('login'))
    
    # This is a LIST of dictionaries - each dictionary is one recipe
    recipe_list = [
        {
            'id': 1,  # This is a NUMBER (integer) - unique ID for each recipe
            'name': 'Jollof Rice',  # This is a STRING (text)
            'description': 'The most delicious West African rice dish with rich tomato flavor',
            'prep_time': 45,  # NUMBER - how many minutes to make it
            'difficulty': 'Medium',  # STRING - Easy, Medium, or Hard
            'category': 'Main Dish',
            'image': 'https://images.unsplash.com/photo-1604329760661-e71dc83f8f26?w=800'
        },
        {
            'id': 2,
            'name': 'Pancakes',
            'description': 'Fluffy breakfast pancakes that melt in your mouth',
            'prep_time': 20,
            'difficulty': 'Easy',
            'category': 'Breakfast',
            'image': 'https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=800'
        },
        {
            'id': 3,
            'name': 'Chocolate Cake',
            'description': 'Rich and moist chocolate cake perfect for celebrations',
            'prep_time': 60,
            'difficulty': 'Hard',
            'category': 'Dessert',
            'image': 'https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=800'
        },
        {
            'id': 4,
            'name': 'Caesar Salad',
            'description': 'Fresh and crispy salad with creamy caesar dressing',
            'prep_time': 15,
            'difficulty': 'Easy',
            'category': 'Salad',
            'image': 'https://images.unsplash.com/photo-1546793665-c74683f339c1?w=800'
        },
        {
            'id': 5,
            'name': 'Spaghetti Bolognese',
            'description': 'Classic Italian pasta with hearty meat sauce',
            'prep_time': 40,
            'difficulty': 'Medium',
            'category': 'Main Dish',
            'image': 'https://images.unsplash.com/photo-1627308595229-7830a5c91f9f?w=800'
        },
        {
            'id': 6,
            'name': 'Chicken Curry',
            'description': 'Spicy and flavorful curry with tender chicken pieces',
            'prep_time': 50,
            'difficulty': 'Medium',
            'category': 'Main Dish',
            'image': 'https://images.unsplash.com/photo-1588166524941-3bf61a9c41db?w=800'
        }
    ]
    
    # Send the recipe list to the HTML page so it can display them
    # 'title' and 'recipes' are variables the HTML template can use
    return render_template('recipes.html', title="Our Recipes", recipes=recipe_list)


# =============================================================================
# SINGLE RECIPE PAGE - Shows detailed info about ONE recipe
# =============================================================================
@app.route('/recipe/<int:recipe_id>/')
def recipe(recipe_id):
    """
    This shows the FULL details of one specific recipe
    The <int:recipe_id> means we expect a NUMBER in the URL
    For example: /recipe/1/ or /recipe/5/
    """
    
    # Sample recipe data (your teammate will get this from database later)
    # This is a DICTIONARY - notice the curly braces {}
    all_recipes = {
        1: {
            'id': 1,
            'name': 'Jollof Rice',
            'description': 'The most delicious West African rice dish with rich tomato flavor',
            'prep_time': 45,
            'servings': 6,  # This is a NUMBER - how many people it feeds
            'difficulty': 'Medium',
            'category': 'Main Dish',
            'image': 'https://images.unsplash.com/photo-1604329760661-e71dc83f8f26?w=800',
            # Ingredients are stored as one big string, separated by ||
            'ingredients': '3 cups rice||4 tomatoes||2 onions||1 cup vegetable oil||2 cups chicken stock||1 tablespoon curry powder||1 teaspoon thyme||Salt and pepper to taste',
            # Instructions also separated by ||
            'instructions': 'Blend tomatoes and onions together||Heat oil in a large pot||Fry the blended mixture for 15 minutes||Add rice and stir well||Pour in the chicken stock||Add curry powder, thyme, salt and pepper||Cover and cook on low heat for 30 minutes||Stir occasionally to prevent burning||Serve hot and enjoy',
            # YouTube video ID - just the part after "watch?v=" in YouTube URL
            'youtube_id': 'jKaQ9raKnGk'  # STRING - this would be a real cooking video
        },
        2: {
            'id': 2,
            'name': 'Pancakes',
            'description': 'Fluffy breakfast pancakes that melt in your mouth',
            'prep_time': 20,
            'servings': 4,
            'difficulty': 'Easy',
            'category': 'Breakfast',
            'image': 'https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=800',
            'ingredients': '2 cups flour||2 eggs||1.5 cups milk||2 tablespoons sugar||2 teaspoons baking powder||1/4 teaspoon salt||3 tablespoons melted butter||1 teaspoon vanilla extract',
            'instructions': 'Mix flour, sugar, baking powder and salt in a bowl||In another bowl, whisk eggs, milk, butter and vanilla||Pour wet ingredients into dry ingredients||Stir until just combined (don\'t overmix)||Heat a non-stick pan over medium heat||Pour 1/4 cup batter for each pancake||Cook until bubbles form on surface||Flip and cook other side until golden||Serve with syrup and butter',
            'youtube_id': 'c13ea70V-1Q'
        },
        3: {
            'id': 3,
            'name': 'Chocolate Cake',
            'description': 'Rich and moist chocolate cake perfect for celebrations',
            'prep_time': 60,
            'servings': 8,
            'difficulty': 'Hard',
            'category': 'Dessert',
            'image': 'https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=800',
            'ingredients': '2 cups flour||2 cups sugar||3/4 cup cocoa powder||2 teaspoons baking soda||1 teaspoon salt||2 eggs||1 cup milk||1 cup vegetable oil||2 teaspoons vanilla||1 cup boiling water',
            'instructions': 'Preheat oven to 180°C||Grease and flour two 9-inch cake pans||Mix dry ingredients in large bowl||Add eggs, milk, oil and vanilla||Beat for 2 minutes||Stir in boiling water (batter will be thin)||Pour into prepared pans||Bake for 30-35 minutes||Cool for 10 minutes in pans||Remove from pans and cool completely||Frost with your favorite chocolate frosting',
            'youtube_id': 'dQw4w9WgXcQ'
        }
    }
    
    # Try to get the recipe with the ID from the URL
    # .get() returns None if the recipe doesn't exist (safer than using [])
    recipe_data = all_recipes.get(recipe_id)
    
    # Check if we found the recipe - if not, show error message
    if recipe_data:
        # Recipe exists! Show the recipe page
        return render_template('recipe.html', title=recipe_data['name'], recipe=recipe_data)
    else:
        # Recipe not found! Send user back to recipes page with a message
        flash(category='warning', message='Sorry, that recipe was not found!')
        return redirect(url_for('recipes'))


# =============================================================================
# ADD RECIPE PAGE - Form to add new recipes
# =============================================================================
@app.route('/create/', methods=('GET', 'POST'))
def create():
    """
    This page lets users add NEW recipes to our collection
    GET method = just show the form
    POST method = someone submitted the form, process the data
    """
    
    # Check if someone submitted the form (POST request)
    if request.method == 'POST':
        
        # Get all the data from the form
        # request.form is a DICTIONARY that holds all form inputs
        recipe_name = request.form['name']  # This is a STRING
        description = request.form['description']  # STRING
        prep_time = request.form['prep_time']  # This comes as STRING but should be NUMBER
        servings = request.form['servings']  # STRING that should be NUMBER
        difficulty = request.form['difficulty']  # STRING - Easy/Medium/Hard
        category = request.form['category']  # STRING - Breakfast/Lunch/etc
        ingredients = request.form['ingredients']  # STRING
        instructions = request.form['instructions']  # STRING
        image_url = request.form.get('image_url', '')  # STRING - .get() gives empty string if blank
        youtube_id = request.form.get('youtube_id', '')  # STRING
        
        # Check if required fields are filled in
        # This is a BOOLEAN check - True or False
        if not recipe_name:
            flash(category='danger', message='Recipe name is required!')
            return render_template('create.html', title="Add New Recipe")
        
    
        # Show a success message
        flash(category='success', message=f'Recipe "{recipe_name}" added successfully! (Database integration coming soon)')
        
        # Redirect user to recipes page to see all recipes
        return redirect(url_for('recipes'))
    
    # If GET request (not POST), just show the empty form
    return render_template('create.html', title="Add New Recipe")


# =============================================================================
# CONTACT PAGE - Form to send messages
# =============================================================================
@app.route('/contact/', methods=('GET', 'POST'))
def contact():
    """
    This is the contact page where people can send us messages
    GET = show the form
    POST = process the submitted message
    """
    
    # Check if form was submitted
    if request.method == 'POST':
        
        # Get form data - these are all STRINGS
        name = request.form['name']
        email = request.form['email']
        subject = request.form['subject']
        message = request.form['message']
        
        # Validate that all fields are filled
        # We use 'and' operator to check multiple conditions
        if not name or not email or not subject or not message:
            flash(category='danger', message='All fields are required!')
            return render_template('contact.html', title="Contact Us")
    
        # For now, just show success message
        # Using f-string to insert the name into the message
        flash(category='success', message=f'Thanks {name}! Your message has been sent. We will reply to {email} soon!')
        return redirect(url_for('contact'))
    
    # GET request - show the contact form
    return render_template('contact.html', title="Contact Us")


# =============================================================================
# SHOPPING LIST PAGE
# =============================================================================
@app.route('/shoppingList/')
def shoppingList():
    """
    This shows the shopping list page
    Users can see items they need to buy for recipes
    """
    
    # Sample shopping list data (your teammate will use real database later)
    # This is a LIST of DICTIONARIES
    shopping_items = [
        {'id': 1, 'item': 'Rice', 'quantity': '3 cups', 'completed': False},  # BOOLEAN - False means not bought yet
        {'id': 2, 'item': 'Tomatoes', 'quantity': '4 pieces', 'completed': True},  # True means already bought
        {'id': 3, 'item': 'Onions', 'quantity': '2 pieces', 'completed': False},
        {'id': 4, 'item': 'Chicken', 'quantity': '1 kg', 'completed': False},
    ]
    
    return render_template('shoppingList.html', title="Shopping List", items=shopping_items)

# Logout
@app.route('/logout/')
def logout():
    # Clear the session and redirect to the index page with a flash message
    session.clear()
    flash(category='info', message='You have been logged out.')
    return redirect(url_for('home'))


# Run application
#=========================================================
# This code executes when the script is run directly.
if __name__ == '__main__':
    print("Starting Flask application...")
    print("Open Your Application in Your Browser: http://localhost:81")
    # The app will run on port 81, accessible from any local IP address
    app.run(host='0.0.0.0', port=81, debug=True)