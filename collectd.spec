Summary: Statistics collection daemon for filling RRD files
Name: collectd
Version: 4.4.4
Release: 1%{?dist}
License: GPLv2
Group: System Environment/Daemons
URL: http://collectd.org/

Source: http://collectd.org/files/%{name}-%{version}.tar.bz2
Patch0: %{name}-%{version}-include-collectd.d.patch
# bug 468067 "pkg-config --libs OpenIPMIpthread" fails
Patch1: %{name}-%{version}-configure-OpenIPMI.patch

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root

BuildRequires: libvirt-devel, libxml2-devel
BuildRequires: rrdtool-devel
BuildRequires: lm_sensors-devel
BuildRequires: curl-devel
%if 0%{?fedora} >= 8
BuildRequires: perl-libs, perl-devel
%else
BuildRequires: perl
%endif
BuildRequires: perl(ExtUtils::MakeMaker)
BuildRequires: perl(ExtUtils::Embed)
BuildRequires: net-snmp-devel
BuildRequires: libpcap-devel
BuildRequires: mysql-devel
BuildRequires: OpenIPMI-devel

%description
collectd is a small daemon written in C for performance.  It reads various
system  statistics  and updates  RRD files,  creating  them if necessary.
Since the daemon doesn't need to startup every time it wants to update the
files it's very fast and easy on the system. Also, the statistics are very
fine grained since the files are updated every 10 seconds.


%package apache
Summary:       Apache plugin for collectd
Group:         System Environment/Daemons
Requires:      collectd = %{version}-%{release}, curl
%description apache
This plugin collects data provided by Apache's 'mod_status'.


%package dns
Summary:       DNS traffic analysis module for collectd
Group:         System Environment/Daemons
Requires:      collectd = %{version}-%{release}
%description dns
This plugin collects DNS traffic data.


%package email
Summary:       Email plugin for collectd
Group:         System Environment/Daemons
Requires:      collectd = %{version}-%{release}, spamassassin
%description email
This plugin collects data provided by spamassassin.


%package ipmi
Summary:       IPMI module for collectd
Group:         System Environment/Daemons
Requires:      collectd = %{version}-%{release}, OpenIPMI
%description ipmi
This plugin for collectd provides IPMI support.


%package mysql
Summary:       MySQL module for collectd
Group:         System Environment/Daemons
Requires:      collectd = %{version}-%{release}, mysql
%description mysql
MySQL querying plugin. This plugins provides data of issued commands,
called handlers and database traffic.


%package nginx
Summary:       Nginx plugin for collectd
Group:         System Environment/Daemons
Requires:      collectd = %{version}-%{release}, curl
%description nginx
This plugin gets data provided by nginx.


%package -n perl-Collectd
Summary:       Perl bindings for collectd
Group:         System Environment/Daemons
Requires:      collectd = %{version}-%{release}
Requires: perl(:MODULE_COMPAT_%(eval "`%{__perl} -V:version`"; echo $version))
%description -n perl-Collectd
This package contains Perl bindings and plugin for collectd.


%package rrdtool
Summary:       RRDTool module for collectd
Group:         System Environment/Daemons
Requires:      collectd = %{version}-%{release}, rrdtool
%description rrdtool
This plugin for collectd provides rrdtool support.


%package sensors
Summary:       Libsensors module for collectd
Group:         System Environment/Daemons
Requires:      collectd = %{version}-%{release}, lm_sensors
%description sensors
This plugin for collectd provides querying of sensors supported by
lm_sensors.


%package snmp
Summary:        SNMP module for collectd
Group:          System Environment/Daemons
Requires:       collectd = %{version}-%{release}, net-snmp
%description snmp
This plugin for collectd provides querying of net-snmp.


%package virt
Summary:       Libvirt plugin for collectd
Group:         System Environment/Daemons
Requires:      collectd = %{version}-%{release}, libvirt
%description virt
This plugin collects information from virtualized guests.


