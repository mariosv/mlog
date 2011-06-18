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
"""Database definition. All database persistant types are declared in this
   module

"""
import datetime

from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation, sessionmaker, relationship, backref


Base = declarative_base()


# association table
logTags = Table('logTags', Base.metadata,
                Column('log_id', Integer, ForeignKey('logs.id')),
                Column('tag_id', Integer, ForeignKey('tags.id'))
)


class Log(Base):
    """A log contains an id, a date and a text message. If a date is not
       specified the current date is set.

       A M-N relationship is declared between Log and Tag. Tags of a log can
       be accessed using the tags attribute

    """
    __tablename__ = 'logs'

    id = Column(Integer, primary_key=True)
    date = Column(DateTime)
    message = Column(String)

    tags = relationship('Tag', secondary=logTags, backref='logs')

    def __init__(self, msg, date=None):
        self.date = date
        if date is None:
            self.date = datetime.datetime.now()
        self.message = msg

    def __repr__(self):
        return "<Log(%s, %s, %s)>" % (str(self.date), self.message,
                                      ' '.join([x.name for x in self.tags]))


class Tag(Base):
    """A tag is consisted of a unique id and a unique name column"""
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "<Tag(%s)>" % (str(self.name))

