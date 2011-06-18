# This file is part of mlog
#
# mlog is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# mlog is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with mlog.  If not, see <http://www.gnu.org/licenses/>.
import os
import sys
import datetime

from db import *
from errors import *

class Logger(object):
    def __init__(self, options):
        """Creates a Logger options with the given configuration
           
           Arguments:
                options    An initialized ProgramOptions object

        """
        self.__configFilePath = options.configFile


        if len(options.logFile) == 0:
            self.__logFilePath = os.path.join(os.environ['HOME'], '.mlog-db')
        else:
            self.__logFilePath = options.logFile

        self.__searchKeyword = options.searchKeyword
        self.__beforeDate = self.__recreateDate(options.beforeDate)
        self.__afterDate = self.__recreateDate(options.afterDate)

        self.__appliedTags = options.tags

        self.__startDBSession()


    def printLogs(self):
        """Print all logs matching the given(if any) search criteria and tags

        """

        logs = []
        if len(self.__appliedTags) > 0:
            tList = []
            for tag in self.__appliedTags:
                # find tag
                t = self.__session.query(Tag).filter(Tag.name == tag).all()
                if len(t) == 1:
                    tList.append(t[0])
            for t in tList:
                logs += self.__session.query(Log).filter(Log.tags.contains(t))
        else:
            logs = self.__session.query(Log)

        for log in logs:
            if self.__logMatches(log):
                self.__printLog(log)


    def listTags(self):
        """Prints on stdout available tags and logs per tags count for each"""
        tags = self.__session.query(Tag).join(logTags).all();
        for tag in tags:
            logsPerTag = len(tag.logs)
            tagName = tag.name
            print("%6d: %s" % (logsPerTag, tagName))


    def deleteLogWithId(self, logId):
        """Delete the log with the provided log id"""
        log = self.__session.query(Log).get(logId)
        if log:
            self.__session.delete(log)
        else:
            sys.stderr.write("Log with id: " + str(logId) \
                             + " was not found in the database\n")


    def __printLog(self, log):
        """Print a log to stdout, also print the tags associated with this log

        """
        message = log.message
        date = log.date
        id = log.id
        tags = [x.name for x in log.tags]
        dashes = 40 * '-'
        print("\033[1m>%6d :: [%s] %s\033[0m" % (id, date, dashes))
        print(message)
        print('\n<%s>\n' % (', '.join([x.name for x in log.tags])))



    def appendLog(self, message):
        """Appends a log to the database"""
        log = Log(message.strip())

        for t in self.__appliedTags:
            dbTag = self.__session.query(Tag).filter(Tag.name == t)
            if(len(dbTag.all()) != 1):
                tag = Tag(t)
            else:
                tag = dbTag[0]
            log.tags.append(tag)
            self.__session.add(tag)
        self.__session.add(log)


    def __logMatches(self, log):
        """Check if a log matches the current date and keyword criteria"""
        matchSearch = False
        if self.__searchKeyword != 0:
            if self.__searchKeyword.lower() in log.message.lower():
                matchSearch = True
        else:
            matchSearch = True

        matchBefore = True
        matchAfter = True

        if self.__beforeDate:
            if log.date > self.__beforeDate:
                matchBefore = False

        if self.__afterDate:
            if dateFound < self.__afterDate:
                matchAfter = False

        return (matchSearch and matchBefore and matchAfter)


    def __del__(self):
        """Makes sure database is "closed" - changes are submited"""
        self.__closeDBSession()


    def __startDBSession(self):
        """Initializes database connection and starts a db session"""
        engine = create_engine('sqlite:///' + self.__logFilePath)
        #engine.echo = True
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.__session = Session()


    def __closeDBSession(self):
        """Commits changes to the database"""
        try:
            self.__session.commit()
        except Exception as error:
            sys.stderr.write('Failed to write log: ' + str(error) + '\n')
            self.__session.rollback()


    def __recreateDate(self, dateString):
        """Creates a Date object from a date string"""
        if len(dateString) == 0:
            return None
        ds = dateString.replace('[', '')
        ds = ds.replace(']', '')
        if len(ds) == 0:
            return None
        (date, time) = ds.split('T')
        (y, m, d) = date.split('-')
        (h, minutes, s) = time.split(':')

        try:
            newDate = datetime.datetime(int(y), int(m), int(d),
                                        int(h), int(minutes), int(float(s)))
        except ValueError, e:
            print(e)
            sys.exit(1)
        return newDate

