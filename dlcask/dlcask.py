import os
import drive_access
from flask import Flask, render_template, g, session
from flask_session import Session
from apiclient import discovery
from httplib2 import Http
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)
# app.secret_key = os.urandom(24)

# Session extension config
SESSION_TYPE = 'filesystem'
SESSION_FILE_DIR = 'secret/'
SESSION_PERMANENT = True
SESSION_FILE_THRESHOLD = 50
app.config.from_object(__name__)
Session(app)

self_path = os.path.abspath(os.path.dirname(__file__))

scopes = (
    'https://www.googleapis.com/auth/drive.metadata.readonly',
    'https://www.googleapis.com/auth/spreadsheets.readonly'
)

credentials = ServiceAccountCredentials.from_json_keyfile_name(os.path.join(
    self_path, 'secret/dlcask_service_secret.json'), scopes=scopes)
http_auth = credentials.authorize(Http())
drive_service = discovery.build('drive', 'v3', http=http_auth)
sheet_service = discovery.build('sheets', 'v4', http=http_auth)


@app.route('/')
def index():
    session['s'] = drive_access.parse_projects(drive_service, sheet_service)
    return render_template('index.html', projects=session['s'])


@app.route('/<title>')
def project(title):
    for project in session['s']:
        if project.title == title:
            return render_template('project.html', project=project)


if __name__ == '__main__':
    app.run()
