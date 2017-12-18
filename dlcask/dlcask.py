import drive_access
from collections import namedtuple
from flask import Flask, render_template
from apiclient import discovery
from httplib2 import Http
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)
#project_data = namedtuple('project_data', 'title digi_perc qc_perc ready_perc md_perc')

# projects = [project_data("Radzinowics", "5", "80", "15", "0"),
#             project_data("HUA Media Guides", "55", "15", "30", "10"),
#             project_data("FBCTLH", "0", "0", "100", "65")
#             ]

scopes = (
    'https://www.googleapis.com/auth/drive.metadata.readonly',
    'https://www.googleapis.com/auth/spreadsheets.readonly'
)

credentials = ServiceAccountCredentials.from_json_keyfile_name(
    '/home/mrmiguez/bin/dlcask/dlcask/secret/dlcask_service_secret.json', scopes=scopes)
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
