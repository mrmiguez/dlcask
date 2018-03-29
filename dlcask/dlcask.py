import drive_access
from flask import Flask, render_template, g, session
from flask_session import Session


app = Flask(__name__)
# app.secret_key = os.urandom(24)

# Session extension config
SESSION_TYPE = 'filesystem'
SESSION_FILE_DIR = 'secret/'
SESSION_PERMANENT = True
SESSION_FILE_THRESHOLD = 50
app.config.from_object(__name__)
Session(app)


@app.route('/')
def index():
    session['s'] = drive_access.project_list()
    return render_template('index.html', projects=session['s'])


@app.route('/<title>')
def project(title):
    for project in session['s']:
        if project.title == title:
            detail = drive_access.project_detail(project.title, project.gid)
            return render_template('project.html', project=detail)


if __name__ == '__main__':
    app.run()
