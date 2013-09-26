# -*- coding: utf-8 -*-
#
# Copyright 2013 Univention GmbH
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

from univention.testing.strings import random_name
from univention.testing.utils import get_ldap_connection, fail
from univention.config_registry import ConfigRegistry
import subprocess
import sys

VALID_EXTENSION_TYPES = ('hook', 'syntax', 'module')

def get_package_name():
	""" returns a valid package name """
	return random_name()

def get_package_version():
	return random_version()

def get_extension_name(extension_type):
	"""
	Returns a valid extension name for the given extension type.
	>>> get_extension_name('hook')
	'jcvuardfqx'
	>>> get_extension_name('syntax')
	'hwvkm29tde'
	>>> get_extension_name('module')
	'ucstest/r3jkljngcp'
	"""
	assert(extension_type in VALID_EXTENSION_TYPES)
	if extension_type == 'module':
		return 'ucstest/%s' % random_name()
	else:
		return random_name()

def get_extension_filename(extension_type, extension_name):
	assert(extension_type in VALID_EXTENSION_TYPES)
	return '%s.py' % extension_name

def call_cmd(cmd, fail_on_error=True):
	"""
	Calls the given cmd (list of strings).
	"""
	print 'CMD: %r' % cmd
	sys.stdout.flush()
	exitcode = subprocess.call(cmd)
	if fail_on_error and exitcode:
		fail('EXITCODE of script %s: %r' % (cmd[0], exitcode))
	return exitcode

def call_join_script(name, fail_on_error=True):
	"""
	Calls the given join script (e.g. name='66foobar.inst').
	If fail is true, then the function fail() is called if the exitcode is not zero.
	"""
	ucr = ConfigRegistry()
	ucr.load()
	return call_cmd(['/usr/lib/univention-install/%s' % name, '--binddn', ucr.get('tests/domainadmin/account'), '--bindpwdfile', ucr.get('tests/domainadmin/pwdfile')], fail_on_error=fail_on_error)

def call_unjoin_script(name, fail_on_error=True):
	"""
	Calls the given unjoin script (e.g. name='66foobar-uninstall.uinst').
	If fail is true, then the function fail() is called if the exitcode is not zero.
	"""
	ucr = ConfigRegistry()
	ucr.load()
	return call_cmd(['/usr/lib/univention-uninstall/%s' % name, '--binddn', ucr.get('tests/domainadmin/account'), '--bindpwdfile', ucr.get('tests/domainadmin/pwdfile')], fail_on_error=fail_on_error)

def get_syntax_buffer(name=None):
	"""
	Returns a UDM syntax with given name (e.g. 'MySimpleHook'). If name is omitted,
	a randomly generated name is used.
	"""
	if name is None:
		name = random_name()
	return '''# this syntax class has been created by ucs-test
class %(syntax_name)s(simple):
        regex = re.compile('^ucstest-[0-9A-Za-z]+$')
        error_message = 'Wrong value given for ucs-test-syntax!'
''' % {'syntax_name': name}

def get_hook_buffer(name=None):
	"""
	Returns a UDM hook with given name (e.g. 'MySimpleHook'). If name is omitted,
	a randomly generated name is used.
	"""
	if name is None:
		name = random_name()
	return '''# this udm hook has been created by ucs-test
from univention.admin.hook import simpleHook

class %(hook_name)s(simpleHook):
	type = 'SetDescriptionValue'

	def hook_ldap_pre_modify(self, obj):
		""" Set description consisting of username, lastname """
		obj['description'] = 'USERNAME=%%(username)s  LASTNAME=%%(lastname)s' %% obj.info
''' % {'hook_name': name}


