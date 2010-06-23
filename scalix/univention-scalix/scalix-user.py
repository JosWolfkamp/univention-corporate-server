# -*- coding: utf-8 -*-
#
# Univention Scalix
#  listener module: synchronizing information between UCS and Scalix
#
# Copyright 2006-2010 Univention GmbH
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

import listener
import os, string
import univention.debug
import univention_baseconfig

name='scalix-user'
description='update scalix user information'
# attributes=['scalixHideUserEntry', 'scalixMailboxClass', 'scalixLimitMailboxSize', 'scalixLimitOutboundMail', 'scalixLimitInboundMail', 'scalixLimitNotifyUser', 'scalixScalixObject', 'scalixMailnode', 'scalixServerLanguage', 'scalixAdministrator', 'scalixMailboxAdministrator', 'scalixEmailAddress', 'member', 'dn', 'uid', 'objectClass', 'displayName', 'sn', 'givenname', 'initials', 'mail' 'cn', 'facsimileTelephoneNumber', 'homephone', 'street', 'st', 'telephoneNumber', 'title', 'c', 'company', 'departmentNumber', 'description', 'l', 'mobile', 'pager', 'physicalDeliveryOfficeName', 'postalCode', 'mailPrimaryAddress', 'mailAlternativeAddress', 'uniqueMember']
attributes=[]

filter='(|(objectClass=univentionGroup)(&(objectClass=posixAccount)(objectClass=shadowAccount)))'

def handler(dn, new, old):

	try:
		listener.setuid(0)
		
		if (new and new.has_key('scalixScalixObject')) or (old and old.has_key('scalixScalixObject')):
			# ensure a utf-8-environment
			old_env=None
			if os.environ.has_key('LC_ALL'):
				old_env=os.environ['LC_ALL']
			os.environ['LC_ALL']='de_DE.UTF-8'

			baseConfig = univention_baseconfig.baseConfig()
			baseConfig.load()
			if baseConfig.has_key('scalix/omldapsync/parameter'):
				os.system("/opt/scalix/bin/omldapsync %s >>/var/log/univention/scalix-sync.log" % baseConfig['scalix/omldapsync/parameter'])
			else:
				os.system("/opt/scalix/bin/omldapsync -u ucs2scalix -S >> /var/log/univention/scalix-sync.log")

			if not old_env==None:
				os.environ['LC_ALL']=old_env
			else:
				del os.environ['LC_ALL']

	finally:
		listener.unsetuid()

def initialize():
	pass

def clean():
	pass

def postrun():
	pass
