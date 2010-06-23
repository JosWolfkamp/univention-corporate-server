#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention nscd Updater
#  Univention Listener Module
#
# Copyright 2001-2010 Univention GmbH
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

name='nscd_update'
description='Invalidate the NSCD group cache whenever a group membership has been modified.'
filter='(objectClass=univentionGroup)'
attributes=['uniqueMember', 'cn']

import listener
import univention_baseconfig
import univention.debug

def handler(dn, new, old):
	pass

def postrun():
	baseConfig = univention_baseconfig.baseConfig()
	baseConfig.load()

	if baseConfig.get('nscd/group/invalidate_cache_on_changes', 'false').lower() in [ 'true', 'yes', 'on']:
		listener.setuid(0)
		try:
			univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, "calling 'nscd -i group'")
			listener.run('/usr/sbin/nscd', ['nscd', '-i', 'group'], uid=0)
		except:
			univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, "nscd -i group was not successfull")
		listener.unsetuid()
