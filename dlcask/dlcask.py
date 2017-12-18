import os
import drive_access
from collections import namedtuple
from flask import Flask, render_template
from apiclient import discovery
from httplib2 import Http
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

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
    projects = drive_access.parse_projects(drive_service, sheet_service)
    return render_template('index.html', projects=projects)


@app.route('/<project>')
def project(project):
    return render_template('project.html', project=project)


if __name__ == '__main__':
    app.run()
