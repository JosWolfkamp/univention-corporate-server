#!/bin/bash
#
# Copyright 2015-2016 Univention GmbH
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


check_returnvalue ()
{
	rval=$1
	errormessage=$2
	if [ "${rval}" != 0 ]; then
		echo "${errormessage}"
		exit "${rval}"
	fi
}

install_vmware_packages ()
{
	univention-install -y --force-yes open-vm-tools
}

install_virtualbox_packages ()
{
	ucr set repository/online/unmaintained=yes
	univention-install -y --force-yes virtualbox-guest-x11
	ucr set repository/online/unmaintained=no
}

install_activation_packages ()
{
	univention-install -y --force-yes univention-system-activation
	ucr set --force auth/sshd/user/root=yes
}

download_packages ()
{
	mkdir -p /var/cache/univention-system-setup/packages/
	if [ ! -e /etc/apt/sources.list.d/05univention-system-setup.list ]; then
		echo "deb [trusted=yes] file:/var/cache/univention-system-setup/packages/ ./" >>/etc/apt/sources.list.d/05univention-system-setup.list
	fi

	cd /var/cache/univention-system-setup/packages/
	install_cmd="$(univention-config-registry get update/commands/install)"

	for package in "$1"; do
		LC_ALL=C $install_cmd --reinstall -s -o Debug::NoLocking=1 ${package} | 
		apt-get download -o Dir::Cache::Archives=/var/cache/univention-system-setup/packages $(LC_ALL=C $install_cmd --reinstall -s -o Debug::NoLocking=1 ${package} | sed -ne 's|^Inst \([^ ]*\) .*|\1|p')

		check_returnvalue $? "Failed to download required packages for ${package}"
		apt-ftparchive packages . >Packages
		check_returnvalue $? "Failed to create ftparchive directory"
		apt-get update
	done

	return 0
}

app_get_packages ()
{
	local app=$1
	python -c "from univention.management.console.modules.appcenter.app_center import Application; \
				app = Application.find('$app'); \
				print ' '.join(app.get('defaultpackages')+app.get('defaultpackagesmaster'))"
}

app_get_component ()
{
	local app=$1
	python -c "from univention.management.console.modules.appcenter.app_center import Application; \
				app = Application.find('$app'); \
				print app.component_id"
}

app_get_name ()
{
	local app="$1"
	python -c "from univention.management.console.modules.appcenter.app_center import Application; \
				app = Application.find('$app'); \
				print app.name;"
}

app_get_pre_installed_packages ()
{
	local app="$1"
	python -c "from univention.management.console.modules.appcenter.app_center import Application; \
				app = Application.find('$app'); \
				print app.get('AppliancePreInstalledPackages').replace(',',' ');"
}

app_appliance_is_software_blacklisted ()
{
	local app="$1"
	[ -z "$app" ] && return 1
	python -c "
import sys
from univention.management.console.modules.appcenter.app_center import Application
app = Application.find('$app')
bl = app.get('AppliancePagesBlackList')
if bl and 'software' in bl.split(','):
	sys.exit(0)
else:
	sys.exit(1)
"
}

app_get_appliance_additional_apps ()
{
	local app="$1"
	python -c "from univention.management.console.modules.appcenter.app_center import Application; \
				app = Application.find('$app'); \
				print app.get('ApplianceAdditionalApps').replace(',',' ');"
}

appliance_dump_memory ()
{
	local app="$1"
	local targetfile="$2"
	python -c "
from univention.management.console.modules.appcenter.app_center import Application
app = Application.find('$app')
if app.get('ApplianceMemory'):
	print app.get('ApplianceMemory')
else:
	print '1024'" >"$targetfile"
}

