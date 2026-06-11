#!/home/xferuser/virtualenvs/main/bin/python

import os
import sys
import csv
import json
import time
import logging
import logging.handlers
import httplib2
import httplib
from threading import Thread
import tempfile
import subprocess
import shutil
import datetime

from apiclient.discovery import build
from oauth2client import GOOGLE_TOKEN_URI
from oauth2client.client import OAuth2Credentials
from googleapiclient.errors import HttpError

CHECK_INTERVAL = 600
HEARTBEAT_INTERVAL = 300
WORK_DIR = os.path.dirname(os.path.realpath(__file__))

# Read settings from settings.json file
try:
    with open(os.path.join(WORK_DIR, "access_config.json"), "rb") as fh:
        SETTINGS = json.load(fh).get("settings", None)
        if not SETTINGS:
            print >> sys.stderr, "Expected key settings is not found.\n"
            sys.exit(1)
except IOError as e:
    print >> sys.stderr, "Error reading access_config.json file in current directory.\n %s" % str(
        e)
    sys.exit(1)


def run_command(comms):
    """
      Runs gsutils with params
    """
    env = os.environ.copy()
    subP = subprocess.Popen(comms.split(), env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = subP.communicate()
    exitcode = subP.returncode
    pid = subP.pid
    results = {"stdout": stdout, "stderr": stderr,
               "exitcode": exitcode, "pid": pid}
    return results


def get_combine_csv(fn_list, tmp_dir, report_type, dt_range):
    fn_out = report_type + '_' + dt_range.replace('-', '') + '.txt'
    with open(os.path.join(tmp_dir, fn_out), 'a') as fout:
        writer = csv.writer(fout, delimiter='|',
                            quoting=csv.QUOTE_ALL, lineterminator="\n")
        # first file:
        #with open(fn_list[0]) as fn_first:
        #reader = csv.reader(fn_first)
        #writer.writerows(reader)
        # now the rest:
        for num in range(0, len(fn_list)):
            with open(fn_list[num]) as fn_first:
                reader = csv.reader(fn_first)
                next(reader, None)
                for row in reader:
                    xrow = [f.replace("\r\n", ", ").replace("\n", " ")
                            for f in row]
                    writer.writerow(xrow)
    return fn_out


def create_credentials(client_id, client_secret, refresh_token):
    """Create Google OAuth2 credentials.

    Args:
    client_id: Client id of a Google Cloud console project.
    client_secret: Client secret of a Google Cloud console project.
    refresh_token: A refresh token authorizing the Google Cloud console project
    to access the DS data of some Google user.

    Returns:
    OAuth2Credentials
    """
    return OAuth2Credentials(access_token=None,
                             client_id=client_id,
                             client_secret=client_secret,
                             refresh_token=refresh_token,
                             token_expiry=None,
                             token_uri=GOOGLE_TOKEN_URI,
                             user_agent=None)


def get_service(credentials):
    """Set up a new DoubleClick Search service.

    Args:
    credentials: An OAuth2Credentials generated with create_credentials, or
    flows in the oatuh2client.client package.
    Returns:
    An authorized Doubleclicksearch serivce.
    """
    # Use the authorize() function of OAuth2Credentials to apply necessary credential
    # headers to all requests.
    http = credentials.authorize(http=httplib2.Http())

    # Construct the service object for the interacting with the DoubleClick Search API.
    service = build('doubleclicksearch', 'v2', http=http)
    return service


def request_report(service, query):
    """Request sample report and print the report ID that DS returns. See Set Up Your Application.

    Args:
    service: An authorized Doublelcicksearch service.
    Returns:
    The report id.
    """
    try:
        request = service.reports().request(body=query)
        json_data = request.execute()
    except HttpError as e:
        error = json.loads(e.content)['error']
        logger.error("ERROR: execution of the query is failed!: %s" %
                     (error,), exc_info=True)
        return False
    if 'error' in json_data:
        logger.error("ERROR: the query is not valid!", exc_info=True)
        return False
    else:
        return json_data['id']


def download_files(service, report_id, report_fragment, tmp_dir, report_type):
    """Generate and print sample report.

    Args:
    service: An authorized Doublelcicksearch service.
    report_id: The ID DS has assigned to a report.
    report_fragment: The 0-based index of the file fragment from the files array.
    """

    fn_local = os.path.join(tmp_dir, report_type +
                            '-' + report_fragment + '.csv')
    request = service.reports().getFile(
        reportId=report_id, reportFragment=report_fragment)
    f = file(fn_local, 'w')
    tries = 1
    while tries < 10:
        try:
            f.write(request.execute())
            break
        except httplib.IncompleteRead as e:
            logger.error("ERROR: Incomplete read of file from Google Service Report: %s" % (
                e,), exc_info=True)
            tries += 1
            time.sleep(30)
    f.close()

    return fn_local


def poll_report(service, report_id, report_type, dt_start, dt_end):
    """Poll the API with the reportId until the report is ready, up to ten times.

    Args:
    service: An authorized Doublelcicksearch service.
    report_id: The ID DS has assigned to a report.
    """

    for _ in xrange(100):
        try:
            request = service.reports().get(reportId=report_id)
            json_data = request.execute()
            if json_data['isReportReady']:
                logger.info('The report is ready.')

                # For large reports, DS automatically fragments the report into multiple
                # files. The 'files' property in the JSON object that DS returns contains
                # the list of URLs for file fragment. To download a report, DS needs to
                # know the report ID and the index of a file fragment.
                print json_data
                tmp_dir = tempfile.mkdtemp()
                fragments_fn = []
                for i in range(len(json_data['files'])):
                    logger.info('Downloading fragment ' + str(i) +
                                ' for ' + report_type + ' report ' + report_id)
                    # See Download the report.
                    fragment = download_files(
                        service, report_id, str(i), tmp_dir, report_type)
                    fragments_fn.append(fragment)

                dt_range = dt_start + '_' + dt_end if dt_start != dt_end else dt_start
                fn_report = get_combine_csv(
                    fragments_fn, tmp_dir, report_type, dt_range)

                fn_ctrl = fn_report.split('.')[0] + '.ctl'
                with open(os.path.join(tmp_dir, fn_ctrl), 'w') as fp:
                    print >> fp, '%s|%s|%d|%d' % (fn_report, dt_range.replace(
                        '-', ''), os.stat(os.path.join(tmp_dir, fn_report)).st_size, json_data['rowCount'])
                sftp_batch = os.path.join(tmp_dir, 'sftp_batch_file')
                with open(sftp_batch, 'w') as fp:
                    print >> fp, 'put %s\nbye' % (
                        os.path.join(tmp_dir, fn_report),)
                ret = run_command('sftp -C -b %s wf-prod' % (sftp_batch,))
                #ret = run_command('scp %s localhost:/vol/data/mock-sftp/ds3/' % (os.path.join(tmp_dir, fn_report),))
                if ret['exitcode']:
                    logger.error(
                        "ERROR: transfering %s from local to wf-prod via scp is failed!" % (fn_report,), exc_info=True)
                    raise Exception("BOOM")
                else:
                    os.remove(os.path.join(tmp_dir, fn_report))
                sftp_batch = os.path.join(tmp_dir, 'sftp_batch_file')
                with open(sftp_batch, 'w') as fp:
                    print >> fp, 'put %s\nbye' % (
                        os.path.join(tmp_dir, fn_ctrl),)
                ret = run_command('sftp -C -b %s wf-prod' % (sftp_batch,))
                #ret = run_command('scp %s localhost:/vol/data/mock-sftp/ds3/' % (os.path.join(tmp_dir, fn_ctrl),))
                if ret['exitcode']:
                    logger.error(
                        "ERROR: transfering %s from local to wf-prod via scp is failed!" % (fn_ctrl,), exc_info=True)
                    raise Exception("BOOM")
                else:
                    os.remove(os.path.join(tmp_dir, fn_ctrl))
                shutil.rmtree(tmp_dir)
                return

            else:
                logger.info('Report is not ready. I will try again.')
                time.sleep(30)
        except HttpError as e:
            error = json.loads(e.content)['error']['errors'][0]

            # See Response Codes
            logger.error('HTTP code %d, reason %s' %
                         (e.resp.status, error['reason']))
            break


def do_work(start_date):
    for query_template in QUERY_TEMPLATES:
        try:
            with open(os.path.join(WORK_DIR, query_template), "rb") as fh:
                QUERY = json.load(fh).get("query", None)
                if not QUERY:
                    print >> sys.stderr, "Expected key query is not found.\n"
                    sys.exit(1)
        except IOError as e:
            print >> sys.stderr, "Error reading query template file in current directory.\n %s" % str(
                e)
            sys.exit(1)

        #dt_start = dt_end = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        dt_start = dt_end = start_date
        QUERY['timeRange']['startDate'] = dt_start
        QUERY['timeRange']['endDate'] = dt_end

        creds = create_credentials(
            SETTINGS["client_id"], SETTINGS["client_secret"], SETTINGS["refresh_token"])
        service = get_service(creds)
        report = request_report(service, QUERY)
        if report:
            report_id = report
            poll_report(service, report_id, QUERY['reportType'], dt_start=QUERY['timeRange']
                        ['startDate'], dt_end=QUERY['timeRange']['endDate'])


def start_heartbeat():
    def heartbeat():
        while 1:
            logger.info("heartbeat")
            time.sleep(HEARTBEAT_INTERVAL)
    t = Thread(target=heartbeat)
    t.daemon = True
    t.start()


def mainloop():
    import cPickle as pickle
    from dateutil.rrule import rrule, DAILY
    prev_day = datetime.date.today()-datetime.timedelta(1)
    iterdates = iter(rrule(DAILY, dtstart=datetime.date(2015, 07, 28), until=datetime.date(prev_day.year, prev_day.month, prev_day.day)))
    all_required = set([d.strftime('%Y-%m-%d') for d in iterdates])
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "completed.p"), "rb") as f:
        completed = pickle.load(f)
    needed = sorted(all_required - completed)
    # needed = ['2018-05-31']
    needed = [args.date_needed]

    logger.info("starting mainloop")
    for dt in needed:
        try:
            do_work(dt)
            completed.add(dt)
            with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "completed.p"), "wb") as f:
                pickle.dump(completed, f)
        except Exception, e:
            logging.exception(e)
            logger.error("BOOM: %s" % str(e))


