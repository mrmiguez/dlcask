import re
import googleapiclient
from collections import namedtuple
from secret import FOLDER_ID

simple_project = namedtuple('simple_project', 'title batch_data')
#complex_project = namedtuple('complex_project', 'title batch_nums data_batch_list')
project_ids = namedtuple('project_ids', 'title gid wkbk_gid md_gid')
project_data = namedtuple('project_data', 'digi_perc qc_perc ready_perc md_perc')


# get DLC Project Folders
def get_projects(drive_service):
    files = drive_service.files().list(
            q="'{0}' in parents and mimeType='application/vnd.google-apps.folder'".format(FOLDER_ID)).execute(
            ).get('files', [])
    return [project_ids(f['name'], f['id'], sheet_ids(drive_service, f['id'])[0], sheet_ids(drive_service, f['id'])[1])
            for f in files]


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
        if mods.search(f['name']):
            mods_ids.append(f['id'])
    return wkbk_ids, mods_ids


def parse_projects(drive_service, sheet_service):
    projects = []
    project_query = get_projects(drive_service)
    for project in project_query:
        if len(project.md_gid) < 2:
            try:
                perc1, perc2, perc3, perc4 = data_stats(sheet_service, project.md_gid[0])
                projects.append(simple_project(project.title,
                                           [project_data(perc1, perc2, perc3, perc4)]))
            except IndexError:
                pass
        else:
            data_list = []
            for gid in project.md_gid:
                perc1, perc2, perc3, perc4 = data_stats(sheet_service, gid)
                data_list.append(project_data(perc1, perc2, perc3, perc4))
            projects.append(simple_project(project.title, data_list))
    return projects


def data_stats(sheet_service, md_gid):
    return (17, 35, 48, md_perc(sheet_service, md_gid))



# def parse_projects(drive_service, sheet_service):
#     return [project_data(project.name,
#                          "15",
#                          "20",
#                          "25",
#                          md_perc(sheet_service, project.md_gid))
#             for project in project_folders(drive_service)]


def md_perc(sheet_service, sheet_id):
    request = sheet_service.spreadsheets().values().get(spreadsheetId=sheet_id, range="A1:ZZ99999", majorDimension="COLUMNS")
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
    return (record_complete_count / iid_count) * 100

