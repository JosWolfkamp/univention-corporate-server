# -*- coding: utf-8 -*-
#
# Univention Baseconfig
#  set relay host / smarthost in sendmail cfg
#
# Copyright 2007-2010 Univention GmbH
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

import os

mcfile = '/etc/mail/sendmail.mc'
cffile = '/etc/mail/sendmail.cf'

def handler(baseConfig, changes):
	strA = "define(`SMART_HOST',`"
	strAfull = "define(`SMART_HOST',`%s')dnl"
	strB = "define(`confAUTH_MECHANISMS', `EXTERNAL GSSAPI DIGEST-MD5 CRAM-MD5 LOGIN PLAIN')dnl"
	strC = "FEATURE(`authinfo', `hash /etc/mail/auth/client-info')dnl"
	strD = "include(`/etc/mail/sasl/sasl.m4')dnl"

	relayhost = ""
	if baseConfig.has_key('mail/sendmail/relayhost'):
		relayhost = baseConfig['mail/sendmail/relayhost']
	if not relayhost:
		return

	relayauth = False
	if baseConfig.has_key('mail/sendmail/relayauth') and baseConfig['mail/sendmail/relayauth'] in ['yes', 'true']:
		relayauth = True

	fh=open(mcfile, 'r')
	lines = fh.read().splitlines()
	fh.close()

	changed = False
	foundHost = False
	foundAuth = False
	foundSASL = False

	for idx in range(len(lines)):
		pos = lines[idx].find(strA)
		if (pos == 0):
			lines[idx] = strAfull % relayhost
			changed = True
			foundHost = True

		for key in [ strB, strC, strD ]:
			pos = lines[idx].find(key)
			if (pos == 0) or (pos == 4):
				# found?
				if lines[idx][0:4]=='dnl ' or pos == 0:
					foundAuth = True

				if relayauth and pos == 4 and lines[idx][0:4] == 'dnl ':
					lines[idx] = lines[idx][4:]
					changed = True

				if not relayauth and pos == 0:
					lines[idx] = 'dnl ' + lines[idx]
					changed = True

				if lines[idx].startswith(strD):
					foundSASL = True

	if not foundHost:
		for i in range(len(lines)):
			if lines[i][0:18] == 'MAILER_DEFINITIONS':
				lines.insert(i,'')
				lines.insert(i,strAfull % relayhost)
				lines.insert(i,'')
				changed = True
				break
		else:
			lines.append('')
			lines.append(strAfull % relayhost)
			lines.append('')
			changed = True

	if relayauth and not foundAuth:
		for i in range(len(lines)):
			if lines[i][0:18] == 'MAILER_DEFINITIONS':
				lines.insert(i,'')
				lines.insert(i,strB)
				lines.insert(i,strC)
				lines.insert(i,'')
				changed = True
				break
		else:
			lines.append('')
			lines.append(strB)
			lines.append(strC)
			lines.append('')
			changed = True

	if relayauth and not foundSASL:
		mark='''include(`/usr/share/sendmail/cf/m4/cf.m4')dnl'''
		for i in range(len(lines)):
			if lines[i].startswith(mark):
				lines.insert(i+1, '''include(`/etc/mail/sasl/sasl.m4')dnl''')
				changed = True
				break

	if relayauth:
		# check if sasl include file exists, create it otherwise
		if not os.path.isfile("/etc/mail/sasl/sasl.m4"):
			if os.path.isfile("/usr/share/sendmail/update_authm4"):
				os.system("/usr/share/sendmail/update_authm4")
				
	if changed:
		fh=open(mcfile, 'w')
		fh.write( '\n'.join(lines) + '\n')
		fh.close()

		os.system('m4 %s > %s' % (mcfile, cffile))
		os.system('PATH=$PATH:/opt/scalix/bin/ omsendin')
