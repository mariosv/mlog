========
Overview
========

**mlog** is a personal log/note keeping utility. It has a command line interface
that allows users to add/edit/remove/search text logs.

sqlite is used for storage and is accessed using SQLAlchemy ORM.

=====
Usage
=====

For a list of all the available command line options run::

    mlog --help

There are four available commands: *add*, *delete*, *edit*, *tags*, *list* and
a series of options. 


========
Commands
========

"add" command
=============

If you want to simply add a note- append a log, run::

    $> mlog add "message text here"

Message text can also be parsed from standard input by running::

    $> mlog add

Text from an input file can be used too::

    $> mlog add -i file_with_message

Existing or new tags can also be associated with the new log using --tags
option::

    $> mlog add -t "foo, bar"

this way the new log is associated with tags "foo" and "bar".

Note that tags are always converted to lower case. You can later on search using
these tags.


"list" command
==============

**list** command is used to display logs as well as to search logs.

By running::

    $> mlog list

A list of all the logs found in the database will be dumped at standard output.
This list can be filtered either by specifying the tags to be displayed(using
--tags option) or by specifying a search keayword right after the list command::

    $> mlog list <search keyword>

Returned list can also be filtered by date using --before and --after options::

    $> mlog list --before <DATE> --after <DATE>

DATE should be provided in the following format::

    year-month-dayThours:minutes:seconds


"delete" command
================

Deleting a log can be done with the following command::

    $> mlog del <log id>


"edit" command
==============

If you want to change the message or/and the tags of a log entry you can using
the **edit** command as follows::

    $> mlog edit <log id> [--tags <"new list of tags">]

mlog will then search your environment for VISUAL and EDITOR variables to find
your preferred editor. If nothing is found vi will be used. Text editor will
be launched and you can there edit and save the log message.

Tags of a log can be modified by using --tags option to supply a new list of
tags to be used. Note that if --tags is not used, tags of the log remain 
unchanged and if an empty tag list is provided::
    
    $> mlog edit <log id> --tags ""

no tags will be associated with the modified log.

TODO: there might be a problem with "zombie" tags


"tags" command
==============

To list all the available tags and their frequency run::

    $> mlog tags


=============
Database File
=============

The database file to be used for all operation can be set with the --db-path
command line option. If none is set, the default path for the database file
is used which is ~/.mlog-db.

