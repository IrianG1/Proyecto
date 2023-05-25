import os

from flask import Flask, session, render_template, redirect, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from functools import wraps
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


# Decorador de validacion de rutas
def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def index():
    return render_template("register.html")


@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email")
    password = request.form.get("password")
    print(f"{email} {password}")
    return redirect("/home")


@app.route("/register", methods=["POST"])
def register():
    email = request.form.get("email")
    password = request.form.get("password")
    name = request.form.get("name")

    consulta = text("INSERT INTO users (name, email, email) VALUES (:name, :email, :password)")
    db.execute(consulta, {"name": name, "email": email, "password": password})

    print(f"{email} {password} {name}")
    
    return redirect("/home")

@login_required
@app.route("/home", methods=["POST", "GET"])
def Home():
    longitud=0
    if request.method == "POST":
        
        name = request.form.get("buscar")
        print(name)
        name = "%" + name + "%"
        buscar = text("SELECT title, author, year FROM books WHERE title LIKE :buscar or author LIKE :buscar or year LIKE :buscar LIMIT 10")
        row = db.execute(buscar, {"buscar": name}).fetchall(as_dict=True)
        
        print(row)
        longitud = len(row)
        return render_template("home.html", rows=row, longitud=longitud)
    return render_template("home.html", longitud=longitud)

