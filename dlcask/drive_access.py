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
batch = namedtuple("batch", "dg qc md")


def project_list():
    """
    :param drive_service: Drive API connection
    :return: list of child folders in FOLDER_ID parent
    """
    folders = drive_service.files().list(
            q="'{0}' in parents and mimeType='application/vnd.google-apps.folder'".format(FOLDER_ID)).execute(
            ).get('files', [])
    return [g_folder(f['name'], f['id']) for f in folders]


def project_detail(parent_gid):
    """

    :param sheet_service:
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
                                [sheet(wb_sheet['properties']['title'], wb_sheet['properties']['sheetId'])
                                 for wb_sheet in sheet_request['sheets'][1:]]
                               )
    # return project_workbook  # test
    sheet_groups = [{ k: list(v) } for k, v in
                    itertools.groupby(project_workbook.sheets, key=lambda sheet: sheet.title.split('_')[0])]
    # todo: match together MODS & digi batches and calculate batch(dg, qc, md)
    # todo: build & return details(title, scope, dates, batches)


def sheet_ids(parent_gid):
    """

    :param drive_service:
    :param parent_gid:
    :return:
    """
    workbook = re.compile("WorkBook|workbook|Workbook")
    mods = re.compile("^mods")
    request = drive_service.files().list(q="'{0}' in parents and mimeType='application/vnd.google-apps.spreadsheet'".format(
            parent_gid))
    response = request.execute()
    files = response.get('files', [])
    mods_ids = []
    for f in files:
        if workbook.search(f['name']):
            wkbk_id = sheet(f['name'], f['id'])
        if mods.search(f['name']):
            mods_ids.append(sheet(f['name'],f['id']))
    return wkbk_id, mods_ids
