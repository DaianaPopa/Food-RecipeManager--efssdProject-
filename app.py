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
siteName = "Food Nation"
# Set the site name in the app context
@app.context_processor
def inject_site_name():
    return dict(siteName=siteName)


# Routes
#===================
# These define which template is loaded, or action is taken, depending on the URL requested
#===================


# Home Page
@app.route('/')
def home():
    # This defines a variable 'userName' that will be passed to the output HTML
    userName = "Guest"
    #Render HTML with the dynamic name
    return render_template('home.html', title="Welcome", username=userName)


# About Page
@app.route('/about/')
def about():
    # Render HTML with the name in a H1 tag
    return render_template('about.html', title="About Food Nation")



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


# Login
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


       # user = Users.query.filter_by(username=username).first()

        # Display appropriate flash messages
        if error is None:
            flash(category='success', message=f"Login successful! Welcome back {username}!")
            return redirect(url_for('home'))
        else:
            flash(category='danger', message=f"Login failed: {error}")
   
    # If the request method is GET, render the login form
    return render_template('login.html', title="Log In")


# Logout
@app.route('/logout/')
def logout():
    # Clear the session and redirect to the index page with a flash message
    session.clear()
    flash(category='info', message='You have been logged out.')
    return redirect(url_for('home'))


@app.route('/shoppingList')
def shoppingList():
    return render_template("shoppingList.html")

# Recipes Page
@app.route('/recipes/')
def recipes():
    return render_template('recipes.html', title="Recipes")

# Recipe page
@app.route('/recipe/<int:id>/')
def recipe(id):
    return render_template('recipe.html', title="Recipe Details")

# # Films List Page
# @app.route('/films/')
# def films():

#     # Get films list data
#     film_list = get_all_films()  

#     # Render the films.html template with a list of films
#     return render_template('films.html', title="All Films", films=film_list)

# # Film Detail Page
# @app.route('/film/<int:id>/')
# def film(id):
    
#     # Get film data
#     film_data = get_film_by_id(id)  

#     if film_data:
#         return render_template('film.html', title=film_data['title'], film=film_data)
#     else:
#         # If film not found, redirect to films list with a flash message
#         flash(category='warning', message='Requested film not found!')
#         return redirect(url_for('films'))

# # Add A Film Page
# @app.route('/create/', methods=('GET', 'POST'))
# def create():

#     # If the request method is POST, process the form submission
#     if request.method == 'POST':

#         # Get the title input from the form
#         title = request.form['title']

#         # Validate the input
#         if not title:
#             flash(category='danger', message='Title is required!')
#             return render_template('create.html')

#         # [TO-DO]: Add real creation logic here (e.g. save to database record)
#         new_film = {
#             'user': 1,  # test user
#             'title': title,
#             'tagline': request.form.get('tagline', ''),
#             'director': request.form.get('director', ''),
#             'poster': request.form.get('poster', ''),
#             'release_year': request.form.get('release_year', 0),
#             'genre': request.form.get('genre', ''),
#             'watched': 'watched' in request.form,
#             'rating': request.form.get('rating', 0),
#             'review': request.form.get('review', '')
#         }
#         create_film(new_film)
#         # ===========================

#         # Flash a success message
#         flash(category='success', message='Created successfully!')
#         return redirect(url_for('films'))
    
#     return render_template('create.html', title="Add A New Film")


# # Edit A Film Page
# @app.route('/update/<int:id>/', methods=('GET', 'POST'))
# def update(id):
#     # Get film data
#     film_data = get_film_by_id(id)
#     if not film_data:
#         flash('Film not found!', 'warning')
#         return redirect(url_for('films'))

#     # If the request method is POST, process the form submission
#     if request.method == 'POST':

#         # Get the title input from the form
#         title = request.form['title']

#         # Validate the input
#         if not title:
#             flash(category='danger', message='Title is required!')
#             return render_template('update.html', id=id)
        
#         # [TO-DO]: Add real update logic here (e.g. update database record)
#         updated_fields = {
#             'title': title,
#             'tagline': request.form.get('tagline', ''),
#             'director': request.form.get('director', ''),
#             'poster': request.form.get('poster', ''),
#             'release_year': request.form.get('release_year', 0),
#             'genre': request.form.get('genre', ''),
#             'watched': 'watched' in request.form,
#             'rating': request.form.get('rating', 0),
#             'review': request.form.get('review', '')
#         }

#         update_film(id, updated_fields)
#         # ===========================

#         # Flash a success message
#         flash(category='success', message='Updated successfully!')
#         return redirect(url_for('film', id=id))

#     return render_template('update.html', title="Update Film", film=film_data)

# # Delete A Film
# @app.route('/delete/<int:id>', methods=('POST',))
# def delete(id):

#     # [TO-DO]: Add real deletion logic here (e.g. delete database record)
#     delete_film(id)
#     # ===========================

#     # Flash a success message and redirect to the index page
#     flash(category='success', message='Film deleted successfully!')
#     return redirect(url_for('films'))


# Run application
#=========================================================
# This code executes when the script is run directly.
if __name__ == '__main__':
    print("Starting Flask application...")
    print("Open Your Application in Your Browser: http://localhost:81")
    # The app will run on port 81, accessible from any local IP address
    app.run(host='0.0.0.0', port=81, debug=True)
