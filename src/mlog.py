#!/usr/bin/env python

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
"""Entry point for the console interface of mlog. Command line arguments are
   parsed and the appropriate operations are performed using the core modules

"""

import os
import sys
import optparse
import re

from core.errors import *
from core.logger import *


class ProgramCommands(object):
    """Enumeration of the available mlog operations"""
    ADD = 0
    LIST = 1
    DELETE = 2
    EDIT = 3
    LIST_TAGS = 4


class ProgramOptions(object):
    """Parses and stores user provided command options. Command line options are
       parsed on initialization.

       Attributes:
            inputFile       an input file name to log it's contents
            dbPath          a log file to write the database instead of the
                            standard log path
            afterDate       Search start date. Start search logs after this
                            date.
            beforeDate      Search end date. End searching logs after this date
            logId           A logId. Used for the DELETE operation
            searchKeyword   Search keyword for SEARCH operation
            message         Message to log

       Raises:
            ConfigError
                                
       """
    inputFile = None
    dbPath = None
    afterDate = ''
    beforeDate = ''
    logId = ''
    searchKeaword = ''
    message = ''

    def __init__(self):
        (self.__options, self.__args) = self.__parseCLOptions()

        self.inputFile = self.__options.inputFile
        self.dbPath = self.__options.dbPath
        self.afterDate = self.__options.afterDate
        self.beforeDate = self.__options.beforeDate

        self.logId = -1

        self.searchKeyword = ''
        self.message = ''

        self.command = self.__determineCommand()

        # parse tag list
        self.tags = self.__findTags(self.__options.tagList)

        # get search keyword
        if self.command == ProgramCommands.LIST:
            if len(self.__args) > 2:
                raise ConfigError('Too many arguments for list command')
            if len(self.__args) == 2:
                self.searchKeyword = self.__args[1]

        # parse the message for add command
        elif self.command == ProgramCommands.ADD:
            self.message = self.__parseMessage()
        elif self.command == ProgramCommands.DELETE:
            err = 'A valid log id must be provided'
            if len(self.__args) == 2:
                try:
                    self.logId = int(self.__args[1])
                except ValueError as e:
                    raise ConfigError(err + str(e))
            else:
                raise ConfigError(err)
        elif self.command == ProgramCommands.LIST_TAGS:
            if len(self.__args) != 1:
                raise ConfigError("Too many arguments for tags command")


    def __parseMessage(self):
        """Parses the log message text:
            1. If an input file is specified, its contents are used as the log
               message text. If filename provided is '-', stdin is parsed
            2. If no input file is specified, either any text after the add
               command is used or input is expected from stdin

        """
        message = ''
        if self.__options.inputFile is None:
            # no input file provided
            message = ' '.join(self.__args[1:])
            msg_copy = message.strip()
            if len(msg_copy) != 0:
                return message
            else:
                message = sys.stdin.read()
                print('')
                msg_copy = message.strip()
                if len(msg_copy) != 0:
                    return message.strip()
        else:
            # parse input file
            if self.__options.inputFile == '-':
                # parse standard input
                message = sys.stdin.read()
                print('')
            else:
                try:
                    fd = open(self.__options.inputFile)
                    message = fd.read()
                    fd.close()
                except IOError as error:
                    raise ConfigError(str(error))
            return message.strip()


    def __findTags(self, tagList):
        """Split a tag string to a list of tags. Tags can be given with any
           seperator. But it's tag can be only a single word

        """
        tags = []
        if len(self.__options.tagList.strip()) != 0:
            tags = [x.lower() for x in re.findall('\w+', tagList)]
        return tags


    def __determineCommand(self):
        """Parse the command argument and determine which operation should be
           executed

        """
        validCommands = ('list', 'ls', 'add', 'delete', 'del', 'modify', 'edit',
                         'tags', 'list-tags')
        if len(self.__args) == 0:
            raise ConfigError('No command specified')

        cmd = self.__args[0]

        if cmd not in validCommands:
            err = "Invalid command: %s\n Valid commands are: %s\n" % (cmd,
                    validCommands)
            raise ConfigErr(err)

        if cmd in ('ls', 'list'):
            command = ProgramCommands.LIST
        elif cmd in ('add'):
            command = ProgramCommands.ADD
        elif cmd in ('delete', 'del'):
            command = ProgramCommands.DELETE
        elif cmd in ('modify', 'edit'):
            command = ProgramCommands.EDIT
        elif cmd in ('tags', 'list-tags'):
            command = ProgramCommands.LIST_TAGS
        else:
            raise ConfigError('Unknown command: %s' % cmd)

        return command


    def __parseCLOptions(self):
        """Parses command line arguments and returns a dictionary with the
           parsed values and a list with the non parsable values

        """
        usage = "Usage: %prog <command> [options]\n" \
                "Available commands: list add delete edit tags"

        parser = optparse.OptionParser(usage=usage)

        # build mode option
        parser.add_option('-i', '--input-file',
                          dest = 'inputFile',
                          help = 'File containing text to be logged',
                          default = None,
                          metavar = 'INPUT_FILE')
        parser.add_option('-d', '--db-path',
                          dest = 'dbPath',
                          default = None,
                          help = 'File to be used as logfile',
                          metavar = 'DATABASE_PATH')
        parser.add_option('-a', '--after',
                          dest = 'afterDate',
                          default = '',
                          help = 'Return logs after the given (ISO) date',
                          metavar = 'AFTER_DATE')
        parser.add_option('-b', '--before',
                          dest = 'beforeDate',
                          default = '',
                          help = 'Return logs before the given (ISO) date',
                          metavar = 'BEFORE_DATE')
        parser.add_option('-t', '--tags',
                          dest = 'tagList',
                          default = '',
                          help = 'List of tags for the new log',
                          metavar = 'TAGS')

        (options, args) = parser.parse_args()
        return (options, args)



def main():
    options = ProgramOptions()

    logger = Logger(options)

    if options.command == ProgramCommands.LIST:
        logger.printLogs()
    elif options.command == ProgramCommands.ADD:
        logger.appendLog(options.message)
    elif options.command == ProgramCommands.EDIT:
        pass
    elif options.command == ProgramCommands.DELETE:
        logger.deleteLogWithId(options.logId)
    elif options.command == ProgramCommands.LIST_TAGS:
        logger.listTags()


if __name__ == '__main__':
    try:
        main()
    except ConfigError as error:
         sys.stderr.write(str(error) + '\n')
         sys.exit(os.EX_CONFIG)
    except Error as error:
         sys.stderr.write(str(error) + '\n')
         sys.exit(os.EX_SOFTWARE)
        
        