def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)

    handler = logging.handlers.SysLogHandler('/dev/log')
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter(
        'Python: { "loggerName":"%(name)s", "ascTime":"%(asctime)s", "pathName":"%(pathname)s", "logRecordCreationTime":"%(created)f", "functionName":"%(funcName)s", "levelNo":"%(levelno)s", "lineNo":"%(lineno)d", "time":"%(msecs)d", "levelName":"%(levelname)s", "message":"%(message)s"}'))
    logger.addHandler(handler)


if __name__ == "__main__":

    import fcntl
    import sys
    pid_file = '/run/lock/lock_wf_ds3.pid'
    fh = open(pid_file, 'w')
    try:
        fcntl.lockf(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        # another instance is running
        print >> sys.stderr, 'Error: Another instance is running...'
        sys.exit(0)

    setup_logging()
    logger = logging.getLogger("daemon-ds3.wells_fargo")

    # parsing arguments
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--date_needed", required=True,
                        help="Input date needed in format: YYYY-MM-DD")
    parser.add_argument("-q", "--query_template", required=True, choices=[
                        "keyword", "visit", "conversion"], action="append", help="Query template. Ex. -q conversion,visit")
    args = parser.parse_args()

    # QUERY_TEMPLATES = ['keyword_query_template.txt', 'visit_query_template.txt','conversion_query_template.txt']
    # QUERY_TEMPLATES = ['conversion_query_template.txt']
    # QUERY_TEMPLATES = ['keyword_query_template.txt', 'visit_query_template.txt','conversion_query_template.txt']
    QUERY_TEMPLATES = [s + "_query_template.txt" for s in args.query_template]

    start_date = [args.date_needed]

    print QUERY_TEMPLATES
    print start_date

    #start_heartbeat()
    mainloop()

    #do_work('2016-01-19')