register_apps ()
{
	app=$1
	apps="$app $(app_get_appliance_additional_apps $app)"

	for the_app in $apps; do
		name=$(app_get_name $the_app)
		component=$(app_get_component $the_app)
		component_prefix="repository/online/component/"
		ucr set ${component_prefix}${component}description="$name" \
				${component_prefix}${component}/localmirror=false \
				${component_prefix}${component}/server="$(ucr get repository/app_center/server)" \
				${component_prefix}${component}/unmaintained=disabled \
				${component_prefix}${component}/version=current \
				${component_prefix}${component}=enabled
		if [ -e "/var/cache/univention-appcenter/${component}.LICENSE_AGREEMENT" ]; then
			ucr set umc/web/appliance/data_path?"/var/cache/univention-appcenter/${component}."
		fi
	done

	ucr set umc/web/appliance/id?${app}
	univention-install -y univention-app-appliance

	apt-get update
}

install_pre_packages ()
{
	app=$1

	packages="$(app_get_pre_installed_packages $app)"
	if [ -n "$packages" ]; then
		DEBIAN_FRONTEND=noninteractive apt-get -y install $packages
	fi
}

download_packages_and_dependencies ()
{
	app=$1

	apps="$app $(app_get_appliance_additional_apps $app)"

	mkdir -p /var/cache/univention-system-setup/packages/
	if [ ! -e /etc/apt/sources.list.d/05univention-system-setup.list ]; then
		echo "deb [trusted=yes] file:/var/cache/univention-system-setup/packages/ ./" >>/etc/apt/sources.list.d/05univention-system-setup.list
	fi

	cd /var/cache/univention-system-setup/packages/
	install_cmd="$(univention-config-registry get update/commands/install)"

	for app in $apps; do
		packages="$(app_get_packages $app)"
		echo "Try to download: $packages"
		for package in $packages; do
			LC_ALL=C $install_cmd --reinstall -s -o Debug::NoLocking=1 ${package} | 
			apt-get download -o Dir::Cache::Archives=/var/cache/univention-system-setup/packages $(LC_ALL=C $install_cmd --reinstall -s -o Debug::NoLocking=1 ${package} | sed -ne 's|^Inst \([^ ]*\) .*|\1|p')

			check_returnvalue $? "Failed to download required packages for ${package}"
		done
		apt-ftparchive packages . >Packages
		check_returnvalue $? "Failed to create ftparchive directory"
		apt-get update
	done

	return 0
}

download_system_setup_packages ()
{
	app="$1"

	echo "download_system_setup_packages for $app"

	mkdir -p /var/cache/univention-system-setup/packages/
	(
		if [ ! -e /etc/apt/sources.list.d/05univention-system-setup.list ]; then
			echo "deb [trusted=yes] file:/var/cache/univention-system-setup/packages/ ./" >>/etc/apt/sources.list.d/05univention-system-setup.list
		fi

		cd /var/cache/univention-system-setup/packages/
		install_cmd="$(univention-config-registry get update/commands/install)"

		# server role packages
		packages="server-master server-backup server-slave server-member basesystem"

		# ad member mode
		packages="$packages ad-connector samba welcome-screen"

		if ! app_appliance_is_software_blacklisted $app; then
			packages="$packages management-console-module-adtakeover printserver dhcp fetchmail kde radius virtual-machine-manager-node-kvm mail-server nagios-server pkgdb samba4 s4-connector squid virtual-machine-manager-daemon self-service self-service-passwordreset-umc"
		fi

		for package in $packages; do
			LC_ALL=C $install_cmd --reinstall -s -o Debug::NoLocking=1 univention-${package} | 
			apt-get download -o Dir::Cache::Archives=/var/cache/univention-system-setup/packages $(LC_ALL=C $install_cmd --reinstall -s -o Debug::NoLocking=1 univention-${package} | sed -ne 's|^Inst \([^ ]*\) .*|\1|p')

			check_returnvalue $? "Failed to download required packages for univention-${package}"

			apt-ftparchive packages . >Packages
			check_returnvalue $? "Failed to create ftparchive directory"
			apt-get update
		done

		#for package in firefox-en; do
		#	LC_ALL=C $install_cmd --reinstall -s -o Debug::NoLocking=1 ${package} | 
		#	apt-get download -o Dir::Cache::Archives=/var/cache/univention-system-setup/packages $(LC_ALL=C $install_cmd --reinstall -s -o Debug::NoLocking=1 ${package} | sed -ne 's|^Inst \([^ ]*\) .*|\1|p')

		#	check_returnvalue $? "Failed to download required packages for ${package}"
		#done

		apt-ftparchive packages . >Packages
		check_returnvalue $? "Failed to create ftparchive directory"
	)
}

