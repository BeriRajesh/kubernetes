from datadog_helper import DatadogHelper
import json
import os
import sys

os.chdir(os.path.realpath(os.path.dirname(__file__)))
sys.path.append('../')
import lib.helper_functions as hf

hf.verbose = 1

datadogh = DatadogHelper()

screenboard_modified_path = 'screenboards-modified'

screenboard_files = [f for f in os.listdir(screenboard_modified_path)]

# loop through file, update or create dashboards correspondingly
for screenboard_file in screenboard_files:
    with open('{}/{}'.format(screenboard_modified_path, screenboard_file), 'r') as fp:
        screenboard = json.load(fp)

    if ('id' not in screenboard) or screenboard['id'] == "":
        sb_id = datadogh.create_screenboard(screenboard)
        continue

    print(screenboard['board_title'])
    sb_id = screenboard['id']

    # try to get the screenboard by id, if not found then create it
    if 'errors' in datadogh.get_screenboard(sb_id):
        sb_id = datadogh.create_screenboard(screenboard)
        continue

    datadogh.update_screenboard(sb_id, screenboard)

