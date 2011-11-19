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
import argparse
import re

from core.errors import Error, ConfigError
from core.logger import Logger


class AliasedSubParsersAction(argparse._SubParsersAction):
    """Aliases for argparse positional arguments.
    https://gist.github.com/471779
    """

    class _AliasedPseudoAction(argparse.Action):
        def __init__(self, name, aliases, help):
            dest = name
            if aliases:
                dest += ' (%s)' % ','.join(aliases)
            sup = super(AliasedSubParsersAction._AliasedPseudoAction, self)
            sup.__init__(option_strings=[], dest=dest, help=help)

    def add_parser(self, name, **kwargs):
        if 'aliases' in kwargs:
            aliases = kwargs['aliases']
            del kwargs['aliases']
        else:
            aliases = []

        parser = super(AliasedSubParsersAction, self).add_parser(name, **kwargs)

        # Make the aliases work.
        for alias in aliases:
            self._name_parser_map[alias] = parser
        # Make the help text reflect them, first removing old help entry.
        if 'help' in kwargs:
            help = kwargs.pop('help')
            self._choices_actions.pop()
            pseudo_action = self._AliasedPseudoAction(name, aliases, help)
            self._choices_actions.append(pseudo_action)

        return parser


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
        # defaults
        self.searchKeyword = None
        self.tags = []

        # argparse Namespace object
        args_ns = self.__parseCLOptions()

        self.__args = args_ns._get_args()
        self.__options = dict(args_ns._get_kwargs())

        # global options
        self.dbPath = self.__options.get('dbPath')

        self.logId = -1

        self.command = self.__options.get('command', ProgramCommands.LIST)

        if self.command == ProgramCommands.LIST:
            self.tags = self.__findTags(self.__options.get('tagList', []))
            self.afterDate = self.__options.get('afterDate')
            self.beforeDate = self.__options.get('beforeDate')
            self.searchKeyword = self.__options.get('searchKeyword', '')

        # parse the message for add command
        elif self.command == ProgramCommands.ADD:
            self.message = self.__parseMessage()
            self.tags = self.__findTags(self.__options.get('tagList', []))

        # handle update/removal
        elif self.command in (ProgramCommands.DELETE, ProgramCommands.EDIT):
            self.tags = self.__findTags(self.__options.get('tagList', None))
            self.inputFile = self.__options.get('inputFile', None)
            self.logId = self.__options.get('entry_id')


    def __parseMessage(self):
        """Parses the log message text:
            1. If an input file is specified, its contents are used as the log
               message text. If filename provided is '-', stdin is parsed
            2. If no input file is specified, either any text after the add
               command is used or input is expected from stdin

        """
        message = ''
        inputFile = self.__options.get('inputFile')
        if inputFile is None:
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
            if inputFile == '-':
                # parse standard input
                message = sys.stdin.read()
                print('')
            else:
                try:
                    fd = open(inputFile)
                    message = fd.read()
                    fd.close()
                except IOError as error:
                    raise ConfigError(str(error))
            return message.strip()


    def __findTags(self, tagList):
        """Get tags options and do some extra parsing to match comma
        seperated tags. Return None if tags not set in command line
        """

        if not tagList:
            return None

        tags = []
        for t in tagList:
            tag_splits = t.split(',')
            if len(tag_splits) > 0:
                for newtag in tag_splits:
                    tags.append(newtag)
            else:
                tags.append(t.replace(",",""))

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
            raise ConfigError(err)

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

        parser = argparse.ArgumentParser(conflict_handler='resolve')
        parser.register('action', 'parsers', AliasedSubParsersAction)
        subparsers = parser.add_subparsers()

        # database argument
        parser.add_argument('-d', '--db-path',
                          dest = 'dbPath',
                          default = None,
                          help = 'File to be used as logfile',
                          metavar = 'DATABASE_PATH')

        # list parser
        parser_list = subparsers.add_parser('list', aliases=['l','ls', 'll'],
                                            help = 'List existing log entries',)
        parser_list.add_argument('-a', '--after',
                          dest = 'afterDate',
                          default = '',
                          help = 'Return logs after the given (ISO) date',
                          metavar = 'AFTER_DATE')
        parser_list.add_argument('-b', '--before',
                          dest = 'beforeDate',
                          default = '',
                          help = 'Return logs before the given (ISO) date',
                          metavar = 'BEFORE_DATE')
        parser_list.add_argument('-t', '--tags',
                          dest = 'tagList',
                          default = None,
                          nargs = '+',
                          help = 'List of tags to filter results',
                          metavar = 'TAGS')

        # add parser
        parser_add = subparsers.add_parser('add', aliases=['a'],
                                           help = 'Create new log entries')
        parser_add.add_argument('-i', '--input-file',
                          dest = 'inputFile',
                          help = 'File containing text to be logged',
                          default = None,
                          metavar = 'INPUT_FILE')
        parser_add.add_argument('-t', '--tags',
                          dest = 'tagList',
                          default = None,
                          nargs = '+',
                          help = 'List of tags for the new log',
                          metavar = 'TAGS')

        # edit/delete parsers
        parser_edit = subparsers.add_parser('edit', aliases=['e'],
                                            help = 'Edit existing log entries',
                                            parents=[parser_add],
                                            conflict_handler='resolve')
        parser_edit.add_argument('entry_id', help = 'Entry to edit')
        parser_delete = subparsers.add_parser('delete',
                                              aliases = ['del', 'd'],
                                              help = 'Remove existing '
                                                     'log entries')
        parser_delete.add_argument('entry_id', help = 'Entry to delete')
        # tags list parser
        parser_list_tags = subparsers.add_parser('tags', aliases=['lt',
                                                                  'list-tags'],
                                                 help = 'List existing '
                                                        'log entries')

        # commands
        parser_add.set_defaults(command=ProgramCommands.ADD)
        parser_list.set_defaults(command=ProgramCommands.LIST)
        parser_edit.set_defaults(command=ProgramCommands.EDIT)
        parser_delete.set_defaults(command=ProgramCommands.DELETE)
        parser_list_tags.set_defaults(command=ProgramCommands.LIST_TAGS)

        # no args, show list command
        if (len(sys.argv) < 2):
            options = parser.parse_args(['list'])
        else:
            options = parser.parse_args()

        return options



def main():
    options = ProgramOptions()
    logger = Logger(options)

    if options.command == ProgramCommands.LIST:
        logger.printLogs()
    elif options.command == ProgramCommands.ADD:
        logger.appendLog(options.message)
    elif options.command == ProgramCommands.EDIT:
        logger.editLogWithId(options.logId)
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


