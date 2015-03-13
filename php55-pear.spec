
%global peardir %{_datadir}/pear
%define basepkg php55

%global xmlrpcver 1.5.5
%global getoptver 1.3.1
%global arctarver 1.3.11
%global structver 1.0.4
%global xmlutil   1.2.1

Summary: PHP Extension and Application Repository framework
Name: %{basepkg}-pear
Version: 1.9.4
Release: 1%{?dist}
Epoch: 1
# PEAR, Archive_Tar, XML_Util are BSD
# XML-RPC, Console_Getopt are PHP
# Structures_Graph is LGPLv2+
License: BSD and PHP and LGPLv2+
Group: Development/Languages
URL: http://pear.php.net/package/PEAR
Source0: http://download.pear.php.net/package/PEAR-%{version}.tgz
# wget https://raw.github.com/pear/pear-core/master/install-pear.php -O install-pear.php
Source1: install-pear.php
Source2: relocate.php
Source3: strip.php
Source4: LICENSE
Source5: LICENSE-XML_RPC
Source10: pear.sh
Source11: pecl.sh
Source12: peardev.sh
Source13: macros.pear
Source20: http://pear.php.net/get/XML_RPC-%{xmlrpcver}.tgz
Source21: http://pear.php.net/get/Archive_Tar-%{arctarver}.tgz
Source22: http://pear.php.net/get/Console_Getopt-%{getoptver}.tgz
Source23: http://pear.php.net/get/Structures_Graph-%{structver}.tgz
Source24: http://pear.php.net/get/XML_Util-%{xmlutil}.tgz
Patch0: php-pear-1.9.4-restcache.patch
BuildArch: noarch
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires: %{basepkg}-cli >= 5.1.0-1, %{basepkg}-xml, gnupg
Provides: php-pear(Console_Getopt) = %{getoptver}
Provides: php-pear(Archive_Tar) = %{arctarver}
Provides: php-pear(PEAR) = %{version}
Provides: php-pear(Structures_Graph) = %{structver}
Provides: php-pear(XML_RPC) = %{xmlrpcver}
Provides: php-pear(XML_Util) = %{xmlutil}
Obsoletes: php-pear-XML-Util <= %{xmlutil}
# Hold release string in legacy provide, since XML_Util has not changed:
Provides:  php-pear-XML-Util = %{xmlutil}-2%{?dist}
Requires: %{basepkg}-cli >= 5.1.0-1
Provides: php-pear = %{version}

%description
PEAR is a framework and distribution system for reusable PHP
components.  This package contains the basic PEAR components.

%prep
%setup -cT

