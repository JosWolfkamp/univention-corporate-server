# -*- coding: utf-8 -*-
"""
Python native Univention debugging library.

See :py:mod:`univention.debug` for an alternative being a wrapper for the C
implementation.
"""
# Copyright 2008-2019 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.

from __future__ import print_function
import sys
import logging
# import logging.handlers

ERROR = 0
WARN = 1
PROCESS = 2
INFO = 3
ALL = 4
DEFAULT = WARN

# The default levels provided are DEBUG(10), INFO(20), WARNING(30), ERROR(40) and CRITICAL(50).
# Mapping old levels to new ones
_map_lvl_old2new = {
	0: logging.ERROR,    # 40
	1: logging.WARNING,  # 30
	2: 25,               # 25
	3: logging.INFO,     # 20
	4: 15,               # 15
}

MAIN = 0x00
LDAP = 0x01
USERS = 0x02
NETWORK = 0x03
SSL = 0x04
SLAPD = 0x05
SEARCH = 0x06
TRANSFILE = 0x07
LISTENER = 0x08
POLICY = 0x09
ADMIN = 0x0A
CONFIG = 0x0B
LICENSE = 0x0C
KERBEROS = 0x0D
DHCP = 0x0E
PROTOCOL = 0x0F
MODULE = 0x10
ACL = 0x11
RESOURCES = 0x12
PARSER = 0x13
LOCALE = 0x14
AUTH = 0x15

NO_FLUSH = 0x00
FLUSH = 0x01

NO_FUNCTION = 0x00
FUNCTION = 0x01

_map_id_old2new = {
	MAIN: "MAIN",
	LDAP: "LDAP",
	USERS: "USERS",
	NETWORK: "NETWORK",
	SSL: "SSL",
	SLAPD: "SLAPD",
	SEARCH: "SEARCH",
	TRANSFILE: "TRANSFILE",
	LISTENER: "LISTENER",
	POLICY: "POLICY",
	ADMIN: "ADMIN",
	CONFIG: "CONFIG",
	LICENSE: "LICENSE",
	KERBEROS: "KERBEROS",
	DHCP: "DHCP",
	PROTOCOL: "PROTOCOL",
	MODULE: "MODULE",
	ACL: "ACL",
	RESOURCES: "RESOURCES",
	PARSER: "PARSER",
	LOCALE: "LOCALE",
	AUTH: "AUTH",
}


# 13.08.08 13:13:57.123  LISTENER    ( ERROR   ) : listener: 1
# 13.08.08 13:13:57.123  LISTENER    ( WARN    ) : received signal 2
# 13.08.08 13:14:02.123  DEBUG_INIT
_outfmt = '%(asctime)s.%(msecs)03d %(name)-11s (%(levelname)-7s): %(message)s'
_outfmt_syslog = '%(name)-11s (%(levelname)-7s): %(message)s'
_datefmt = '%d.%m.%Y %H:%M:%S'

_logfilename = None
_handler_console = None
_handler_file = None
_handler_syslog = None
_do_flush = False
_enable_function = False
_enable_syslog = False
_logger_level = dict((key, DEFAULT) for key in _map_id_old2new.values())


def init(logfilename, do_flush=0, enable_function=0, enable_syslog=0):
	"""
	Initialize debugging library for logging to 'logfile', forcing 'flush' and tracing 'function's.

	:param str logfilename:  name of the logfile, or 'stderr', or 'stdout'.
	:param bool do_flush: force flushing of messages (True).
	:param bool enable_function: enable (True) or disable (False) function tracing.
	:param bool enable_syslog: enable (True) or disable (False) logging to SysLog.
	:returns: output file or None.
	"""
	global _logfilename, _handler_console, _handler_file, _handler_syslog, _do_flush, _enable_function, _enable_syslog

	result = None
	_logfilename = logfilename

	# create root logger
	logging.basicConfig(level=logging.DEBUG,
						filename='/dev/null',       # disabled
						format=_outfmt,
						datefmt=_datefmt)

	formatter = logging.Formatter(_outfmt, _datefmt)
	exit()
	if logfilename == 'stderr' or logfilename == 'stdout':
		# add stderr or stdout handler
		_handler_console = logging.StreamHandler(sys.stdout if logfilename == 'stdout' else sys.stderr)
		_handler_console.setLevel(logging.DEBUG)
		_handler_console.setFormatter(formatter)
		logging.getLogger('').addHandler(_handler_console)
		result = _handler_console.stream
	else:
		try:
			# add file handler
			_handler_file = logging.FileHandler(logfilename, 'a+')
			_handler_file.setLevel(logging.DEBUG)
			_handler_file.setFormatter(formatter)
			logging.getLogger('').addHandler(_handler_file)
			result = _handler_file.stream
		except EnvironmentError as ex:
			print('opening %s failed: %s' % (logfilename, ex))