create_install_script ()
{
	main_app=$1

	apps="$main_app $(app_get_appliance_additional_apps $main_app)"

	packages=""
	for app in $apps; do
		packages="$packages $(app_get_packages $app)"
	done
	# Due to dovect: https://forge.univention.org/bugzilla/show_bug.cgi?id=39148
	if [ "$main_app" = "oxseforucs" ] || [ "$main_app" = "egroupware" ] || [ "$main_app" = "horde" ] || [ "$main_app" = "tine20" ] || [ "$main_app" = "fortnox" ]; then
		close_fds=TRUE
	fi
	# Ticket #2015052821000587
	if [ "$main_app" = "kolab-enterprise" ]; then
		close_fds=TRUE
	fi
	
	cat >/usr/lib/univention-install/99_setup_${main_app}.inst <<__EOF__
#!/bin/sh
. /usr/share/univention-join/joinscripthelper.lib
VERSION="1"
joinscript_init
eval "\$(ucr shell update/commands/install)"
export DEBIAN_FRONTEND=noninteractive
apt-get update
if [ "$close_fds" = "TRUE" ]; then
	echo "Close logfile output now. Please see /var/log/dpkg.log for more information"
	exec 1> /dev/null
	exec 2> /dev/null
fi
\$update_commands_install -y --force-yes -o="APT::Get::AllowUnauthenticated=1;" $packages || die
joinscript_save_current_version
univention-register-apps
if [ \$# -gt 1 ]; then
	. /usr/share/univention-lib/ldap.sh

	ucs_parseCredentials "\$@"
	dcaccount="\$(echo "\$binddn" | sed -ne 's|uid=||;s|,.*||p')"
	dcpwd="\$(mktemp)"
	echo -n "\$bindpwd" >\$dcpwd
	univention-run-join-scripts -dcaccount "\$dcaccount" -dcpwd "\$dcpwd"

	rm \$dcpwd
	unset binddn
	unset bindpwd

else
	univention-run-join-scripts
fi
invoke-rc.d ntp restart

# Use the first template as default (Bug #38832)
if [ -e /usr/share/univention-management-console-frontend/js/umc/modules/udm/wizards/FirstPageWizard.js ]; then
	sed -i 's|templates.unshift(|templates.push(|' /usr/share/univention-management-console-frontend/js/umc/modules/udm/wizards/FirstPageWizard.js
	. /usr/share/univention-lib/umc.sh
	umc_frontend_new_hash
fi
__EOF__
	chmod 755 /usr/lib/univention-install/99_setup_${main_app}.inst

}

install_app_in_prejoined_setup ()
{
	eval "$(ucr shell update/commands/install)"
	export DEBIAN_FRONTEND=noninteractive

	packages=""
	for app in $apps; do
		packages="$packages $(app_get_packages $app)"
	done

	$update_commands_install -y --force-yes -o="APT::Get::AllowUnauthenticated=1;" $packages

	univention-run-join-scripts
}

appliance_preinstall_non_univention_packages ()
{
	packages="	texlive-doc-base
			heimdal-clients
			libfile-copy-recursive-perl
			update-inetd
			openbsd-inetd
			libcap-ng0
			heimdal-kdc
			quota
			libslp1
			slapd
			nagios-plugins-common
			liblockfile-bin
			rpcbind
			nfs-common
			python-egenix-mxtools
			python-egenix-mxdatetime
			libpq5
			python-pygresql
			bc
			libblas3
			liblinear1
			nmap
			libsnmp-session-perl
			mrtg
			wamerican
			pam-runasroot
			nscd
			libnss-extrausers
			libdaemon0
			ifplugd
			nfs-kernel-server
			libopts25
			ntp
			bind9utils
			bind9
			libgraphite3
			libkpathsea6
			libptexenc1
			tex-common
			texlive-common
			ed
			texlive-binaries
			xdg-utils
			luatex
			ttf-marvosym
			preview-latex-style
			mysql-common
			libyaml-syck-perl
			lmodern
			nagios-nrpe-server
			tex-gyre
			freeipmi-common
			nagios-plugins-basic
			dpt-i2o-raidutils
			libfsplib0
			elinks-data
			elinks
			libotf0
			m17n-db
			m17n-contrib
			libm17n-0
			fonts-liberation
			fping
			gnuplot-nox
			groff
			libconfig-tiny-perl
			libdate-manip-perl
			libfile-basedir-perl
			libfile-desktopentry-perl
			libfile-mimeinfo-perl
			libsocket6-perl
			libio-socket-inet6-perl
			liblinear-tools
			liblwp-useragent-determined-perl
			libparse-recdescent-perl
			libmail-imapclient-perl
			libmath-calc-units-perl
			libparams-classify-perl
			libmodule-runtime-perl
			libtry-tiny-perl
			libmodule-implementation-perl
			libparams-validate-perl
			libnagios-plugin-perl
			libxml-twig-perl
			libnet-dbus-perl
			libnet-smtp-tls-perl
			libnet-snmp-perl
			libradiusclient-ng2
			libreadonly-perl
			libreadonly-xs-perl
			libruby1.9.1
			libsnmp-base
			libsnmp15
			libutempter0
			libx11-protocol-perl
			libxml-xpathengine-perl
			locate
			postgresql-client-common
			postgresql-client-9.1
			postgresql-client
			ps2eps
			psutils
			raidutils
			ruby1.9.1
			ruby
			snmp
			tcl8.5
			tk8.5
			nagios-plugins-standard
			nagios-plugins
			vim-runtime
			vim
			x11-xserver-utils
			xbitmaps
			xterm
			zip
			libfreeipmi12
			libipmiconsole2
			libipmidetect0
			freeipmi-tools
			nagios-plugins-contrib
			texlive-base
			gnuplot
			libsvm-tools
			texlive-extra-utils
			texlive-font-utils
			texlive-luatex
			texlive-latex-base
			texlive-fonts-recommended
			texlive-pictures
			texlive-lang-german
			texlive-generic-recommended
			tipa
			texlive-latex-recommended
			texlive-pstricks
			texlive
			texlive-latex-extra
			latex-xcolor
			prosper
			pgf
			latex-beamer
			heimdal-servers
			gettext
			patch
		"
	for p in $packages; do
		DEBIAN_FRONTEND=noninteractive apt-get -y install --no-install-recommends "$p"
	done
}

install_haveged ()
{
    _unmaintained_setting=$(ucr get repository/online/unmaintained)
    ucr set repository/online/unmaintained="yes"
    univention-install -y haveged
    ucr set repository/online/unmaintained="$_unmaintained_setting"
}

uninstall_packages ()
{
	# if upgraded, u-basesystem will be installed by postup.sh
	state="$(dpkg --get-selections univention-basesystem 2>/dev/null | awk '{print $2}')"
	if [ "$state" = "install" ]; then
		apt-get purge -y --force-yes univention-basesystem
		apt-get -y --force-yes autoremove
	fi

	# Old kernels
	apt-get purge -y --force-yes linux-image-4.1.0-ucs153-amd64 linux-image-4.1.0-ucs153-amd64-signed
}

setup_pre_joined_environment ()
{
	cat >/var/cache/univention-system-setup/profile <<__EOF__
hostname="master"
domainname="ucs.example"
server/role="domaincontroller_master"
locale="de_DE.UTF-8:UTF-8 en_US.UTF-8:UTF-8"
interfaces/eth0/type="static"
timezone="Europe/Berlin"
gateway="10.203.0.1"
ssl/organizationalunit="Univention Corporate Server"
windows/domain="UCS"
packages_install=""
interfaces/eth0/start="true"
ad/member="False"
xorg/keyboard/options/XkbLayout="de"
interfaces/primary="eth0"
interfaces/eth0/broadcast="10.203.255.255"
packages_remove=""
ssl/organization="DE"
root_password="zRMtAmGIb3"
ssl/email="ssl@ucs.example"
ldap/base="dc=ucs,dc=example"
locale/default="de_DE.UTF-8:UTF-8"
nameserver1="192.168.0.3"
ssl/state="DE"
interfaces/eth0/ipv6/acceptRA="false"
ssl/locality="DE"
interfaces/eth0/netmask="255.255.0.0"
interfaces/eth0/network="10.203.0.0"
update/system/after/setup="True"
components=""
interfaces/eth0/address="10.203.10.40"
__EOF__
	/usr/lib/univention-system-setup/scripts/setup-join.sh 2>&1 | tee /var/log/univention/setup.log
}

setup_appliance ()
{
	# Stop firefox. Not required to run, and resets some UCRv (e.g. system/setup/boot/start)
	pkill -f /opt/firefox/firefox

	# allow X11 login as normal user
	ucr set "auth/gdm/group/Domain Users"=yes
	 
	# Disable xorg autodetection and set resolution to 800x600 for system setup
	ucr set xorg/autodetect=no \
	xorg/device/driver='' \
	xorg/resolution=800x600
	 
	# Disable kernel mode set
	ucr set grub/append="nomodeset $(ucr get grub/append)"
	 
	# Show bootscreen in 800x600
	ucr set grub/gfxmode=800x600@16
	 
	# generate all UMC languages
	ucr set locale/default="en_US.UTF-8:UTF-8" locale="en_US.UTF-8:UTF-8 de_DE.UTF-8:UTF-8"; locale-gen

	install_haveged

	uninstall_packages

	univention-install -y --force-yes --reinstall univention-system-setup-boot
	univention-install -y --no-install-recommends univention-x-core

	# shrink appliance image size
	appliance_preinstall_non_univention_packages
	rm /etc/apt/sources.list.d/05univention-system-setup.list
	rm -r /var/cache/univention-system-setup/packages/

	apt-get update
	download_system_setup_packages $@

	# Cleanup apt archive
	apt-get clean
	apt-get update

	# set initial system uuid (set to new value in setup-join.sh)
	ucr set uuid/system="00000000-0000-0000-0000-000000000000"
}

appliance_cleanup ()
{
	# fix appcenter icons
	cat >/usr/lib/univention-system-setup/appliance-hooks.d/commit-apps-xml <<__EOF__
#!/bin/sh
python -c "import univention.management.console.modules.appcenter as ac; ac.Application._update_local_files()"
ucr commit /usr/share/univention-management-console/modules/apps.xml
__EOF__
	chmod 755 /usr/lib/univention-system-setup/appliance-hooks.d/commit-apps-xml
	 
	# Ensure dbus will be restated after the configuration
	cat >/usr/lib/univention-system-setup/appliance-hooks.d/dbus <<__EOF__
#!/bin/sh
test -x /etc/init.d/dbus && /etc/init.d/dbus restart
__EOF__
	chmod +x /usr/lib/univention-system-setup/appliance-hooks.d/dbus
	 
	## UCS4: 
	# after system setup is finished, boot in 1024x768 (not 800x600)
	cat >/usr/lib/univention-system-setup/appliance-hooks.d/screenresolution <<__EOF__
#!/bin/sh
ucr set grub/gfxmode=1024x768@16 \
	xorg/resolution=1024x768
__EOF__
	chmod +x /usr/lib/univention-system-setup/appliance-hooks.d/screenresolution

	# deactivate kernel module; prevents bootsplash from freezing in vmware
	ucr set kernel/blacklist="$(ucr get kernel/blacklist);vmwgfx"
	 
	# Show an info that the domain setup might take a while (Bug #38833)
	sed -i 's|info_header "domain-join" "$(gettext "Domain join")"|info_header "domain-join" "$(gettext "Domain setup (this might take a while)")"|' \
			/usr/lib/univention-system-setup/scripts/setup-join.sh
	sed -i 's|msgid "Domain join"|msgid "Domain setup (this might take a while)"|' /usr/share/locale/de/LC_MESSAGES/univention-system-setup-scripts.po
	sed -i 's|msgstr "Domänenbeitritt"|msgstr "Domäneneinrichtung (Dies kann einige Zeit dauern)"|' /usr/share/locale/de/LC_MESSAGES/univention-system-setup-scripts.po
	msgfmt -o /usr/share/locale/de/LC_MESSAGES/univention-system-setup-scripts.mo /usr/share/locale/de/LC_MESSAGES/univention-system-setup-scripts.po

	# re-create dh parameter as background job (Bug #37459)
	cat >/root/dh-parameter-background.patch <<'__EOF__'
--- /usr/lib/univention-system-setup/scripts/setup-join.sh	(Revision 61517)
+++ /usr/lib/univention-system-setup/scripts/setup-join.sh	(Arbeitskopie)
@@ -157,20 +157,10 @@
 	fi
 	progress_next_step 3
 
-	(
 	test -x /usr/share/univention-mail-postfix/create-dh-parameter-files.sh && \
-		/usr/share/univention-mail-postfix/create-dh-parameter-files.sh
-	) | (
-		nsteps=3
-		while read line; do
-			if [ "This is going to take a long time" == "$line" ]; then
-				# one of 2 SSH keys is generated
-				progress_next_step $nsteps
-				nsteps+=2
-			fi
-		done
-	)
-	progress_next_step 10
+		/usr/share/univention-mail-postfix/create-dh-parameter-files.sh >>/var/log/univention/dh-parameter-files-creation.log 2>&1 &
+
+	progress_next_step 15
 fi
__EOF__
	patch -d/ -p0 </root/dh-parameter-background.patch
	rm /root/dh-parameter-background.patch
 
 # Do network stuff

	# set initial values for UCR ssl variables
	/usr/sbin/univention-certificate-check-validity

	# Set official update server, deactivate online repository until system setup script 90_postjoin/20upgrade
	ucr set repository/online=no \
		repository/online/server='https://updates.software-univention.de'
	# ucr set repository/online/server=univention-repository.knut.univention.de

	# Cleanup apt archive
	apt-get update
	apt-get clean

	# Activate DHCP
	ucr set interfaces/eth0/type=dhcp dhclient/options/timeout=12
	ucr unset gateway
	 
	# Set a default nameserver and remove all local configured nameserver
	ucr set nameserver1=208.67.222.222 dns/forwarder1=208.67.222.222
	ucr unset nameserver2 nameserver3
	ucr unset dns/forwarder2 dns/forwarder3

	# Manual cleanup
	rm -rf /tmp/*
	rm /var/log/installer/cdebconf/*
	for dir in "python-cherrypy3 libwibble-dev texlive-base texlive-lang-german texmf texlive-latex-recommended groff-base libept-dev"; do
		[ -d /usr/share/doc/$dir ] && rm -rf /usr/share/doc/$dir
	done

	# fill up HDD with ZEROs to maximize possible compression
	dd if=/dev/zero of=/fill-it-up bs=1M; rm /fill-it-up

	# Remove persistent net rule
	rm -f /etc/udev/rules.d/70-persistent-net.rules
	 
	ucr set system/setup/boot/start=true
}



appliance_basesettings ()
{
	set -x
	app=$1
	
	/usr/sbin/univention-app-appliance $app

	app_fav_list=""
	for a in $apps; do
		app_fav_list="$app_fav_list,apps:$a"
	done
	
	# App as UMC favourite for administrator user
	cat >/usr/lib/univention-system-setup/appliance-hooks.d/umc-favorites <<__EOF__
#!/bin/bash
eval "\$(ucr shell)"
old_fav=\$(udm users/user list --dn "uid=Administrator,cn=users,\$ldap_base" | grep "^  umcProperty: favorites = " | awk '{print \$4}')
test -z "\$old_fav" && old_fav="udm:users/user,udm:groups/group,appcenter,updater"
fav="favorites \$old_fav$app_fav_list"
udm users/user modify --dn "uid=Administrator,cn=users,\$ldap_base" --set umcProperty="\$fav"
__EOF__
	chmod 755 /usr/lib/univention-system-setup/appliance-hooks.d/umc-favorites

	# Fixes for BETA appliances
	if [ "$app" = "zarafa" ]; then
		sed -i 's|ucr set zarafa/webapp/config/DEFAULT_SERVER?|ucr set zarafa/webapp/config/DEFAULT_SERVER=|' /usr/lib/univention-install/71zarafa4ucs-webapp.inst
		cat >/usr/lib/univention-system-setup/appliance-hooks.d/99_set_webapp_server <<__EOF__
#!/bin/bash
ucr set zarafa/webapp/config/DEFAULT_SERVER=\"https://\$(ucr get hostname).\$(ucr get domainname):237/zarafa\"
__EOF__
		
		chmod 755 /usr/lib/univention-system-setup/appliance-hooks.d/99_set_webapp_server
	fi
	if [ "$app" = "owncloud82" ]; then
		cat >/usr/lib/univention-system-setup/appliance-hooks.d/99_fix_owncloud_trusted_domains <<__EOF__
#!/bin/bash

ips="\$(python  -c "
from univention.config_registry.interfaces import Interfaces
for name, iface in Interfaces().all_interfaces: print iface.get('address')")"

HOSTS="'\$(ucr get hostname).\$(ucr get domainname)',"

for ip in \$ips; do
	HOSTS="\${HOSTS}'\${ip}',"
done

cd /var/www/owncloud/config
(
echo '<?php'
echo -ne '\$CONFIG = '
php -r "include('config.php'); \\\$CONFIG['trusted_domains'] = array(\$HOSTS); var_export(\\\$CONFIG);"
echo ';'
) > config.php.updated
mv -f config.php.updated config.php
chown www-data:www-data config.php
__EOF__
	chmod 755 /usr/lib/univention-system-setup/appliance-hooks.d/99_fix_owncloud_trusted_domains
	fi
}

install_appreport ()
{
	ucr set repository/online/component/appreport=yes \
		repository/online/component/appreport/version="current"
	cat >/usr/lib/univention-system-setup/appliance-hooks.d/install-appreport <<__EOF__
#!/bin/sh
univention-install -y --force-yes univention-appreport
__EOF__
	chmod +x /usr/lib/univention-system-setup/appliance-hooks.d/install-appreport
}

appliance_reset_servers ()
{
	ucr set repository/online/server="https://updates.software-univention.de/"

	# ucr search --brief --value "^appcenter-test.software-univention.de$" | sed -ne 's|: .*||p' | while read key; do
	# 	ucr set "$key=appcenter.software-univention.de"
	# done

	# Cleanup /etc/apt/sources.list in case any modifications were done
	cat >/etc/apt/sources.list <<__EOF__
# This file is not maintained via Univention Configuration Registry
# and can be used to add further package repositories manually
__EOF__
}

disable_root_login_and_poweroff ()
{
	# ucr set --force auth/sshd/user/root=no
	rm /root/*
	rm /root/.bash_history
	history -c
	halt -p
}

appliance_poweroff ()
{
	rm /root/*
	rm /root/.bash_history
	history -c
	halt -p
}
