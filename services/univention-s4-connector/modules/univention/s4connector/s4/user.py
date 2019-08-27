#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  sid sync
#
# Copyright 2004-2019 Univention GmbH
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
import base64
import univention.debug2 as ud


map_prefdev = ['any', 'mhs', 'physical', 'telex', 'teletex', 'g3fax', 'g4fax', 'ia5', 'videotex', 'telephone']


def prefdev_sync_s4_to_ucs(s4connector, key, s4_object):
	ud.debug(ud.LDAP, ud.ERROR, "s4toucs %s" % s4_object)
	attr = 'preferredDeliveryMethod'
	try:
		s4_prefdev = s4_object['attributes'][attr]
	except Exception:
		return
	else:
		if s4_prefdev is None:
			return
	ucs_pref = ''
	for pref in s4_prefdev:
		try:
			int(pref)
		except Exception:
			return
		else:
			ucs_pref += map_prefdev[int(pref)] + ' $ '
	ucs_pref = ucs_pref[:-3]
	return [ucs_pref]


def prefdev_sync_ucs_to_s4(s4connector, key, ucs_object):
	ud.debug(ud.LDAP, ud.ERROR, "ucstos4 %s" % ucs_object)
	attr = 'preferredDeliveryMethod'
	try:
		ucs_prefdev = ucs_object['attributes'][attr]
	except Exception:
		return
	else:
		if ucs_prefdev is None:
			return

	s4_prefdev = []
	for pref in ucs_prefdev[0].replace(' ', '').split('$'):
		if pref in map_prefdev:
			s4_prefdev.append(str(map_prefdev.index(pref)))
	return s4_prefdev


def userCert_sync_s4_to_ucs(s4connector, key, s4_object):
	attr = 'userCert'
	try:
		s4_cert = s4_object['attributes'][attr][0]
	except Exception:
		return
	ucs_cert = base64.b64encode(s4_cert[0])
	return [ucs_cert]


def userCert_sync_ucs_to_s4(s4connector, key, ucs_object):
	attr = 'userCertificate'
	try:
		userCertificate = ucs_object['attributes'][attr][0]
	except Exception:
		return
	return [userCertificate]


def jpegPhoto_sync_s4_to_ucs(s4connector, key, s4_object):
	attr = 'jpegPhoto'

	try:
		s4_photo = s4_object['attributes'][attr]
	except Exception:
		return
	ucs_photo = []
	for photo in s4_photo:
		ucs_photo.append(base64.b64encode(photo))
	return ucs_photo


def jpegPhoto_sync_ucs_to_s4(s4connector, key, ucs_object):
	attr = 'jpegPhoto'
	try:
		ucs_photo = ucs_object['attributes'][attr]
	except Exception:
		return
	s4_photo = []
	for photo in ucs_photo:
		s4_photo.append(photo)
	return s4_photo


def secretary_sync_s4_to_ucs(s4connector, key, s4_object):
	attr = 'secretary'
	try:
		s4_secretary = s4_object['attributes'][attr]
	except Exception:
		return
	else:
		ucs_secretary = []
		for s4_dn in s4_secretary:
			dn_mapped = s4_dn
			if s4connector._get_dn_by_con(s4_dn):
				dn_mapped = s4connector._get_dn_by_con(s4_dn)
				dn_mapped = s4connector.dn_mapped_to_base(dn_mapped, s4connector.lo.base)
			if hasattr(s4connector.property[key], 'position_mapping'):
				for mapping in s4connector.property[key].position_mapping:
					dn_mapped = s4connector._subtree_replace(dn_mapped, mapping[1], mapping[0])
				if dn_mapped == s4_dn:
					if not (s4connector.lo.base.lower() == dn_mapped[-len(s4connector.lo.base):].lower() and len(s4connector.lo.base) > len(s4connector.lo_s4.base)):
						dn_mapped = s4connector._subtree_replace(dn_mapped, s4connector.lo_s4.base, s4connector.lo.base)
			ucs_secretary.append(dn_mapped)
		# remove multiples
		ucs_secretary = list(dict.fromkeys(ucs_secretary))
		return ucs_secretary


def secretary_sync_ucs_to_s4(s4connector, key, ucs_object):
	attr = 'secretary'
	try:
		ucs_secretary = ucs_object['attributes'][attr]
	except Exception:
		return
	else:
		s4_secretary = []
		for ucs_dn in ucs_secretary:
			dn_mapped = ucs_dn
			if s4connector._get_dn_by_ucs(ucs_dn):
				dn_mapped = s4connector._get_dn_by_ucs(ucs_dn)
				dn_mapped = s4connector.dn_mapped_to_base(dn_mapped, s4connector.lo_s4.base)
			if hasattr(s4connector.property[key], 'position_mapping'):
				for mapping in s4connector.property[key].position_mapping:
					dn_mapped = s4connector._subtree_replace(dn_mapped, mapping[0], mapping[1])
				if dn_mapped == ucs_dn:
					if not (s4connector.lo_s4.base.lower() == dn_mapped[-len(s4connector.lo_s4.base):].lower() and len(s4connector.lo_s4.base) > len(s4connector.lo.base)):
						dn_mapped = s4connector._subtree_replace(dn_mapped, s4connector.lo.base, s4connector.lo_s4.base)
			s4_secretary.append(dn_mapped)
		# remove multiples
		s4_secretary = list(dict.fromkeys(s4_secretary))
		return s4_secretary
