## TODO
# - add policy manpage
#

# global definitions
%global selinux_variants mls strict targeted
%global selinux_buildreqs checkpolicy selinux-policy-doc hardlink
%global selinux_policyver %(%{__sed} -e 's,.*selinux-policy-\\([^/]*\\)/.*,\\1,' /usr/share/selinux/devel/policyhelp || echo 0.0.0)

Name:       oath-toolkit
Version:    2.4.0
Release:    2%{?dist}
Summary:    The OATH Toolkit
License:    LGPLv2+

Group:      System Environment/Libraries
URL:        http://www.nongnu.org/oath-toolkit
Source0:    %{name}-%{version}.tar.gz
Source1:    %{name}.fc
Source2:    %{name}.if
Source3:    %{name}.te
Source4:    pam_oath.8.gz
BuildRoot:  %(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)
BuildArch:  x86_64

%description
The OATH Toolkit provide components for building one-time password
authentication systems. It contains shared libraries, command line
tools and a PAM module. Supported technologies include the
event-based HOTP algorithm (RFC4226) and the time-based TOTP
algorithm (RFC6238).

%package selinux
Summary:    SELinux policy module supporting OATH for SSH against PAM
License:    LGPLv2+
Requires:   %{name} = %{version}-%{release}
BuildRequires: %{selinux_buildreqs}
%if "%{selinux_policyver}" != ""
Requires:       selinux-policy >= %{selinux_policyver}
%endif
Requires(post):   /usr/sbin/semodule, /sbin/restorecon
Requires(postun): /usr/sbin/semodule, /sbin/restorecon

%description selinux
SELinux policy module supporting OATH for SSH against PAM.

%package -n pam-oath
Summary:    The OATH PAM module
License:    GPLv3+
Requires:   pam
Requires:   %{name} = %{version}-%{release}
BuildRequires:  pam-devel

%description -n pam-oath
A PAM module for pluggable login authentication for OATH.

%package devel
Summary:    The OATH toolkit development files
Requires:   %{name} = %{version}-%{release}

%description devel
This package holds all the development files needed to build
programs, which will use the OATH libraries.

%prep
%setup -q
mkdir SELinux
%{__cp} -p %{S:1} %{S:2} %{S:3} SELinux

%build
# html files already there, ac directive is ignored, so we should delete this
[ -d "liboath/gtk-doc/html" ] && %{__rm} -rf liboath/gtk-doc/html
%configure \
    --enable-pam \
    --disable-pskc \
    --disable-gtk-doc-html \
    --disable-rpath \
    --disable-static \
    --with-pam-dir=/%{_lib}/security

make %{?_smp_mflags}

# SELinux policy module
cd SELinux
for selinuxvariant in %{selinux_variants}
do
  make NAME=${selinuxvariant} -f /usr/share/selinux/devel/Makefile
  mv %{name}.pp %{name}.pp.${selinuxvariant}
  make NAME=${selinuxvariant} -f /usr/share/selinux/devel/Makefile clean
done
cd -

%install
[ "%{buildroot}" != "/" ] && %{__rm} -rf %{buildroot}
make install DESTDIR=%{buildroot}

# delete libtool files
find %{buildroot}/ -type f -name "*.la" -delete

# SELinux policy module
for selinuxvariant in %{selinux_variants}
do
  %{__install} -d %{buildroot}%{_datadir}/selinux/${selinuxvariant}
  %{__install} -p -m 644 SELinux/%{name}.pp.${selinuxvariant} \
    %{buildroot}%{_datadir}/selinux/${selinuxvariant}/%{name}.pp
done
cd -

/usr/sbin/hardlink -cv %{buildroot}%{_datadir}/selinux

# pam_oath
%{__install} -d %{buildroot}%{_mandir}/man8
%{__install} -m 644 %{S:4} %{buildroot}%{_mandir}/man8/

%clean
[ "%{buildroot}" != "/" ] && %{__rm} -rf %{buildroot}

# SELinux policy module
%post selinux
for selinuxvariant in %{selinux_variants}
do
  /usr/sbin/semodule -s ${selinuxvariant} -i \
    %{_datadir}/selinux/${selinuxvariant}/%{name}.pp &> /dev/null || :
done
/sbin/restorecon %{_localstatedir}/cache/%{name} || :

%postun selinux
if [ $1 -eq 0 ] ; then
  for selinuxvariant in %{selinux_variants}
  do
     /usr/sbin/semodule -s ${selinuxvariant} -r %{name} &> /dev/null || :
  done
fi

%post -p /sbin/ldconfig
%postun -p /sbin/ldconfig

%files selinux
%defattr(-,root,root,0755)
%{_datadir}/selinux/*/%{name}.pp

%files -n pam-oath
%defattr(-,root,root,-)
/%{_lib}/security/pam_oath.so
%{_mandir}/man8/*

%files devel
%defattr(-,root,root,-)
%{_includedir}/liboath/oath.h
%{_libdir}/pkgconfig/liboath.pc

%files
%defattr(-,root,root,-)
%doc README NEWS COPYING AUTHORS ChangeLog
%{_bindir}/oathtool
%{_libdir}/liboath.so
%{_libdir}/liboath.so.0
%{_libdir}/liboath.so.0.1.3
%{_mandir}/man3/*
%{_mandir}/man1/*

%changelog
* Sat Aug 31 2013 MegaMaddin <github@megamaddin.org> - 2.4.0-2
- pam_oath manpage added

* Sat Aug 05 2013 MegaMaddin <github@megamaddin.org> - 2.4.0-1
- new upstream release 2.4.0

* Sat Jul 20 2013 MegaMaddin <github@megamaddin.org> - 2.0.2-4
- added SELinux policy module for using OATH with SSH/PAM

* Sat Jul 06 2013 MegaMaddin <github@megamaddin.org> - 2.0.2-3
- cleaned out specfile

* Sat Jul 06 2013 MegaMaddin <github@megamaddin.org> - 2.0.2-2
- fixed some rpmlint failures in specfile

* Sat Jun 29 2013 MegaMaddin <github@megamaddin.org> - 2.0.2-1
- initial rpm distribution
