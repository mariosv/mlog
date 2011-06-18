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
"""Error class hierarchy for mlog project"""


class Error(Exception):
    """Base Error class of all mlog error classses"""
    def __init__(self, msg):
        super(Exception, self).__init__(msg)


class ConfigError(Error):
    """Error specialized for configuration errors, typically invalid mlog
       command invocation

    """
    def __init__(self, msg):
        super(Error, self).__init__('Configuration error: ' + str(msg))

