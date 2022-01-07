from flask import Flask, render_template, abort, flash, request, redirect, url_for, jsonify, g
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from passlib.hash import argon2
from functools import wraps
import sqlite3
import queries
import config
from objects import Role

app = Flask(__name__, template_folder="template", static_folder="static")
app.config.from_object('config.Config')

login_manager = LoginManager(app)

# Set up database
def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config["SQLITE_DATABASE_PATH"])
        db.row_factory = make_dicts
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# Admin utils
def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if current_user.role == Role.admin:
            return f(*args, **kwargs)
        else:
            return login_manager.unauthorized()

    return login_required(wrapper)


@app.template_filter("is_admin")
def is_admin(role: int) -> bool:
    return role == Role.admin.value


@app.template_filter("role_name")
def role_node(role: int) -> str:
    return Role(role).name


class User(UserMixin):
    def __init__(self, username, role, password_hash):
        self.username = username
        self.role = role
        self.password_hash = password_hash

    def get_id(self):
        return self.username

    @classmethod
    def get(cls, username):
        cursor = get_db().cursor()
        cursor.execute("SELECT username, role, password_hash FROM user WHERE username=?", [username])
        user = cursor.fetchone()

        if user is not None:
            user = cls(**user)
        return user

    @classmethod
    def create(cls, username, password, role):
        password_hash = argon2.hash(password)

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO user (username, role, password_hash) VALUES (?, ?, ?)",
            (
                username,
                role,
                password_hash
            )
        )
        conn.commit()

        return cls(username, role, password_hash)

    @classmethod
    def verify_and_get(cls, username, password):
        usr = User.get(username)
        if usr is None:
            return None

        # verify that password
        return usr if argon2.verify(password, usr.password_hash) else None


@app.route("/")
def index():
    return redirect(get_user_home())


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            flash("Please enter a username and password.")
            return render_template("login.html")

        usr = User.verify_and_get(username, password)
        if usr is None:
            flash("That username/password combination does not exist.")
            return render_template("login.html")

        login_user(usr)
        return redirect(get_user_home())

    return render_template("login.html")


@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        role = request.form.get("role")

        if not username or not password or not role:
            flash("Please enter a value in all fields.")
            return render_template("signup.html")

        usr = User.get(username)
        if usr is not None:
            flash("That username is not available.")
            return render_template("signup.html")

        usr = User.create(username, password, role)
        login_user(usr)
        return redirect(get_user_home())

    return render_template("signup.html")

@app.route("/dashboard")
@admin_required
def dashboard():
    tickets = queries.get_user_tickets(
        get_db(),
        current_user.username
    )
    user_tickets, unassigned_tickets = [], []
    for ticket in tickets:
        if ticket["assignee"] is None:
            unassigned_tickets.append(ticket)
        else:
            user_tickets.append(ticket)

    return render_template(
        "admin_dashboard.html",
        user=current_user,
        user_tickets=user_tickets,
        unassigned_tickets=unassigned_tickets
    )


@app.route("/tickets")
@app.route("/tickets/")
@admin_required
def all_tickets():
    tickets = queries.get_all_tickets(get_db())
    return render_template(
        "tickets.html",
        user=current_user,
        tickets=tickets
    )


@app.route("/tickets/<int:ticket_id>")
@app.route("/tickets/<int:ticket_id>/")
@admin_required
def view_ticket(ticket_id):
    ticket = queries.get_ticket_detail(get_db(), ticket_id)

    if ticket is None:  # no ticket with that ID was found.
        abort(404)

    #if ticket["assignee"] is not None and ticket["assignee"] != current_user.username:
    #    abort(403)  # forbidden

    return render_template("ticket_view.html", user=current_user, ticket=ticket, ticket_creator_role_name = Role(ticket["creator_role"]).name)


@app.route("/create_issue", methods=["GET", "POST"])
@login_required
def create_issue():
    if request.method == "POST":
        summary = request.form.get("summary")
        description = request.form.get("description")

        if not summary or not description:
            flash("Please provide both a description and summary")
            return render_template("issue_submit.html", user=current_user)

        try:
            id = queries.insert_issue(
                get_db(),
                summary,
                description,
                current_user.username
            )

            flash(f"Issue #{id} Submitted")
        except sqlite3.DataError as ex:
            if ex.args[0] == 1406:  # data too long for column
                if len(summary) > config.Constants.TICKET_SUMMARY_MAX_LENGTH:
                    flash(f"Summary can be no longer than {config.Constants.TICKET_SUMMARY_MAX_LENGTH} characters")
                elif len(description) > config.Constants.TICKET_DESC_MAX_LENGTH:
                    flash(f"Description can be no longer than {config.Constants.TICKET_DESC_MAX_LENGTH} characters")
                else:
                    flash(f"Summary can be no longer than {config.Constants.TICKET_SUMMARY_MAX_LENGTH} characters and Description can be no longer than {config.Constants.TICKET_DESC_MAX_LENGTH} characters")
            else:
                print(f"An error occurred: {ex.args}")
                flash("An unknown error has occurred")
        except Exception as ex:
            print(f"An error occurred: {ex.args}")
            flash("An unknown error has occurred")

    return render_template("issue_submit.html", user=current_user)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


@app.errorhandler(401)
def unauthorized(e):
    return redirect(get_user_home())


def get_user_home():
    if current_user.is_authenticated:
        if current_user.role == Role.admin:
            return url_for("dashboard")
        else:
            return url_for("create_issue")
    return url_for("login")


# JS API
@app.route("/api/admins.json")
@admin_required
def admins():
    return jsonify(queries.get_all_admins(get_db()))


@app.route("/api/categories.json")
@admin_required
def categories():
    return jsonify(queries.get_all_categories(get_db()))


@app.route("/tickets/<int:ticket_id>/category", methods=["PUT"])
@admin_required
def set_category(ticket_id):
    category_id = request.get_data(as_text=True)
    if category_id == "null":
        category_id = None

    try:
        queries.set_ticket_category(get_db(), ticket_id, category_id)
    except (sqlite3.DataError, sqlite3.IntegrityError, sqlite3.InternalError):
        abort(400)  # invalid category id

    return get_category(ticket_id)


@app.route("/tickets/<int:ticket_id>/category", methods=["GET"])
@admin_required
def get_category(ticket_id):
    data = queries.get_ticket_category(get_db(), ticket_id)
    if data is None:
        abort(404)

    return jsonify(data)


@app.route("/tickets/<int:ticket_id>/assignee", methods=["PUT"])
@admin_required
def set_assignee(ticket_id):
    assignee = request.get_data(as_text=True)
    if not assignee:
        assignee = None

    try:
        queries.set_ticket_assignee(get_db(), ticket_id, assignee)
    except (sqlite3.DataError, sqlite3.IntegrityError, sqlite3.InternalError):
        abort(400)  # invalid assignee

    return get_assignee(ticket_id)


@app.route("/tickets/<int:ticket_id>/assignee", methods=["GET"])
@admin_required
def get_assignee(ticket_id):
    data = queries.get_ticket_assignee(get_db(), ticket_id)
    if data is None:
        abort(404)

    return jsonify(data)


@app.route("/tickets/<int:ticket_id>/close", methods=["POST"])
@admin_required
def close_ticket(ticket_id):
    try:
        queries.delete_ticket(get_db(), ticket_id)
    except sqlite3.DataError as ex:
        abort(500)  # something has gone wrong here

    return jsonify({})


if __name__ == "__main__":
    import os
    if not os.path.isfile(config.Config.SQLITE_DATABASE_PATH):
        # Initialise database
        import schema
        schema.init_db()

    app.run()
