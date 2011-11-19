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
import tempfile
import subprocess

from db import *
from errors import *

from sqlalchemy.orm import relation, sessionmaker, relationship, backref

class Logger(object):
    def __init__(self, options):
        """Creates a Logger options with the given configuration

           Arguments:
                options    An initialized ProgramOptions object

        """
        self.__session = None

        if options.dbPath is None:
            self.__logFilePath = os.path.join(os.environ['HOME'], '.mlog-db')
        else:
            self.__logFilePath = options.dbPath

        self.__searchKeyword = options.searchKeyword
        self.__beforeDate = self.__recreateDate(options.beforeDate)
        self.__afterDate = self.__recreateDate(options.afterDate)

        self.__appliedTags = options.tags

        self.__startDBSession()


    def __del__(self):
        """Makes sure database is "closed" - changes are submited"""
        self.__closeDBSession()


    def printLogs(self):
        """Print all logs matching the given(if any) search criteria and tags

        """
        logs = []
        if self.__appliedTags is not None and len(self.__appliedTags) > 0:
            tList = []
            for tag in self.__appliedTags:
                # find tag
                t = self.__session.query(Tag).filter(Tag.name == tag).all()
                if len(t) == 1:
                    tList.append(t[0])
                else:
                    # all given tags must exist in the database
                    e = "Tag \"%s\" does not exist in the database" % tag
                    raise Error(e)
            clauses = and_(* [Log.tags.contains(x) for x in tList])
            logs = self.__session.query(Log).filter(clauses)
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


    def appendLog(self, message):
        """Appends a log to the database"""
        log = Log(message.strip())

        if self.__appliedTags is not None:
            for t in self.__appliedTags:
                tag = self.__getOrCreateTag(t)
                log.tags.append(tag)
        self.__session.add(log)


    def deleteLogWithId(self, logId):
        """Delete the log with the provided log id"""
        log = self.__session.query(Log).get(logId)
        if log:
            self.__session.delete(log)
        else:
            e = ("Log with id: " + str(logId) \
                 + " was not found in the database\n")
            raise Error(e)


    def editLogWithId(self, logId):
        """Launches users default editor to edit the contents of the log with
           the provided id. If a tag list is provided it is used to replace
           current tags

        """
        # find log in the database
        log = self.__session.query(Log).get(logId)
        if not log:
            e = ("Log with id: " + str(logId) \
                 + " was not found in the database\n")
            raise Error(e)
        # edit log message and replace the original
        log.message = self.__editMessageInExternalEditor(log.message)

        # change tags
        if self.__appliedTags is not None:
            tagList = []
            for tag in self.__appliedTags:
                tagList.append(self.__getOrCreateTag(tag))
            log.tags = tagList


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


    def __getOrCreateTag(self, tagName):
        """Searches db for a tag with the given name. If none is found it
           creates one

        """
        dbTag = self.__session.query(Tag).filter(Tag.name == tagName)
        if(len(dbTag.all()) != 1):
            tag = Tag(tagName)
            self.__session.add(tag)
        else:
            tag = dbTag[0]

        return tag


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
            if log.date < self.__afterDate:
                matchAfter = False

        return (matchSearch and matchBefore and matchAfter)


    def __startDBSession(self):
        """Initializes database connection and starts a db session"""
        engine = create_engine('sqlite:///' + self.__logFilePath)
        #engine.echo = True
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.__session = Session()


    def __closeDBSession(self):
        """Commits changes to the database"""
        if self.__session is None:
           return

        try:
            self.__session.commit()
        except Exception as error:
            sys.stderr.write('Failed to write log: ' + str(error) + '\n')
            self.__session.rollback()


    def __recreateDate(self, dateString):
        """Creates a Date object from a date string"""
        if (isinstance(dateString, datetime.datetime)):
            return dateString
        if len(dateString) == 0:
            return None
        ds = dateString.replace('[', '')
        ds = ds.replace(']', '')
        if len(ds) == 0:
            return None
        try:
            (date, time) = ds.split('T')
            (y, m, d) = date.split('-')
            (h, minutes, s) = time.split(':')

            newDate = datetime.datetime(int(y), int(m), int(d),
                                        int(h), int(minutes), int(float(s)))
            return newDate
        except ValueError, e:
            raise ConfigError('Invalid date string: %s' % (dateString))


    def __editMessageInExternalEditor(self, original):
        """Launches an external editor to edit the given message string"""
        (fd, name) = tempfile.mkstemp(prefix="mlog-temp-file-")
        try:
            # write original text on the temp file
            tmp = os.fdopen(fd, 'w')
            tmp.write(original)
            tmp.close()
            # launch external editor to edit the message
            userEditor = self.__getEditor()
            subprocess.call((userEditor, name))
            # read the modified file
            tmp = open(name)
            newMessage = tmp.read()
            tmp.close()
        except OSError:
            e = "Editor \"%s\" was not found.\nSet the EDITOR or VISUAL " \
                "environment variable to point to a valid text editor." \
                % (userEditor)
            raise Error(e)
        except Exception as error:
            raise Error('Error editing message: %s' % str(error))
        finally:
            os.unlink(name)
        return newMessage


    def __getEditor(self):
        """Return editor to use

           Attempts to find user default editor and return the command string
           to call it. If it is not found vi is used

        """
        userEditor = 'vi'
        visual = os.environ.get('VISUAL')
        if visual:
            userEditor = visual
        editor = os.environ.get('EDITOR')
        if editor:
            userEditor = editor
        return userEditor