# Create a usable PEAR directory (used by install-pear.php)
for archive in %{SOURCE0} %{SOURCE21} %{SOURCE22} %{SOURCE23} %{SOURCE24}
do
    tar xzf  $archive --strip-components 1 || tar xzf  $archive --strip-path 1
    file=${archive##*/}
    [ -f LICENSE ] && mv LICENSE LICENSE-${file%%-*}
    [ -f README ]  && mv README  README-${file%%-*}
done
tar xzf %{SOURCE24} package.xml
mv package.xml XML_Util.xml

# apply patches on used PEAR during install
# - no patch

%build
# This is an empty build section.

%install
rm -rf $RPM_BUILD_ROOT

export PHP_PEAR_SYSCONF_DIR=%{_sysconfdir}
export PHP_PEAR_SIG_KEYDIR=%{_sysconfdir}/pearkeys
export PHP_PEAR_SIG_BIN=%{_bindir}/gpg
export PHP_PEAR_INSTALL_DIR=%{peardir}

# 1.4.11 tries to write to the cache directory during installation
# so it's not possible to set a sane default via the environment.
# The ${PWD} bit will be stripped via relocate.php later.
export PHP_PEAR_CACHE_DIR=${PWD}%{_localstatedir}/cache/php-pear
export PHP_PEAR_TEMP_DIR=/var/tmp

install -d $RPM_BUILD_ROOT%{peardir} \
           $RPM_BUILD_ROOT%{_localstatedir}/cache/php-pear \
           $RPM_BUILD_ROOT%{_localstatedir}/www/html \
           $RPM_BUILD_ROOT%{peardir}/.pkgxml \
           $RPM_BUILD_ROOT%{_sysconfdir}/rpm \
           $RPM_BUILD_ROOT%{_sysconfdir}/pear

export INSTALL_ROOT=$RPM_BUILD_ROOT

%{_bindir}/php -n -dmemory_limit=32M -dshort_open_tag=0 -dsafe_mode=0 \
         -derror_reporting=E_ALL -ddetect_unicode=0 \
      %{SOURCE1} -d %{peardir} \
                 -c %{_sysconfdir}/pear \
                 -b %{_bindir} \
                 -w %{_localstatedir}/www/html \
                 %{SOURCE0} %{SOURCE21} %{SOURCE22} %{SOURCE23} %{SOURCE24} %{SOURCE20}

# Replace /usr/bin/* with simple scripts:
install -m 755 %{SOURCE10} $RPM_BUILD_ROOT%{_bindir}/pear
install -m 755 %{SOURCE11} $RPM_BUILD_ROOT%{_bindir}/pecl
install -m 755 %{SOURCE12} $RPM_BUILD_ROOT%{_bindir}/peardev

# Sanitize the pear.conf
%{_bindir}/php -n %{SOURCE2} $RPM_BUILD_ROOT%{_sysconfdir}/pear.conf $RPM_BUILD_ROOT | 
  %{_bindir}/php -n %{SOURCE2} php://stdin $PWD > new-pear.conf
%{_bindir}/php -n %{SOURCE3} new-pear.conf ext_dir |
  %{_bindir}/php -n %{SOURCE3} php://stdin http_proxy > $RPM_BUILD_ROOT%{_sysconfdir}/pear.conf

%{_bindir}/php -r "print_r(unserialize(substr(file_get_contents('$RPM_BUILD_ROOT%{_sysconfdir}/pear.conf'),17)));"

install -m 644 -c %{SOURCE4} LICENSE
install -m 644 -c %{SOURCE5} LICENSE-XML_RPC

install -m 644 -c %{SOURCE13} \
           $RPM_BUILD_ROOT%{_sysconfdir}/rpm/macros.pear     

# apply patches on installed PEAR tree
pushd $RPM_BUILD_ROOT%{peardir} 
 pushd PEAR
  %__patch -s --no-backup --fuzz 0 -p0 < %{PATCH0}
 popd
popd

# Why this file here ?
rm -rf $RPM_BUILD_ROOT/.depdb* $RPM_BUILD_ROOT/.lock $RPM_BUILD_ROOT/.channels $RPM_BUILD_ROOT/.filemap

# Need for re-registrying XML_Util
install -m 644 XML_Util.xml $RPM_BUILD_ROOT%{peardir}/.pkgxml/


%check
# Check that no bogus paths are left in the configuration, or in
# the generated registry files.
grep $RPM_BUILD_ROOT $RPM_BUILD_ROOT%{_sysconfdir}/pear.conf && exit 1
grep %{_libdir} $RPM_BUILD_ROOT%{_sysconfdir}/pear.conf && exit 1
grep '"/tmp"' $RPM_BUILD_ROOT%{_sysconfdir}/pear.conf && exit 1
grep /usr/local $RPM_BUILD_ROOT%{_sysconfdir}/pear.conf && exit 1
grep -rl $RPM_BUILD_ROOT $RPM_BUILD_ROOT && exit 1


%clean
rm -rf $RPM_BUILD_ROOT
rm new-pear.conf


%triggerpostun -- php-pear-XML-Util
# re-register extension unregistered during postun of obsoleted php-pear-XML-Util
%{_bindir}/pear install --nodeps --soft --force --register-only %{pear_xmldir}/XML_Util.xml >/dev/null || :


%files
%defattr(-,root,root,-)
%{peardir}
%{_bindir}/*
%config(noreplace) %{_sysconfdir}/pear.conf
%config %{_sysconfdir}/rpm/macros.pear
%dir %{_localstatedir}/cache/php-pear
%dir %{_localstatedir}/www/html
%dir %{_sysconfdir}/pear
%doc README* LICENSE*


%changelog
* Sun Jul 14 2013 Andy Thompson <andy@webtatic.com> 1.9.4-7
- Update shell scripts to work with ini-loaded modules.

* Sat May 18 2013 Andy Thompson <andy@webtatic.com> 1.9.4-6
- fork php54w-pear
- update basepkg to php55w