def get_module_buffer(name=None):
	"""
	Returns a UDM module with given name (e.g. 'testing/mytest'). If name is omitted,
	a randomly generated name is used ('ucstest/%(randomstring)s').
	"""
	if name is None:
		name = 'ucstest/%s' % (random_name(), )
	assert('/' in name)
	return '''# this UDM module has been created by ucs-test
from univention.admin.layout import Tab
import univention.admin.uldap
import univention.admin.syntax
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization

translation=univention.admin.localization.translation('univention.admin.handlers.container')
_=translation.translate

module='%(module_udmname)s'
operations=['add','edit','remove','search','move','subtree_move']
childs=1
short_description=_('Univention UCSTest Module')
long_description=''
options={}
property_descriptions={
	'name': univention.admin.property(
			short_description=_('Name'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			include_in_default_search=1,
			options=[],
			required=1,
			may_change=0,
			identifies=1,
		),
}
layout = [Tab( _('General'),_('Basic values'),[ "name" ] )]
mapping=univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
class object(univention.admin.handlers.simpleLdap):
	module=module
	def __init__(self, co, lo, position, dn='', superordinate=None, attributes = [] ):
		global mapping
		global property_descriptions
		self.mapping=mapping
		self.descriptions=property_descriptions
		univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate, attributes = attributes )

	def _ldap_pre_create(self):
		self.dn='%%s=%%s,%%s' %% (mapping.mapName('name'), mapping.mapValue('name', self.info['name']), self.position.getDn())

	def _ldap_addlist(self):
		return [('objectClass', ['top', 'organizationalRole'])]

def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):
	filter=univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'organizationalRole'),
		univention.admin.filter.expression('cn', 'univention')
		])
	if filter_s:
		filter_p=univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)
	res=[]
	for dn, attrs in lo.search(unicode(filter), base, scope, [], unique, required, timeout, sizelimit):
		res.append( object( co, lo, None, dn, attributes = attrs ) )
	return res

def identify(dn, attr, canonical=0):
	return 'organizationalRole' in attr.get('objectClass', []) and attr.get('cn', []) == ['univention']
''' %  {'module_udmname': name}


def get_extension_buffer(extension_type, name=None):
	"""
	Get UDM extension of specified type with specified name.
	In case the name is omitted, a random name will be used.
	"""
	assert(extension_type in VALID_EXTENSION_TYPES)
	return { 'hook': get_hook_buffer,
	  'syntax': get_syntax_buffer,
	  'module': get_module_buffer,
	  }[extension_type](name)


def get_postinst_script_buffer(extension_type, filename, app_id=None, version_start=None, version_end=None):
	"""
	Returns a postinst script that registers the given file as UDM extension with extension type ('hook', 'syntax' or 'module').
	Optionally UNIVENTION_APP_ID, UCS version start and UCS version end may be specified.
	"""
	assert(extension_type in VALID_EXTENSION_TYPES)
	if not app_id:
		app_id = ''
	else:
		app_id = 'UNIVENTION_APP_IDENTIFIER="%s"' % app_id
	if not version_start:
		version_start = ''
	else:
		version_start = '--ucsversionstart %s' % version_start
	if not version_end:
		version_end = ''
	else:
		version_end = '--ucsversionend %s' % version_end

	return '''#!/bin/sh
set -e
#DEBHELPER#
%(app_id)s
. /usr/share/univention-lib/ldap.sh
ucs_registerLDAPExtension "$@" --udm_%(extension_type)s %(filename)s %(version_start)s %(version_end)s || die
exit 0
''' % {'filename': filename, 'extension_type': extension_type, 'app_id': app_id,
	   'version_start': version_start, 'version_end': version_end}


def get_postrm_script_buffer(extension_type, extension_name, package_name):
	"""
	Returns an postrm script that deregisters the given UDM extension. The type of the extension
	has to be specified ('hook', 'syntax' or 'module').
	"""
	assert(extension_type in VALID_EXTENSION_TYPES)
	if extension_type == 'module':
		assert('/' in extension_name)
	return'''#!/bin/sh
set -e
#DEBHELPER#
. /usr/share/univention-lib/ldap.sh
ucs_unregisterLDAPExtension "$@" --udm_%(extension_type)s %(extension_name)s || die
exit 0
''' % {'package_name': package_name, 'extension_name': extension_name, 'extension_type': extension_type}


