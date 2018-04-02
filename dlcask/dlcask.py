#import os
#import sys
import drive_access
from flask import Flask, render_template, g, session
from flask_session import Session

#PATH = os.path.abspath(os.path.dirname(__file__))
#sys.path.append(os.path.join(PATH, 'secret/'))
from secret import ARCH_ID


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
            detail, err = drive_access.project_detail(project.title, project.gid)
            if detail:
                return render_template('project.html', project=detail)
            else:
                return render_template('error.html', err=err)


@app.route('/archive')
def archive():
    projects = drive_access.project_list(folder_id=ARCH_ID)
    return render_template('archive.html', projects=projects)


if __name__ == '__main__':
    app.run()