%prep
%setup -q
%patch0 -p1
%patch1 -p0

sed -i.orig -e 's|-Werror||g' Makefile.in */Makefile.in


%build
%configure \
    --without-libiptc \
    --disable-ascent \
    --disable-static \
    --enable-mysql \
    --enable-sensors \
    --enable-email \
    --enable-apache \
    --enable-perl \
    --enable-unixsock \
    --enable-ipmi \
    --with-perl-bindings=INSTALLDIRS=vendor
%{__make} %{?_smp_mflags}


%install
%{__rm} -rf %{buildroot}
%{__rm} -rf contrib/SpamAssassin
%{__make} install DESTDIR="%{buildroot}"

%{__install} -Dp -m0644 src/collectd.conf %{buildroot}%{_sysconfdir}/collectd.conf
%{__install} -Dp -m0755 contrib/fedora/init.d-collectd %{buildroot}%{_initrddir}/collectd

%{__install} -d -m0755 %{buildroot}%{_localstatedir}/lib/collectd/

# Convert docs to UTF-8
find contrib/ -type f -exec %{__chmod} a-x {} \;
for f in contrib/README ChangeLog ; do
  mv $f $f.old; iconv -f iso-8859-1 -t utf-8 < $f.old > $f; rm $f.old
done

# Remove Perl hidden .packlist files.
find %{buildroot} -name .packlist -exec rm {} \;
# Remove Perl temporary file perllocal.pod
find %{buildroot} -name perllocal.pod -exec rm {} \;

# Move the Perl examples to a separate directory.
mkdir perl-examples
find contrib -name '*.p[lm]' -exec mv {} perl-examples/ \;

# Move config contribs
mkdir -p %{buildroot}/etc/collectd.d/
cp contrib/redhat/apache.conf %{buildroot}/etc/collectd.d/apache.conf
cp contrib/redhat/email.conf %{buildroot}/etc/collectd.d/email.conf
cp contrib/redhat/mysql.conf %{buildroot}/etc/collectd.d/mysql.conf
cp contrib/redhat/nginx.conf %{buildroot}/etc/collectd.d/nginx.conf
cp contrib/redhat/sensors.conf %{buildroot}/etc/collectd.d/sensors.conf
cp contrib/redhat/snmp.conf %{buildroot}/etc/collectd.d/snmp.conf

# configs for subpackaged plugins
for p in dns ipmi libvirt perl rrdtool
do
%{__cat} > %{buildroot}/etc/collectd.d/$p.conf <<EOF
LoadPlugin $p
EOF
done


