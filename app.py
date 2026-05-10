from flask import Flask, render_template, request, redirect, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required
from flask_socketio import SocketIO
from models import db, User, Task
import pandas as pd

app = Flask(__name__)

app.config.from_pyfile("config.py")

db.init_app(app)

socketio = SocketIO(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
@login_required
def home():

    tasks = Task.query.all()

    data = []

    for task in tasks:
        data.append({
            "title": task.title,
            "status": task.status
        })

    df = pd.DataFrame(data)

    total_tasks = len(df)

    completed_tasks = len(
        df[df["status"] == "Completed"]
    ) if not df.empty else 0

    pending_tasks = total_tasks - completed_tasks

    completion_percentage = (
        (completed_tasks / total_tasks) * 100
        if total_tasks > 0 else 0
    )

    return render_template(
        "index.html",
        tasks=tasks,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        completion_percentage=completion_percentage
    )

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]

        password = request.form["password"]

        user = User(
            username=username,
            password=password
        )

        db.session.add(user)

        db.session.commit()

        return redirect("/login")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]

        password = request.form["password"]

        user = User.query.filter_by(
            username=username,
            password=password
        ).first()

        if user:
            login_user(user)

            return redirect("/")

    return render_template("login.html")

@app.route("/logout")
def logout():

    logout_user()

    return redirect("/login")

@app.route("/add_task", methods=["POST"])
@login_required
def add_task():

    title = request.form["title"]

    description = request.form["description"]

    priority = request.form["priority"]

    status = request.form["status"]

    task = Task(
        title=title,
        description=description,
        priority=priority,
        status=status
    )

    db.session.add(task)

    db.session.commit()

    socketio.emit(
        "task_update",
        {"message": "New Task Added"}
    )

    return redirect("/")

@app.route("/delete_task/<int:id>")
@login_required
def delete_task(id):

    task = Task.query.get(id)

    db.session.delete(task)

    db.session.commit()

    return redirect("/")
@app.route("/api/tasks", methods=["GET"])
def get_tasks():

    tasks = Task.query.all()

    task_list = []

    for task in tasks:

        task_list.append({
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "priority": task.priority,
            "status": task.status
        })

    return jsonify(task_list)

@app.route("/api/tasks", methods=["POST"])
def api_add_task():

    data = request.json

    task = Task(
        title=data["title"],
        description=data["description"],
        priority=data["priority"],
        status=data["status"]
    )

    db.session.add(task)

    db.session.commit()

    return jsonify({
        "message": "Task Added Successfully"
    })

@app.route("/api/tasks/<int:id>", methods=["PUT"])
def update_task(id):

    task = Task.query.get(id)

    data = request.json

    task.title = data["title"]
    task.description = data["description"]
    task.priority = data["priority"]
    task.status = data["status"]

    db.session.commit()

    return jsonify({
        "message": "Task Updated Successfully"
    })

@app.route("/api/tasks/<int:id>", methods=["DELETE"])
def api_delete_task(id):

    task = Task.query.get(id)

    db.session.delete(task)

    db.session.commit()

    return jsonify({
        "message": "Task Deleted Successfully"
    })
@app.route("/edit_task/<int:id>", methods=["GET", "POST"])
@login_required
def edit_task(id):

    task = Task.query.get(id)

    if request.method == "POST":

        task.title = request.form["title"]

        task.description = request.form["description"]

        task.priority = request.form["priority"]

        task.status = request.form["status"]

        db.session.commit()

        return redirect("/")

    return render_template(
        "edit_task.html",
        task=task
    )

if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    socketio.run(app, debug=True)