def get_join_script_buffer(extension_type, filename, app_id=None, joinscript_version=1, version_start=None, version_end=None):
	"""
	Returns a join script that registers the given file as UDM extension with extension type ('hook', 'syntax' or 'module').
	Optionally a joinscript version, UNIVENTION_APP_ID, UCS version start and UCS version end may be specified.
	"""
	assert(extension_type in VALID_EXTENSION_TYPES)
	if not app_id:
		app_id = ''
	else:
		app_id = 'UNIVENTION_APP_IDENTIFIER="%s"' % app_id
	if not version_start:
		version_start = ''
	else:
		version_start = '--ucsversionstart %s' % version_start
	if not version_end:
		version_end = ''
	else:
		version_end = '--ucsversionend %s' % version_end

	return '''#!/bin/sh
VERSION=%(joinscript_version)s
set -e
. /usr/share/univention-join/joinscripthelper.lib
joinscript_init
%(app_id)s
. /usr/share/univention-lib/ldap.sh
ucs_registerLDAPExtension "$@" --udm_%(extension_type)s %(filename)s %(version_start)s %(version_end)s || die
joinscript_save_current_version
exit 0
''' % {'filename': filename, 'joinscript_version': joinscript_version, 'extension_type': extension_type, 'app_id': app_id,
	   'version_start': version_start, 'version_end': version_end}

def get_unjoin_script_buffer(extension_type, extension_name, package_name):
	"""
	Returns an unjoin script that deregisters the given UDM extension. The type of the extension
	has to be specified ('hook', 'syntax' or 'module').
	"""
	assert(extension_type in VALID_EXTENSION_TYPES)
	if extension_type == 'module':
		assert('/' in extension_name)
	return'''#!/bin/sh
VERSION=1
set -e
. /usr/share/univention-join/joinscripthelper.lib
joinscript_init
. /usr/share/univention-lib/ldap.sh
ucs_unregisterLDAPExtension "$@" --udm_%(extension_type)s %(extension_name)s || die
joinscript_remove_script_from_status_file %(package_name)s
exit 0
''' % {'package_name': package_name, 'extension_name': extension_name, 'extension_type': extension_type}


def get_absolute_extension_filename(extension_type, filename):
	"""
	Returns the absolute path to an extentension of the given type and filename.
	"""
	assert(extension_type in VALID_EXTENSION_TYPES)
	if extension_type == 'module':
		assert('/' in filename)
	return {'hook': '/usr/share/pyshared/univention/admin/hooks.d/%s',
			'syntax': '/usr/share/pyshared/univention/admin/syntax.d/%s',
			'module': '/usr/share/pyshared/univention/admin/handlers/%s',
			}[extension_type] % filename


def get_dn_of_extension_by_name(extension_type, name):
	"""
	Returns a list of DNs of UDM extension objects with given type an name, or [] if no object has been found.
	"""
	assert(extension_type in VALID_EXTENSION_TYPES)
	if extension_type == 'module':
		assert('/' in name)
	searchfilter = {'hook': '(&(objectClass=univentionUDMHook)(cn=%s))' % name,
					'syntax': '(&(objectClass=univentionUDMSyntax)(cn=%s))' % name,
					'module': '(&(objectClass=univentionUDMModule)(cn=%s))' % name,
					}[extension_type]
	return get_ldap_connection().searchDn(filter=searchfilter)


def remove_extension_by_name(extension_type, extension_name, fail_on_error=True):
	"""
	Remove all extensions of given type and name from LDAP.
	"""
	assert(extension_type in VALID_EXTENSION_TYPES)
	for dn in get_dn_of_extension_by_name(extension_type, extension_name):
		cmd = ['udm', 'settings/udm_%s' % extension_type, 'remove', '--dn', dn]
		print 'CMD: %r' % cmd
		sys.stdout.flush()
		if subprocess.call(cmd):
			if fail_on_error:
				fail('Failed to remove %s' % dn)
			else:
				print 'ERROR: failed to remove %s' % dn
