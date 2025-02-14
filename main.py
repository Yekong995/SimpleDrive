from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    send_from_directory,
    flash,
    session,
)
from werkzeug.security import safe_join
from werkzeug.utils import secure_filename
from secure import *
from rich.console import Console
from rich.traceback import install as trace_install
from rich.pretty import install as pretty_install
from signal import signal, SIGINT
import sys
import os

console = Console()
trace_install(console=console)
pretty_install(console=console)

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.urandom(24)
secure_headers = Secure.with_default_headers()

UPLOAD_FOLDER = "./file"
ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg", "gif", "zip", "7z", "rar", "xlsx", "docx", "pptx"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def handler(_signal_received, _frame):
    console.log("SIGINT or CTRL-C detected. Exiting gracefully")
    sys.exit(0)


signal(SIGINT, handler)

console.log("Collecting files")

if not os.path.exists("file"):
    os.makedirs("file")

files = []

for file in os.listdir("file"):
    if os.path.isfile(os.path.join("file", file)):
        files.append(file)

console.log(f"Found {len(files)} files. All were collected successfully")


@app.after_request
def apply_caching(response):
    secure_headers.set_headers(response)
    return response


@app.route("/", methods=["GET", "POST"])
def index():
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash("No file part", "error")
            return redirect(url_for("index"))
        file = request.files['file']
        
        # Check is user didn't select file
        if file.filename == '':
            flash("No selected file", "error")
            return (redirect(url_for('index')))
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for("index"))
        else:
            flash("File extensions unallowed", "error")
            return redirect(url_for("index"))
    
    if len(files) == 0:
        flash("No files found", "error")
        
    if session.get("isAdmin") == '1':
        has_permission = True
    else:
        has_permission = False

    return render_template("index.html", files=files, has_permission=has_permission)


@app.route("/download/<filename>")
def download(filename):
    if filename not in files:
        flash(f"File {filename} does not exist", "error")
        return redirect(url_for("index"))

    file_path = safe_join(app.root_path, "file")

    if file_path is None:
        flash("File not found", "error")
        console.log(f"File {filename} not found")
        return redirect(url_for("index"))

    return send_from_directory(directory=file_path,
                               path=filename,
                               as_attachment=True)


@app.route("/refresh")
def refresh():
    console.log("Reloading files")
    files.clear()

    for file in os.listdir("file"):
        if os.path.isfile(os.path.join("file", file)):
            files.append(file)

    console.log(f"Found {len(files)} files. All were collected successfully")
    return redirect(url_for("index"))

@app.route("/delete/<filename>")
def delete(filename):
    
    if session.get("isAdmin") == "1":
        os.remove(safe_join(UPLOAD_FOLDER, filename))
        return redirect(url_for("refresh"))
    
    return redirect(url_for("index"))

@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        uname = request.form['username']
        pwd = request.form['pass']
        
        if uname == "Yekong" and pwd == "Yk1126":
            session.setdefault("isAdmin", "1")
            
            return redirect(url_for("index"))
        else:
            flash("Username or password error")
            return render_template("login.html")

    return render_template("login.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True, processes=True)
