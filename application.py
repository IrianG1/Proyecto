import os
import requests
from flask import Flask, session, render_template, redirect,request , jsonify, flash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from functools import wraps
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from werkzeug.security import check_password_hash, generate_password_hash


app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
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


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
def index():
    return render_template("register.html")


@app.route("/login", methods=["POST"])
def login():
    session.clear()
    if request.method == "POST":
        username = request.form.get("email").strip()
        password = request.form.get("password").strip()

        # verificamos si el usuario nuevo ingreso en algo en los campos correspondientes
        if not username:
            flash('El email no ha sido escrito')
            return redirect("/")

        elif not password:
            flash('La password no ha sido escrito')
            return redirect("/")

        # Query database for username
        rows = text("SELECT * FROM users WHERE email = :email")
        rows = db.execute(rows, {"email": username}).fetchone()
   
        print(f"{len(rows)}")

        # Ensure username exists and password is correct
        if not check_password_hash(rows[3], request.form.get("password")):
            flash('Invalida Contraseña')
            return redirect("/")

        # Remember which user has logged in
        session["user_id"] = rows[0]
        session["name"] = rows[1]
        return redirect("/home")


@app.route("/register", methods=["POST"])
def register():

    if request.method == "POST":       
        email = request.form.get("email")
        password = request.form.get("password")
        name = request.form.get("name")

        # verificamos si el usuario nuevo ingreso en algo en los campos correspondientes
        if not email:
            flash('Email requerido')
            return redirect("/")

        elif not password:
            flash('password requerido')
            return redirect("/")

        elif not name:
            flash('nombre requerido')
            return redirect("/")
    

        # Verificamos si el nombre del usuario esta disponible
   
        consulta = text("SELECT email FROM users WHERE email = :email")
        consulta = db.execute(consulta, {"email": email}).fetchone()
        print(consulta)
        if consulta != None:
            flash('email invalido')
            return redirect("/")
    
        # insertamos al nuevo usuario
        consulta = text("INSERT INTO users (name, email, password) VALUES (:name, :email, :password)")
        db.execute(consulta, {"name": name, "email": email, "password":generate_password_hash(password)})
        db.commit()

        # print("XDD")
        # iniciamos session00000

        rows = text("SELECT * FROM users WHERE email = :email")
        rows = db.execute(rows, {"email": email}).fetchone()
        print(rows)
        session["user_id"] = rows[0]
        session["name"] = rows[1]
        # print("Hola1")

        
        return redirect("/home")


@app.route("/home", methods=["POST", "GET"])
@login_required
def Home():
    longitud=0
    if request.method == "POST":
        
        name = request.form.get("buscar")
        print(name)
        name = "%" + name + "%"
        buscar = text("SELECT title, author,isbn, year FROM books WHERE title LIKE :buscar or author LIKE :buscar or year LIKE :buscar LIMIT 10")
        row = db.execute(buscar, {"buscar": name})
        
        print(row)
      
        return render_template("home.html", rows=row, name=session["name"], user_id=session["user_id"])
    return render_template("home.html", name = session["name"], user_id=session["user_id"])


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/libro/<id>", methods=["POST", "GET"])
@login_required
def libro(id):
    response = requests.get("https://www.googleapis.com/books/v1/volumes?q=isbn:"+id).json()
    print(response["items"][0]["volumeInfo"]["imageLinks"]["thumbnail"])
    #return jsonify(response)
    img = response["items"][0]["volumeInfo"]["imageLinks"]["thumbnail"]
    descripcion = response["items"][0]["volumeInfo"]["description"]
    author = response["items"][0]["volumeInfo"]["authors"][0]
    title = response["items"][0]["volumeInfo"]["title"]
    print(title)
    return render_template("buscador.html", img=img, descripcion=descripcion, author=author, title=title, name=session["name"], isbn=id, user_id=session["user_id"])

@app.route('/datos', methods=['POST'])
def recibir_datos():
    datos = request.get_json()
    # Hacer algo con los datos recibidos
    print(datos)
    consulta = text("INSERT INTO review (user_id, isbn, score,comment) VALUES (:user_id, :isbn, :score,:comment)")
    db.execute(consulta, {"user_id": datos["user_id"], "isbn": datos["isbn"], 'score': 5, 'comment': datos["comentario"]})
    db.commit()
    # Realizar acciones adicionales aquí
    return "funciona"
@app.route("/libro/enviar/<id>")
def search(id):
    q = request.args.get("q")
    print(q)
    consulta = text("SELECT * FROM review INNER JOIN users ON  review.user_id=users.id where review.isbn = :isbn")
    shows = db.execute(consulta,{'isbn': id}).fetchall()
    
    # Serializar los resultados como una lista de diccionarios
    serialized_shows = []
    for show in shows:
        serialized_show = {
            'id': show.id,
            'user_id': show.user_id,
            'comment': show.comment,
            'name': show.name
            # Agrega más campos si es necesario
        }
        serialized_shows.append(serialized_show)

    return jsonify(serialized_shows)