# *.la files shouldn't be distributed.
rm -f %{buildroot}/%{_libdir}/collectd/*.la


%post
/sbin/chkconfig --add collectd


%preun
if [ $1 -eq 0 ]; then
    /sbin/service collectd stop &>/dev/null || :
    /sbin/chkconfig --del collectd
fi


%postun
/sbin/service collectd condrestart &>/dev/null || :


%clean
%{__rm} -rf %{buildroot}


%files
%defattr(-, root, root, -)

%config(noreplace) %{_sysconfdir}/collectd.conf
%config(noreplace) %{_sysconfdir}/collectd.d/
%exclude %{_sysconfdir}/collectd.d/apache.conf
%exclude %{_sysconfdir}/collectd.d/dns.conf
%exclude %{_sysconfdir}/collectd.d/email.conf
%exclude %{_sysconfdir}/collectd.d/ipmi.conf
%exclude %{_sysconfdir}/collectd.d/libvirt.conf
%exclude %{_sysconfdir}/collectd.d/mysql.conf
%exclude %{_sysconfdir}/collectd.d/nginx.conf
%exclude %{_sysconfdir}/collectd.d/perl.conf
%exclude %{_sysconfdir}/collectd.d/rrdtool.conf
%exclude %{_sysconfdir}/collectd.d/sensors.conf
%exclude %{_sysconfdir}/collectd.d/snmp.conf

%{_initrddir}/collectd
%{_bindir}/collectd-nagios
%{_sbindir}/collectd
%{_sbindir}/collectdmon
%dir %{_localstatedir}/lib/collectd/

%{_libdir}/collectd/*.so*
%{_libdir}/collectd/types.db
%exclude %{_libdir}/collectd/apache.so*
%exclude %{_libdir}/collectd/dns.so*
%exclude %{_libdir}/collectd/email.so*
%exclude %{_libdir}/collectd/ipmi.so*
%exclude %{_libdir}/collectd/libvirt.so*
%exclude %{_libdir}/collectd/mysql.so*
%exclude %{_libdir}/collectd/nginx.so*
%exclude %{_libdir}/collectd/perl.so*
%exclude %{_libdir}/collectd/rrdtool.so*
%exclude %{_libdir}/collectd/sensors.so*
%exclude %{_libdir}/collectd/snmp.so*

%doc AUTHORS ChangeLog COPYING INSTALL README
%doc %{_mandir}/man1/collectd.1*
%doc %{_mandir}/man1/collectd-nagios.1*
%doc %{_mandir}/man1/collectdmon.1*
%doc %{_mandir}/man5/collectd.conf.5*
%doc %{_mandir}/man5/collectd-exec.5*
%doc %{_mandir}/man5/collectd-unixsock.5*
%doc %{_mandir}/man5/types.db.5*


%files apache
%defattr(-, root, root, -)
%{_libdir}/collectd/apache.so*
%config(noreplace) %{_sysconfdir}/collectd.d/apache.conf


%files dns
%defattr(-, root, root, -)
%{_libdir}/collectd/dns.so*
%config(noreplace) %{_sysconfdir}/collectd.d/dns.conf


%files email
%defattr(-, root, root, -)
%{_libdir}/collectd/email.so*
%config(noreplace) %{_sysconfdir}/collectd.d/email.conf
%doc %{_mandir}/man5/collectd-email.5*


%files ipmi
%defattr(-, root, root, -)
%{_libdir}/collectd/ipmi.so*
%config(noreplace) %{_sysconfdir}/collectd.d/ipmi.conf


%files mysql
%defattr(-, root, root, -)
%{_libdir}/collectd/mysql.so*
%config(noreplace) %{_sysconfdir}/collectd.d/mysql.conf


%files nginx
%defattr(-, root, root, -)
%{_libdir}/collectd/nginx.so*
%config(noreplace) %{_sysconfdir}/collectd.d/nginx.conf


%files -n perl-Collectd
%defattr(-, root, root, -)
%doc perl-examples/*
%{_libdir}/collectd/perl.so*
%{perl_vendorlib}/Collectd.pm
%{perl_vendorlib}/Collectd/
%config(noreplace) %{_sysconfdir}/collectd.d/perl.conf
%doc %{_mandir}/man5/collectd-perl.5*
%doc %{_mandir}/man3/Collectd::Unixsock.3pm*


%files rrdtool
%defattr(-, root, root, -)
%{_libdir}/collectd/rrdtool.so*
%config(noreplace) %{_sysconfdir}/collectd.d/rrdtool.conf


%files sensors
%defattr(-, root, root, -)
%{_libdir}/collectd/sensors.so*
%config(noreplace) %{_sysconfdir}/collectd.d/sensors.conf


%files snmp
%defattr(-, root, root, -)
%{_libdir}/collectd/snmp.so*
%config(noreplace) %{_sysconfdir}/collectd.d/snmp.conf
%doc %{_mandir}/man5/collectd-snmp.5*


%files virt
%defattr(-, root, root, -)
%{_libdir}/collectd/libvirt.so*
%config(noreplace) %{_sysconfdir}/collectd.d/libvirt.conf


%changelog
* Wed Oct 22 2008 Alan Pevec <apevec@redhat.com> 4.4.4-1
- new upstream bugfix release 4.4.4
  http://collectd.org/news.shtml#news59

* Thu Oct 02 2008 Alan Pevec <apevec@redhat.com> 4.4.3-2
- exclude LoadPlugin email from default config

* Tue Sep 16 2008 Alan Pevec <apevec@redhat.com> 4.4.3-1
- Switch F-9 to 4.4.x stable branch, new upstream bugfix release 4.4.3
  http://collectd.org/news.shtml#news57

* Tue Jul 01 2008 Alan Pevec <apevec@redhat.com> 4.3.3-3
- rebuild for rrdtool update

* Thu Jun 12 2008 Alan Pevec <apevec@redhat.com> 4.3.3-2
- fix sub to main packge dependency

* Thu Jun 12 2008 Alan Pevec <apevec@redhat.com> 4.3.3-1
- New upstream version 4.3.3.
- include /etc/collectd.d (bz#443942)
- cleanup subpackages, split dns plugin

* Tue Jun 10 2008 Chris Lalancette <clalance@redhat.com> - 4.3.2-9
- Split rrdtool into a subpackage.

* Wed Apr 23 2008 Richard W.M. Jones <rjones@redhat.com> - 4.3.2-8
- Added {?dist} to release number (thanks Alan Pevec).

* Wed Apr 23 2008 Richard W.M. Jones <rjones@redhat.com> - 4.3.2-7
- Bump release number so we can tag this in F-9.

* Thu Apr 17 2008 Richard W.M. Jones <rjones@redhat.com> - 4.3.2-6
- Exclude perl.so from the main package.

* Thu Apr 17 2008 Richard W.M. Jones <rjones@redhat.com> - 4.3.2-5
- Put the perl bindings and plugin into a separate perl-Collectd
  package.  Note AFAICT from the manpage, the plugin and Collectd::*
  perl modules must all be packaged together.

* Wed Apr 16 2008 Richard W.M. Jones <rjones@redhat.com> - 4.3.2-4
- Remove -devel subpackage.
- Add subpackages for apache, email, mysql, nginx, sensors,
  snmp (thanks Richard Shade).
- Add subpackages for perl, libvirt.

* Tue Apr 15 2008 Richard W.M. Jones <rjones@redhat.com> - 4.3.2-2
- Install Perl bindings in vendor dir not site dir.

* Tue Apr 15 2008 Richard W.M. Jones <rjones@redhat.com> - 4.3.2-1
- New upstream version 4.3.2.
- Create a -devel subpackage for development stuff, examples, etc.
- Use .bz2 package instead of .gz.
- Remove fix-hostname patch, now upstream.
- Don't mark collectd init script as config.
- Enable MySQL, sensors, email, apache, Perl, unixsock support.
- Don't remove example Perl scripts.
- Package types.db(5) manpage.
- Fix defattr.
- Build in koji to find the full build-requires list.

* Mon Apr 14 2008 Richard W.M. Jones <rjones@redhat.com> - 4.2.3.100.g79b0797-2
- Prepare for Fedora package review:
- Clarify license is GPLv2 (only).
- Setup should be quiet.
- Spelling mistake in original description fixed.
- Don't include NEWS in doc - it's an empty file.
- Convert some other doc files to UTF-8.
- config(noreplace) on init file.

* Thu Jan 10 2008 Chris Lalancette <clalance@redhat.com> - 4.2.3.100.g79b0797.1.ovirt
- Update to git version 79b0797
- Remove *.pm files so we don't get a bogus dependency
- Re-enable rrdtool; we will need it on the WUI side anyway

* Mon Oct 29 2007 Dag Wieers <dag@wieers.com> - 4.2.0-1 - 5946+/dag
- Updated to release 4.2.0.

* Mon Oct 29 2007 Dag Wieers <dag@wieers.com> - 3.11.5-1
- Initial package. (using DAR)
