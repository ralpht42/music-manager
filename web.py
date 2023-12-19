from flask import Flask, render_template, request

from database import init_database, signup_user, login_user

app = Flask(__name__, template_folder="web", static_folder="web/static")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")

        # TODO: Daten validieren (Passwortregeln, E-Mail-Adresse, ...)
        try:
            signup_user(email, password)
        except Exception as e:
            return render_template("signup.html", error=str(e))

        return render_template("signin.html", error=None)
    elif request.method == "GET":
        return render_template("signup.html", error=None)


@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # TODO: Daten validieren (Passwortregeln, E-Mail-Adresse, ...)
        try:
            login_user(email, password)
        except Exception as e:
            return render_template("signin.html", error=str(e))
        return render_template("index.html", error=None)
    elif request.method == "GET":
        return render_template("signin.html", error=None)


if __name__ == "__main__":
    init_database()
    app.run(debug=True)
