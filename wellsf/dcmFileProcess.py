import os
import gzip
import zipfile
import subprocess
import pandas as pd
import datetime
import sys
#add to sys.path lib directory so this can be run by command line
if '\\' in (os.getcwd()):
    sys.path.insert(0,os.getcwd().replace(os.getcwd().split('\\')[-1],'lib'))
else:
    sys.path.insert(0,os.getcwd().replace(os.getcwd().split('/')[-1],'lib'))
import logging
import logging.handlers
import shutil
import codecs
from anConfig import anConfig
from sqlToolMySQL import sqlToolMySQL
import csv
import io
import paramiko
from Queue import Queue
from threading import Thread
from s3Tool import s3Tool
import fnmatch


class fileProcessor(object):

    def __init__(self,ownerName, processTypeParam=None):
        self.config = anConfig('adeserver.cfg', 'adeserveroverride.cfg')
        self.connectionNameMySQL = 'mysqlDev'
        self.ownerName = ownerName
        self.downloadDirectory = os.path.join(os.path.abspath(os.path.dirname(__file__)),'download','')
        self.processedDirectory = os.path.join(os.path.abspath(os.path.dirname(__file__)),'processed','')
        self.directoryPurgeCompleted = False
        self.unicodePipe = '|'#.encode('utf-8')
        self.unicodeCarat = '^'#.encode('utf-8')
        self.unicodeNewLine = '\n'#.encode('utf-8')
        self.fileTypeRun = 'ALL'

        if processTypeParam:
            self.fileTypeRun = processTypeParam


    def commandRun(self, comms):
        """
          Runs gsutils with params
        """
        env = os.environ.copy()
        subP = subprocess.Popen(comms.split(), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = subP.communicate()
        exitcode = subP.returncode
        pid = subP.pid
        results = {"stdout": stdout, "stderr": stderr, "exitcode": exitcode, "pid": pid}
        return results

    def processDateGet(self):
        startDate = datetime.date.today() + datetime.timedelta(-60)
        dateList = pd.date_range(start=startDate, end=datetime.date.today()+datetime.timedelta(-1)).tolist()
        dateListFinal = []
        for dateItem in dateList:
            #start of pulling
            if dateItem >= datetime.datetime.strptime('2/26/2017','%m/%d/%Y'):
                dateListFinal.append(dateItem.strftime('%Y%m%d'))
        return dateListFinal

    def previouslyProcessedDatesGet(self):

        sqlText = ''
        with open(os.path.join(os.path.abspath(os.path.dirname(__file__)),'sql','get_processed_file_dates.sql')) as sqlFile:
            sqlText = sqlFile.read()

        sqlText = sqlText.format(owner_name=self.ownerName)
        returnDates = []

        try:
            with sqlToolMySQL(self.config,self.connectionNameMySQL) as sqlTool:
                if sqlTool.executeQuery(sqlText, False, False):
                    for result in sqlTool.cursor:
                        if result[0]:
                            returnDates.append(result[0])
        except Exception, e:
            self.logger.info('Exception occured: '.format(e))

        return returnDates

    def directoryFilePurge(self,fileName=None, directory=None):
        #purge all
        if not fileName and not directory:
            for file in os.listdir(self.downloadDirectory):
                os.unlink(os.path.join(self.downloadDirectory,file))
        elif directory:
            for file in os.listdir(directory):
                os.unlink(os.path.join(directory,file))
        else:
            os.unlink(os.path.join(self.downloadDirectory,fileName))

    def directoryFileCompress(self,fileName=None, directory=None):
        if not fileName and not directory:
            for file in os.listdir(self.processedDirectory):
                if not '.ctl' in file and '.gz' not in file:
                    with open(os.path.join(self.processedDirectory,file),'rb') as fromFile, gzip.open(os.path.join(self.processedDirectory,file + '.gz'),'wb') as zipped:
                        zipped.writelines(fromFile)
                    os.unlink(os.path.join(self.processedDirectory,file))

        elif directory and not fileName:
            for file in os.listdir(directory):
                if not '.ctl' in file and '.gz' not in file:
                    with open(os.path.join(self.processedDirectory,file),'rb') as fromFile, gzip.open(os.path.join(self.processedDirectory,file + '.gz'),'wb') as zipped:
                        zipped.writelines(fromFile)
                    os.unlink(os.path.join(self.processedDirectory,file))
        else:
            with open(os.path.join(self.processedDirectory,fileName),'rb') as fromFile, gzip.open(os.path.join(self.processedDirectory,file + '.gz'),'wb') as zipped:
                    zipped.writelines(fromFile)
            os.unlink(os.path.join(self.processedDirectory,fileName))

    def fileMoveFromDownloadToProcessed(self,fileName):
        shutil.move(fileName, fileName.replace('download','processed'))

    def colHeaderCheckIfKeep(self,fileType, headerList):
        if fileType == 'activity':
            keepList = ['Event Time','Activity ID','User ID','Advertiser ID','Campaign ID','Ad ID',
                        'Rendering ID','Creative Version','Site ID (DCM)','Placement ID','Country Code','State/Region',
                        'Browser/Platform ID','Browser/Platform Version','Operating System ID','User ID',
                        'Total Conversions','Total Revenue','TRAN Value','Other Data',
                        'ORD Value','Interaction Time','Conversion ID','Segment Value 1','Partner1 ID','Partner2 ID']
        if fileType == 'click':
            keepList = ['Event Time','User ID','Advertiser ID','Campaign ID','Ad ID','Rendering ID','Creative Version',
                        'Site ID (DCM)','Placement ID','Country Code','State/Region','Browser/Platform ID',
                        'Browser/Platform Version','Operating System ID','Designated Market Area (DMA) ID','City ID',
                        'ZIP/Postal Code','U Value','Segment Value 1','Partner1 ID','Partner2 ID']
        if fileType == 'impression':
            keepList = ['Event Time','User ID','Advertiser ID','Campaign ID','Ad ID','Rendering ID','Creative Version',
                        'Site ID (DCM)','Placement ID','Country Code','State/Region','Browser/Platform ID',
                        'Browser/Platform Version','Operating System ID','Designated Market Area (DMA) ID',
                        'City ID','ZIP/Postal Code','U Value']
        if fileType == 'search':
            keepList = ['From','To','Engine','Account','Status','Campaign','Ad group','Keyword','Match type',
                        'Device segment','Impr','Clicks','Cost','CC_Product_Submit']
        if fileType == 'display':
            keepList = ['Site (DCM)','Date','Placement','Creative','Campaign','Platform Type','Impressions','Clicks',
                        'Media Cost']

        columnKeep = []
        for x,item in enumerate(headerList):
            if item in keepList:
                columnKeep.append(x)
        return columnKeep

    def fileFtp(self, directory=None,configSection = None):
        if not directory:
            directory = self.processedDirectory

        hostName = ''
        port = 0
        user = ''
        password = ''
        ftpDir = ''

        if not configSection:
            hostName = self.config.getString('wfFTP','host')
            port = int(self.config.getString('wfFTP','port'))
            user = self.config.getString('wfFTP','user')
            ftpDir = self.config.getString('wfFTP','directory')
        else:
            hostName = self.config.getString(configSection,'host')
            port = int(self.config.getString(configSection,'port'))
            user = self.config.getString(configSection,'user')
            password = self.config.getString(configSection,'password')
            ftpDir = self.config.getString(configSection,'directory')

        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()

        #this file is gitignored and will need to be manually placed
        key = None
        if not configSection:
            key = paramiko.RSAKey.from_private_key_file('wf_rsa_key.ppk')
        else:
            key = self.config.getString(configSection,'key')

        def moveFtpFile(q):

            transport = paramiko.Transport((hostName,port))
            if key:
                transport.connect(hostkey=None,username=user,pkey=key)
            else:
                transport.connect(hostkey=None,username=user,password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)

            try:
                while not q.empty():
                    fileNameOnly = q.get()
                    fullFileName = os.path.join(directory,fileNameOnly)

                    #file move
                    #can't confirm, because we don't have permissions so confirm=False
                    sftp.put(fullFileName,'/{}/{}'.format(ftpDir,fileNameOnly), confirm=False)
                    #file delete
                    os.unlink(os.path.join(directory,fileNameOnly))

                    q.task_done()
                    self.logger.info("File FTP'd: {}".format(fileNameOnly))
            except Exception as e:
                print e.message
            sftp.close()
            return True

        numOfThreads = 5
        q = Queue(maxsize=0)
        keys = []

        for file in os.listdir(directory):
            q.put(file)


        #set up the worker threads
        for i in range(numOfThreads):
            self.logger.info('Starting thread: ' + str(i))
            worker = Thread(target=moveFtpFile, args=(q,))
            worker.setDaemon(True)    #setting threads as "daemon" allows main program to
                                      #exit eventually even if these dont finish
                                      #correctly.
            worker.start()

        #now we wait until the queue has been processed
        q.join()

    def matchFilesProcess(self, dateValue):

        #download all files in parallel to working directory
        commandString = 'gsutil -m cp gs://dcdt_-{owner_name}/{owner_name}_match_table_*{date_value}_????????_* {download_dir}'\
            .format(owner_name=self.ownerName, date_value=dateValue,download_dir=self.downloadDirectory)

        if self.fileTypeRun in ('ALL','MATCH'):
            self.logger.info('Downloading match files...')
            results = self.commandRun(commandString)
            self.logger.info('GSUTIL results: {}'.format(results['exitcode']))

        #download activity file
        commandString = 'gsutil -m cp gs://dcdt_-{owner_name}/{owner_name}_activity_*{date_value}_????????_* {download_dir}'\
            .format(owner_name=self.ownerName, date_value=dateValue,download_dir=self.downloadDirectory)
        if self.fileTypeRun in ('ALL','ACTIVITY'):
            self.logger.info('Downloading activity file...')
            results = self.commandRun(commandString)
            self.logger.info('GSUTIL results: {}'.format(results['exitcode']))

        availableFiles = os.listdir(self.downloadDirectory)
        if '' in availableFiles:
            availableFiles.remove('')
        availableFiles.sort(reverse=True)
        dedupedAvailableFileType = []
        #loop through files, removing duplicated files, unzipping and getting information about all files
        for fileName in availableFiles:
            self.logger.info('Processing file: {}'.format(fileName))
            controlString = []
            #add fileName to control String
            controlString.append(str(fileName).replace('.gz','').replace('.csv','.txt'))
            #add processDate to controlString
            controlString.append(dateValue)
            if str(fileName)[:str(fileName).find(dateValue)] not in dedupedAvailableFileType:

                dedupedAvailableFileType.append(str(fileName)[:str(fileName).find(dateValue)])
                originalFileName = str(fileName).split('_')
                del originalFileName[0:2]
                destFileList = []
                for part in originalFileName:
                    if part in ('match','table'):
                        pass
                    #after we get one digit (which is a date) break the loop.  That's all the file name WF wants
                    elif part.isdigit():
                        destFileList.append(part)
                        break
                    else:
                        destFileList.append(part)
                shortFileName = '_'.join(destFileList) + '.txt'
                destFile = os.path.join(self.downloadDirectory,shortFileName)
                destFileControlFile = destFile.replace('.txt','.ctl')
                zippedFile = os.path.join(self.downloadDirectory,str(fileName))

                totalLines = 0
                self.logger.info('Replacing characters and getting line counts...')

                isActivityFile = False
                if shortFileName[0:10] == 'activity_2':
                    isActivityFile = True

                with codecs.open(destFile,'wb+','utf-8') as decompressedFile, gzip.open(zippedFile,'rb') as compressedFile:
                    writeString = ''
                    colHeadersKeep = []
                    for line in compressedFile:
                        totalLines += 1
                        data = io.BytesIO(line)
                        unicodeRow = list(csv.reader(data))[0]
                        #pass header out to be check
                        if totalLines == 1 and isActivityFile:
                            colHeadersKeep = self.colHeaderCheckIfKeep('activity', unicodeRow)

                        colCleaned = []
                        if isActivityFile:
                            for x, col in enumerate(unicodeRow):
                                #don't write out unused columns
                                if x in colHeadersKeep:
                                    colCleaned.append(col.replace(self.unicodePipe,self.unicodeCarat))
                        else:
                            for col in unicodeRow:
                                colCleaned.append(col.replace(self.unicodePipe,self.unicodeCarat))

                        writeString += self.unicodePipe.join(colCleaned)
                        writeString += self.unicodeNewLine

                        #write out every x lines
                        if totalLines % 100 == 0:
                            decompressedFile.write(writeString.decode('utf-8'))
                            writeString = ''

                    #loop completed and lines didn't exactly trip modulous (very likely), write out remaining lines
                    if totalLines % 100 != 0:
                        decompressedFile.write(writeString.decode('utf-8'))


                #write file size
                controlString.append(str(os.path.getsize(destFile)))
                #write number of lines
                controlString.append(str(totalLines))
                finalControlString = '|'.join(controlString)

                with open(destFileControlFile,'wb+') as f:
                    f.write('|'.join(controlString))

                self.directoryFilePurge(fileName)
                self.logger.info('Moving {} and {} to processedFolder'.format(destFile, destFileControlFile))
                self.fileMoveFromDownloadToProcessed(destFile)
                self.fileMoveFromDownloadToProcessed(destFileControlFile)
            else:
                #remove files we already have the newest version of
                self.directoryFilePurge(fileName)
                self.logger.info('File discarded due to duplications file: {}'.format(fileName))


            self.logger.info('Finished file: {}'.format(fileName))

    def combineFileProcess(self, dateValue):

        #download all files in parallel to working directory
        #this needs to be done in 3 pulls, because 1) we want to parallelize it as much as we can and
        #2) the impression/click files come for a different time period than the activity file for the day (5 hour difference)
        #3) so we'll need to shift this daily (and it'll need to be run after 7 AM EST each day to ensure the files are there)
        results = {'exitcode':-99}
        dateValueAsDatePlusOne = (datetime.datetime.strptime(dateValue,'%Y%m%d')+datetime.timedelta(days=1))\
            .strftime('%Y%m%d')
        commandString = 'gsutil -m cp gs://dcdt_-dcm_account6049/dcm_account6049_*_{date_value}0[5-9]_????????_* {download_dir}'\
            .format(owner_name=self.ownerName, date_value=dateValue,download_dir=self.downloadDirectory)
        if self.fileTypeRun in ('ALL','IMPRESSION'):
            self.logger.info('Downloading click/impression files 06 through 09...')
            results = self.commandRun(commandString)
            self.logger.info('GSUTIL results: {}'.format(results['exitcode']))

        commandString = 'gsutil -m cp gs://dcdt_-dcm_account6049/dcm_account6049_*_{date_value}[1-2][0-9]_????????_* {download_dir}'\
            .format(owner_name=self.ownerName, date_value=dateValue,download_dir=self.downloadDirectory)
        if self.fileTypeRun in ('ALL','IMPRESSION'):
            self.logger.info('Downloading click/impression files 10 through 24...')
            results = self.commandRun(commandString)
            self.logger.info('GSUTIL results: {}'.format(results['exitcode']))

        commandString = 'gsutil -m cp gs://dcdt_-dcm_account6049/dcm_account6049_*_{date_value_plus_one}0[0-4]_????????_* {download_dir}'\
            .format(owner_name=self.ownerName, date_value_plus_one=dateValueAsDatePlusOne,download_dir=self.downloadDirectory)
        if self.fileTypeRun in ('ALL','IMPRESSION'):
            self.logger.info('Downloading click/impression files 01 through 05 of NEXT day...')
            results = self.commandRun(commandString)
            self.logger.info('GSUTIL results: {}'.format(results['exitcode']))

            self.logger.info('Finished downloading click/impression files.')

            self.combineFile('click',dateValue)
            self.combineFile('impression',dateValue)

    def combineFile(self,fileType, dateValue):
        finalFileName = '{file_type}_{date_value}.txt'.format(file_type=fileType,date_value = dateValue)
        finalFileNameWithDir = os.path.join(self.processedDirectory,finalFileName)
        destFileControlFile = os.path.join(self.processedDirectory,finalFileName.replace('.txt','.ctl'))

        controlString = []
        availableFiles = os.listdir(self.downloadDirectory)

        if '' in availableFiles:
            availableFiles.remove('')
        availableFiles.sort()

        self.logger.info('processing {} files...'.format(fileType))
        gen = (x for x in availableFiles if fileType in x)

        controlString.append(finalFileName)
        #add processDate to controlString
        controlString.append(dateValue)

        headerRecordSet = False
        totalLines = 0

        colHeadersKeep = []
        with codecs.open(finalFileNameWithDir,'wb+','utf-8') as decompressedFile:
            for fileName in gen:
                writeString = ''
                processingFileNameWithDir = os.path.join(self.downloadDirectory,fileName)
                currentFileLines = 0
                self.logger.info('Processing file: {}'.format(fileName))
                with gzip.open(processingFileNameWithDir,'rb') as compressedFile:
                    for line in compressedFile:
                        data = io.BytesIO(line)
                        unicodeRow = list(csv.reader(data))[0]
                        #pass header out to be check
                        if totalLines == 0:
                            colHeadersKeep = self.colHeaderCheckIfKeep(fileType, unicodeRow)
                        if (not headerRecordSet and currentFileLines == 0) \
                                or (headerRecordSet and currentFileLines != 0):
                            headerRecordSet = True
                            totalLines += 1
                            currentFileLines += 1
                            colCleaned = []
                            for x, col in enumerate(unicodeRow):
                                #don't write out unused columns
                                if x in colHeadersKeep:
                                    colCleaned.append(col.replace(self.unicodePipe,self.unicodeCarat))

                            writeString += self.unicodePipe.join(colCleaned)
                            writeString += self.unicodeNewLine

                            #write out every x lines
                            if totalLines % 100 == 0:
                                decompressedFile.write(writeString.decode('utf-8'))
                                writeString = ''
                        else:
                            currentFileLines += 1
                    #loop completed and lines didn't exactly trip modulous (very likely), write out remaining lines
                    if totalLines % 100 != 0:
                        decompressedFile.write(writeString.decode('utf-8'))

        self.logger.info('Finished combining files for {}'.format(fileType))
        #write file size
        controlString.append(str(os.path.getsize(finalFileNameWithDir)))
        #write number of lines
        controlString.append(str(totalLines))
        finalControlString = '|'.join(controlString)

        with open(destFileControlFile,'wb+') as f:
            f.write('|'.join(controlString))

    def unicode_csv_reader(self,fileName,skipRows = 0,encoding = 'utf-8',delimiter=','):
        csv_reader = csv.reader(codecs.open(fileName,'rb',encoding),delimiter=delimiter)

        if skipRows:
            for i in range(skipRows):
                csv_reader.next()

        for row in csv_reader:
            yield [unicode(cell, 'utf-8') for cell in row]

    def incubatorProcessRun(self,processType):

        def processIncubatorReport(processType,fileName,outFileName):
            reader = self.unicode_csv_reader(fileName,skipRows=10 if processType == 'display' else 0,
                                             encoding='utf-16' if processType == 'search' else 'utf-8',
                                             delimiter=',')

            writer = codecs.open(outFileName,'w','utf-8')

            colIndexes = None
            recordCounter = 0
            dateUpdates = []

            if processType == 'display':
                colNameUpdate = {
                    'Site (DCM)':'Site',
                    'Placement': 'Placement Name'
                }
            elif processType == 'search':
                colNameUpdate = {
                    'Ad group':'Adgroup',
                    'Match type':'Matchtype',
                    'Device segment':'Device'
                }
                dateUpdates = [3, 4]

            for row in reader:

                if row[0] == 'Grand Total:':
                    break

                writeRecord = []
                if recordCounter == 0:
                    colIndexes = self.colHeaderCheckIfKeep(processType, row)
                for (i,cell) in enumerate(row):
                    if i in colIndexes:
                        if recordCounter == 0:
                            cell = colNameUpdate.get(cell,cell)
                        elif i in dateUpdates:
                            cell = datetime.datetime.strftime(datetime.datetime.strptime(cell,'%Y-%m-%d'),'%m/%d/%Y')
                        elif processType == 'search' and i == 9:
                            if '"' in cell or '=' in cell:
                                cell = cell.replace('"', '').replace('=', '')
                        writeRecord.append(cell)
                writer.write(u'|'.join(writeRecord) + u'\n')
                recordCounter += 1

            #Generate control files here
            writer.close()
            ctrlFile = open(outFileName[0:-4] + '.ctl','w')
            ctrlFile.write('|'.join([os.path.basename(outFileName),\
                                     os.path.basename(outFileName[-12:-4]),\
                                     str(os.path.getsize(outFileName)),
                                     str(recordCounter)]))
            ctrlFile.close()


        prefix = 'DI' + processType
        configSection = 'WFDIS3'

        self.downloadDirectory = os.path.join(os.path.abspath(os.path.dirname(__file__)), prefix + 'Download', '')
        self.processedDirectory = os.path.join(os.path.abspath(os.path.dirname(__file__)), prefix + 'Processed', '')

        #First time setup
        for directory in [self.downloadDirectory,self.processedDirectory]:
            if not os.path.exists(directory):
                os.makedirs(directory)

        #Clear out anything remaining
        self.directoryFilePurge()
        self.directoryFilePurge(directory=self.processedDirectory)

        s3Info = {
            'accessKeyId': None,
            'secretAccessKey': None,
            'bucket': self.config.getString(configSection,'bucket')
        }

        s3 = s3Tool(config=self.config)

        if processType == 'search':
            timestamp = datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d')
            filename = self.config.getString(configSection,'path') + 'ResolutionMedia_PaidSearch_AgencyData_60d.zip'
            try:
                s3.moveKey(s3Info,filename,filename.replace('.zip','_{0}.zip'.format(timestamp)))
            except Exception as e:
                print 'Renaming RM file failed: {0}'.format(e)

        fileInfo = {}

        #These file names look like they might change. If so, just update here.
        if processType == 'search':
            fileInfo = {
                'originalFileName': 'ResolutionMedia_PaidSearch_AgencyData*.*',
                'finalFileNameTemplate': 'ResolutionMedia_PaidSearch_AgencyData_YYYYMMDD.txt'
            }

        elif processType == 'display':
            fileInfo = {
                'originalFileName': '*_DI_DCM_Paid_Media_Daily_Pull_*.*',
                'finalFileNameTemplate': 'OMD_PaidDisplay_AgencyData_YYYYMMDD.txt'
            }

        fileCounter = 0
        path = self.config.getString(configSection,'path')
        processedFiles = []

        fileList = s3.getFileList(s3Info,path)

        for file in fileList:

            if '/Archive' in file:
                continue

            baseFileName = os.path.basename(file)

            if fnmatch.fnmatch(baseFileName,fileInfo['originalFileName']):
                timestamp = ''
                if processType == 'display':
                    timestamp = file[-29:-21]

                workingFileName = self.downloadDirectory + baseFileName
                s3.fileReadToFile(s3Info, file, workingFileName)
                processedFiles.append(file)

                if workingFileName[-4:] == '.zip':
                    zip = zipfile.ZipFile(workingFileName,'r')
                    zip.extractall(self.downloadDirectory)
                    zip.close()

                fileCounter += 1

        for (i,file) in enumerate(os.listdir(self.downloadDirectory),1):
            if file[-4:] == '.zip':
                continue

            suffix = ''
            if processType == 'display':
                suffix = file[-29:-21]
            elif processType == 'search' and len(file) == 50:
                suffix = file[-12:-4]
            else:
                #The RM files don't look to be supplied in an automated fashion. Need to see how
                #they are going to do it going forward (I only see one in s3).
                suffix = datetime.datetime.strftime(datetime.datetime.now(),'%Y%m%d')

            fullFileName = self.downloadDirectory + '/' + file
            processIncubatorReport(processType,fullFileName,
                                 self.processedDirectory + '/' +
                                 fileInfo['finalFileNameTemplate'].replace('YYYYMMDD',suffix))


        #Move them out
        if processedFiles:
            try:
                self.fileFtp(directory=None,configSection='WFDIFTP')
            except Exception as e:
                print u'An error has occurred during upload. Message returned by application: {0}'.format(e)

            #Success - Moving processed files in s3 to archive directory
            for file in processedFiles:
                s3.moveKey(s3Info,file,self.config.getString(configSection,'archive_path') + os.path.basename(file))

    def runProcess(self,specificDates=None,processType = None):

        if processType in ['search','display']:
            self.incubatorProcessRun(processType)
            return

        if specificDates:
            potentialDates = specificDates
            #previouslyRunDates should be blank, because we're forcing the run
            previouslyRunDates = []
        else:
            potentialDates = self.processDateGet()
            previouslyRunDates = self.previouslyProcessedDatesGet()

        toRunDates = list(set(potentialDates) - set(previouslyRunDates))
        toRunDates.sort()
        sqlText = ''
        with open(os.path.join(os.path.abspath(os.path.dirname(__file__)),'sql','insert_processed_file_date.sql')) as sqlFile:
            sqlText = sqlFile.read()

        #purge downloadDirectory
        self.directoryPurgeCompleted = False
        for dateValue in toRunDates:
            if not self.directoryPurgeCompleted:
                self.directoryFilePurge()
                self.directoryFilePurge(directory=self.processedDirectory)
                self.directoryPurgeCompleted = True
            self.matchFilesProcess(dateValue)
            self.combineFileProcess(dateValue)
            #log processed_date to sql
            try:
                sqlTextReplaced = sqlText.format(owner_name = self.ownerName,
                                                 date_value = dateValue)
                with sqlToolMySQL(self.config,self.connectionNameMySQL) as sqlTool:
                    sqlTool.executeQuery(sqlTextReplaced, False, True)
            except Exception, e:
                self.logger.info('Exception occured: '.format(e))
                raise Exception(e)
            self.directoryFilePurge()
        #compress all files
        self.directoryFileCompress()
        #ftp all files here

    def setup_logging(self):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        self.logger.addHandler(handler)

        #don't do this on windows
        if os.name != 'nt':
            handler = logging.handlers.SysLogHandler('/dev/log')
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter('Python: { "loggerName":"%(name)s", "ascTime":"%(asctime)s", "pathName":"%(pathname)s", "logRecordCreationTime":"%(created)f", "functionName":"%(funcName)s", "levelNo":"%(levelno)s", "lineNo":"%(lineno)d", "time":"%(msecs)d", "levelName":"%(levelname)s", "message":"%(message)s"}'))
        self.logger.addHandler(handler)

if __name__ == '__main__':

    processTypes = ['search','display','ALL','IMPRESSION','MATCH','ACTIVITY']
    processType = None

    if len(sys.argv) <= 1:
        print 'No parameters passed in, please revise call of main()...'
    if len(sys.argv) >= 2:
        ownerName = sys.argv[1]
        #dcm_account6049
        print 'Running for ownerName:{}'.format(ownerName)
        specificDates = None
    if len(sys.argv) >= 3:
        if sys.argv[2] in processTypes:
            processType = sys.argv[2]
        else:
            specificDates = []
            specificDates.append(sys.argv[2])
    if len(sys.argv) >= 4:
        processType = sys.argv[3]
    fp = fileProcessor(ownerName, processType)

    fp.setup_logging()

    fp.runProcess(specificDates=specificDates,processType=processType)

    if not processType:
        fp.fileFtp()
