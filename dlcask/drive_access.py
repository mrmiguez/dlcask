import re
import googleapiclient
from collections import namedtuple
from secret import FOLDER_ID

project_ids = namedtuple('project_ids', 'name gid wkbk_gid md_gid')
project_data = namedtuple('project_data', 'title digi_perc qc_perc ready_perc md_perc')


# get DLC Project Folders
def project_folders(drive_service):
    projects = []
    files = drive_service.files().list(
            q="'{0}' in parents and mimeType='application/vnd.google-apps.folder'".format(FOLDER_ID)).execute(
            ).get('files', [])
    for f in files:
        projects.append(project_ids(f['name'], f['id'], sheet_ids(drive_service, f['id']), sheet_ids(drive_service, f['id'])))
    return projects


# Retrieve spreadsheet ID's
def sheet_ids(drive_service, parent_gid):
    workbook = re.compile("WorkBook|workbook|Workbook")
    mods = re.compile("^mods")
    request = drive_service.files().list(q="'{0}' in parents and mimeType='application/vnd.google-apps.spreadsheet'".format(
            parent_gid))
    response = request.execute()
    files = response.get('files', [])
    mods_ids = []
    wkbk_ids = []
    for f in files:
        if workbook.search(f['name']):
            wkbk_ids.append(f['id'])
            return wkbk_ids
        if mods.search(f['name']):
            mods_ids.append(f['id'])
            return mods_ids


def parse_projects(drive_service, sheet_service):
    return [project_data(project.name,
                         "15",
                         "20",
                         "25",
                         md_perc(sheet_service, project.md_gid))
            for project in project_folders(drive_service)]


def md_perc(sheet_service, sheet_id):
    if sheet_id is not None and len(sheet_id) < 2:
        request = sheet_service.spreadsheets().values().get(spreadsheetId=sheet_id[0], range="A1:ZZ99999", majorDimension="COLUMNS")
        response = request.execute()
        iid_list = response["values"][0]
        record_complete_data = response["values"][-2]
        iid_count = 0
        record_complete_count = 0
        for item in iid_list:
            if item:
                iid_count = iid_count + 1
        for item in record_complete_data:
            if item:
                record_complete_count = record_complete_count + 1
        print(iid_list, record_complete_data)  # test line
        return (record_complete_count / iid_count) * 100
    else:
        return 0
