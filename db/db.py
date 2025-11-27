import sqlite3
import os
from flask import abort
from werkzeug.security import generate_password_hash, check_password_hash

__all__ = [
    "create_user",
    "validate_login",
    "get_user_by_username",
    "get_user_by_id",
    "get_all_recipes",
    "get_recipe_by_id",
    "create_recipe",
    "update_recipe",
    "delete_recipe",
    "get_recipe_ingredients",
    "get_all_ingredients",
    "update_recipe_ingredients",
    "delete_recipe_ingredients"
]

# DB CONNECTION
def get_db_connection():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, "database.db")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# USERS
def create_user(username, password):
    hashed = generate_password_hash(password)
    conn = get_db_connection()
    conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
    conn.commit()
    conn.close()

def get_user_by_username(username):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return user

def validate_login(username, password):
    user = get_user_by_username(username)
    if user and check_password_hash(user["password"], password):
        return user
    return None

def get_user_by_id(user_id):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    if user is None:
        abort(404)
    return user


# RECIPES
def get_all_recipes(limit=None, order_by="name ASC"):
    conn = get_db_connection()
    query = f"SELECT * FROM recipes ORDER BY {order_by}"

    if limit:
        query += f" LIMIT {limit}"

    recipes = conn.execute(query).fetchall()
    conn.close()
    return recipes


def get_recipe_by_id(recipe_id):
    conn = get_db_connection()
    recipe = conn.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,)).fetchone()
    conn.close()

    if not recipe:
        return None

    ingredients, ingredient_ids = get_recipe_ingredients(recipe_id)
    return recipe, ingredients, ingredient_ids


def create_recipe(name, description, user_id):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO recipes (name, description, user_id) VALUES (?, ?, ?)",
        (name, description, user_id)
    )
    conn.commit()
    conn.close()


def update_recipe(recipe_id, name, description):
    conn = get_db_connection()
    conn.execute(
        "UPDATE recipes SET name=?, description=? WHERE id=?",
        (name, description, recipe_id)
    )
    conn.commit()
    conn.close()


def delete_recipe(recipe_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM recipes WHERE id=?", (recipe_id,))
    conn.commit()
    conn.close()



# INGREDIENTS
def get_recipe_ingredients(recipe_id):
    conn = get_db_connection()

    rows = conn.execute("""
        SELECT ingredients.* FROM ingredients
        JOIN recipe_ingredients 
        ON ingredients.id = recipe_ingredients.ingredient_id
        WHERE recipe_ingredients.recipe_id = ?""", (recipe_id,)).fetchall()

    # Ingredient IDs
    ids = [row["id"] for row in rows]

    conn.close()
    return rows, ids


def get_all_ingredients():
    conn = get_db_connection()
    ingredients = conn.execute("SELECT * FROM ingredients").fetchall()
    conn.close()
    return ingredients


def update_recipe_ingredients(recipe_id, ingredients):
    conn = get_db_connection()

    # Clear old ingredients
    conn.execute("DELETE FROM ingredients WHERE recipe_id = ?", (recipe_id,))

    # Insert new ingredients
    for ing in ingredients:
        conn.execute(
            "INSERT INTO ingredients (recipe_id, name, amount) VALUES (?, ?, ?)",
            (recipe_id, ing["name"], ing["amount"])
        )

    conn.commit()
    conn.close()


def delete_recipe_ingredients(recipe_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM ingredients WHERE recipe_id=?", (recipe_id,))
    conn.commit()
    conn.close()