# 	if enable_syslog:
# 		try:
# add syslog handler
# 			_handler_syslog = logging.handlers.SysLogHandler( ('localhost', 514), logging.handlers.SysLogHandler.LOG_ERR )
# 			_handler_syslog.setLevel( _map_lvl_old2new[ERROR] )
# 			_handler_syslog.setFormatter(formatter)
# 			logging.getLogger('').addHandler(_handler_syslog)
# 		except:
# 			raise
# 			print('opening syslog failed')

	logging.addLevelName(25, 'PROCESS')
	logging.addLevelName(15, 'ALL')
	logging.addLevelName(100, '------')

	logging.getLogger('MAIN').log(100, 'DEBUG_INIT')

	_do_flush = do_flush
	_enable_function = enable_function
	_enable_syslog = enable_syslog

	return result


def exit():
	"""
	Close debug logfile.
	"""
	global _handler_console, _handler_file, _handler_syslog
	logging.getLogger('MAIN').log(100, 'DEBUG_EXIT')
	if _handler_console:
		logging.getLogger('').removeHandler(_handler_console)
		_handler_console = None

	if _handler_file:
		logging.getLogger('').removeHandler(_handler_file)
		_handler_file = None


def reopen():
	"""
	Close and re-open the debug logfile.
	"""
	logging.getLogger('MAIN').log(100, 'DEBUG_REINIT')
	init(_logfilename, _do_flush, _enable_function, _enable_syslog)


def set_level(id, level):
	"""
	Set minimum required severity 'level' for facility 'id'.

	:param int id: ID of the category, e.g. MAIN, LDAP, USERS, ...
	:param int level: Level of logging, e.g. ERROR, WARN, PROCESS, INFO, ALL
	"""
	new_id = _map_id_old2new.get(id, 'MAIN')
	if level > ALL:
		level = ALL
	elif level < ERROR:
		level = ERROR
	_logger_level[new_id] = level


def get_level(id):
	"""
	Get minimum required severity for facility 'category'.

	:param int id: ID of the category, e.g. MAIN, LDAP, USERS, ...
	:return: Return debug level of category.
	:rtype: int
	"""
	new_id = _map_id_old2new.get(id, 'MAIN')
	return _logger_level[new_id]


def set_function(activated):
	"""
	Enable or disable the logging of function begins and ends.

	:param bool activated: enable (True) or disable (False) function tracing.
	"""
	global _enable_function
	_enable_function = activated


def debug(id, level, msg, utf8=True):
	"""
	Log message 'message' of severity 'level' to facility 'category'.

	:param int id: ID of the category, e.g. MAIN, LDAP, USERS, ...
	:param int level: Level of logging, e.g. ERROR, WARN, PROCESS, INFO, ALL
	:param str msg: The message to log
	:param bool utf8: Assume the message is UTF-8 encoded.
	"""
	new_id = _map_id_old2new.get(id, 'MAIN')
	if level <= _logger_level[new_id]:
		new_level = _map_lvl_old2new[level]
		logging.getLogger(new_id).log(new_level, msg)
		# flush if requested
		if _do_flush:
			for handler in [_handler_console, _handler_file, _handler_syslog]:
				if handler:
					handler.flush()


class function(object):

	def __init__(self, text, utf8=True):
		"""
		Log the begin of function 'function'.

		:param str text: name of the function starting.
		:param bool utf8: Assume the message is UTF-8 encoded.
		"""
		self.text = text
		if _enable_function:
			logging.getLogger('MAIN').log(100, 'UNIVENTION_DEBUG_BEGIN : ' + self.text)
			# flush if requested
			if _do_flush:
				for handler in [_handler_console, _handler_file, _handler_syslog]:
					if handler:
						handler.flush()

	def __del__(self):
		"""
		Log the end of function.
		"""
		if _enable_function:
			logging.getLogger('MAIN').log(100, 'UNIVENTION_DEBUG_END   : ' + self.text)
			# flush if requested
			if _do_flush:
				for handler in [_handler_console, _handler_file, _handler_syslog]:
					if handler:
						handler.flush()
