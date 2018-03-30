import os
import re
import itertools
import googleapiclient
from httplib2 import Http
from secret import FOLDER_ID
from apiclient import discovery
from collections import namedtuple
from oauth2client.service_account import ServiceAccountCredentials

# Google API init
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

# namedtuple definitions
g_folder = namedtuple("g_folder", "title gid")
workbook = namedtuple("workbook", "scope dates sheets")
sheet = namedtuple("sheet", "title gid")
details = namedtuple("details", "title scope dates batches")
batch = namedtuple("batch", "num dg md")


def dg_calc(data):
    dg = 0
    for col in data['values']:
        if col[0] == 'Completed By':
            count = 0
            for item in col[1:]:
                if item:
                    count = count + 1
            dg = (count / len(col[1:])) * 100
    return dg


def md_calc(data):
    iid_list = data["values"][0]
    record_complete_data = data["values"][-2]
    iid_count = 0
    record_complete_count = 0
    for item in iid_list:
        if item:
            iid_count = iid_count + 1
    for item in record_complete_data:
        if item:
            record_complete_count = record_complete_count + 1
    return (record_complete_count / iid_count) * 100


def batch_calc(sheet_group):
    """
    calculate batch(num, dg, md)
    :param sheet_group:
    :return:
    """
    for key in sheet_group.keys():
        for batch_sheet in sheet_group[key]:
            if 'mods' in batch_sheet.title:
                md_sheet_request = sheet_service.spreadsheets().values().get(spreadsheetId=batch_sheet.gid,
                                                                             range="C1:ZZ99999",
                                                                             majorDimension="COLUMNS")
                md_sheet_response = md_sheet_request.execute()

            else:
                dg_sheet_request = sheet_service.spreadsheets().values().get(spreadsheetId=batch_sheet.gid,
                                                                             range="{0}!B1:ZZ999".format(
                                                                                 batch_sheet.title),
                                                                             majorDimension="COLUMNS",
                                                                             valueRenderOption="UNFORMATTED_VALUE")
                dg_sheet_response = dg_sheet_request.execute()

    return int(key[-1]), dg_calc(
        dg_sheet_response), md_calc(md_sheet_response)  # todo: dg_calc returns last sheet analysed, not multi


def project_list(folder_id=FOLDER_ID):
    """
    :return: list of child folders in FOLDER_ID parent
    """
    folders = drive_service.files().list(
        q="'{0}' in parents and mimeType='application/vnd.google-apps.folder'".format(folder_id)).execute(
    ).get('files', [])
    # curr_proj = [g_folder(f['name'], f['id']) for f in folders if 'Z_' not in f['name']]
    # curr_proj = curr_proj.sort()
    # arch = curr_proj.pop(-1)
    # return arch, curr_proj
    return [g_folder(f['name'], f['id']) for f in folders if 'Z_' not in f['name']]

def project_detail(parent_title, parent_gid):
    """
    :param parent_title:
    :param parent_gid:
    :return:
    """
    # build workbook(scope, dates, [sheet(title, gid)])
    wb_book, mods_books = sheet_ids(parent_gid)
    book_request = sheet_service.spreadsheets().values().get(spreadsheetId=wb_book.gid, range="A1:C99999",
                                                             majorDimension="ROWS").execute()
    sheet_request = sheet_service.spreadsheets().get(spreadsheetId=wb_book.gid).execute()
    project_workbook = workbook(book_request['values'][0][0],
                                book_request['values'][3:],
                                [sheet(wb_sheet['properties']['title'], wb_book.gid)
                                 for wb_sheet in sheet_request['sheets'][1:]]
                                )

    # match together MODS & digi batches by title
    sheet_groups = [{k: list(v)} for k, v in
                    itertools.groupby(project_workbook.sheets, key=lambda sheet: sheet.title.split('_')[0])]
    batches = []
    # iter spreadsheet batches to calculate completion percentages
    for p_batch in sheet_groups:
        for k in p_batch.keys():
            p_batch[k] = p_batch[k] + [mods_book for mods_book in mods_books if k.lower() in mods_book.title.lower()]
        batches = batches + [batch_calc(p_batch)]

    # build & return details(title, scope, dates, batches)
    project_details = details(parent_title, project_workbook.scope, project_workbook.dates,
                              [batch(num, dg, md) for num, dg, md in batches])
    return project_details


def sheet_ids(parent_gid):
    """
    :param parent_gid:
    :return:
    """
    workbook = re.compile("WorkBook|workbook|Workbook")
    mods = re.compile("^mods")
    request = drive_service.files().list(
        q="'{0}' in parents and mimeType='application/vnd.google-apps.spreadsheet'".format(
            parent_gid))
    response = request.execute()
    files = response.get('files', [])
    mods_ids = []
    for f in files:
        if workbook.search(f['name']):
            wkbk_id = sheet(f['name'], f['id'])
        if mods.search(f['name']):
            mods_ids.append(sheet(f['name'], f['id']))
    return wkbk_id, mods_ids
