from flask import Flask, render_template, url_for, request, flash, redirect, session
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf

# Import DB logic
from db.db import (
    create_user, validate_login, get_user_by_username,
    get_all_recipes, get_recipe_by_id,
    create_recipe, update_recipe, delete_recipe,
    get_recipe_ingredients, update_recipe_ingredients, delete_recipe_ingredients
)

app = Flask(__name__)
app.secret_key = 'your_secret_key'
csrf = CSRFProtect(app)


# CONTEXT PROCESSORS
@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf())

@app.context_processor
def inject_site_name():
    return dict(siteName="KitchenHub")


# BASIC PAGES
@app.route('/')
def home():
    username = session.get('username', 'Guest')
    return render_template('home.html', title="Welcome", username=username)

@app.route('/about/')
def about():
    return render_template('about.html', title="About KitchenHub")


# REGISTER
@app.route('/register/', methods=('GET', 'POST'))
def register():

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        repassword = request.form['repassword']

        error = None

        if not username:
            error = 'Username is required!'
        elif not password or not repassword:
            error = 'Password is required!'
        elif password != repassword:
            error = 'Passwords do not match!'
        elif get_user_by_username(username):
            error = 'Username already exists!'

        if error:
            flash(error, 'danger')
            return render_template('register.html', title="Register")

        create_user(username, password)
        flash("Registration successful!", 'success')
        return redirect(url_for('login'))

    return render_template('register.html', title="Register")


# LOGIN
@app.route('/login/', methods=('GET', 'POST'))
def login():

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        error = None

        if not username:
            error = 'Username is required!'
        elif not password:
            error = 'Password is required!'
        else:
            user = validate_login(username, password)
            if not user:
                error = 'Invalid username or password!'

        if error:
            flash(error, 'danger')
            return render_template('login.html', title="Log In")

        # Valid login → save session
        session.clear()
        session['user_id'] = user['id']
        session['username'] = user['username']

        flash("Login successful!", 'success')
        return redirect(url_for('home'))

    return render_template('login.html', title="Log In")


# LOGOUT
@app.route('/logout/')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))


# SHOPPING LIST
@app.route('/shoppingList')
def shoppingList():
    return render_template("shoppingList.html")


# RECIPES LIST  
@app.route('/recipes/')
def recipes():
    recipes_list = get_all_recipes()
    return render_template('recipes.html', title="All Recipes", recipes=recipes_list)


# RECIPE DETAIL
@app.route('/recipe/<int:id>/')
def recipe(id):
    data = get_recipe_by_id(id)

    if not data:
        flash('Requested recipe not found!', 'warning')
        return redirect(url_for('recipes'))

    recipe, ingredients, ingredient_ids = data

    return render_template(
        'recipe.html',
        title=recipe['name'],
        recipe=recipe,
        ingredients=ingredients
    )



# CREATE RECIPE  
@app.route('/create/', methods=('GET', 'POST'))
def create():

    if request.method == 'POST':

        name = request.form['name']
        description = request.form.get('description', '')

        if not name:
            flash('Recipe name is required!', 'danger')
            return render_template('create.html')

        # Create the recipe
        user_id = session.get('user_id', 1)  # Default user if not logged in
        create_recipe(name, description, user_id)

        flash('Recipe created successfully!', 'success')
        return redirect(url_for('recipes'))

    return render_template('create.html', title="Add a Recipe")



# UPDATE RECIPE  
@app.route('/update/<int:id>/', methods=('GET', 'POST'))
def update(id):

    data = get_recipe_by_id(id)
    if not data:
        flash('Recipe not found!', 'warning')
        return redirect(url_for('recipes'))

    recipe, ingredients, ingredient_ids = data

    if request.method == 'POST':

        name = request.form['name']
        desc = request.form.get('description', '')

        if not name:
            flash('Recipe name is required!', 'danger')
            return render_template('update.html', recipe=recipe, ingredients=ingredients)

        # Update recipe fields
        update_recipe(id, name, desc)

        flash('Recipe updated successfully!', 'success')
        return redirect(url_for('recipe', id=id))

    return render_template('update.html', title="Update Recipe", recipe=recipe, ingredients=ingredients)


# DELETE RECIPE 
@app.route('/delete/<int:id>', methods=('POST',))
def delete(id):

    delete_recipe_ingredients(id)
    delete_recipe(id)

    flash('Recipe deleted successfully!', 'success')
    return redirect(url_for('recipes'))


# RUN APP
if __name__ == '__main__':
    print("Starting Flask application...")
    print("Open Your Application in Your Browser: http://localhost:81")
    app.run(host='0.0.0.0', port=81, debug=True)

