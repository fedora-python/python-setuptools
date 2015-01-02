%if 0%{?fedora}
%global with_python2 0
%global with_python3 1

%{?scl:%global py3dir %{_builddir}/python3-%{name}-%{version}-%{release}}

# This controls whether setuptools is build as a wheel or not,
# simplifying Python 3.4 bootstraping process
%global build_wheel 1
%else
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print (get_python_lib())")}
%endif

%{?scl:%scl_package python-setuptools}
%{!?scl:%global pkg_name %{name}}

%global srcname setuptools
%if 0%{?build_wheel}
%global python2_wheelname %{srcname}-*-py2.py3-none-any.whl
%global python2_record %{python2_sitelib}/%{srcname}-*.dist-info/RECORD
%if 0%{?with_python3}
%global python3_wheelname %python2_wheelname
%global python3_record %{python3_sitelib}/%{srcname}-*.dist-info/RECORD
%endif
%endif

Name:           %{?scl_prefix}python-setuptools
Version:        7.1
Release:        0.53.20150102hgaa23c45dbab3%{?dist}
Summary:        Easily build and distribute Python packages

Group:          Applications/System
License:        Python or ZPLv2.0
URL:            http://pypi.python.org/pypi/%{srcname}
Source0:        python3-nightly-setuptools-aa23c45dbab3.tar
Source1:        psfl.txt
Source2:        zpl.txt

BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch
# Require this so that we use a system copy of the match_hostname() function
#Requires: python-backports-ssl_match_hostname
#BuildRequires: python-backports-ssl_match_hostname
%if 0%{?with_python2}
BuildRequires:  python2-devel
%if 0%{?build_wheel}
BuildRequires:  python-pip
BuildRequires:  python-wheel
%endif
%endif # if with_python2
%if 0%{?with_python3}
BuildRequires:  %{?scl_prefix}python3-devel
%if 0%{?build_wheel}
BuildRequires:  %{?scl_prefix}python3-pip
BuildRequires:  %{?scl_prefix}python3-wheel
%endif
%endif # if with_python3
# For unittests
BuildRequires: subversion


%if 0%{?with_python2}
# We're now back to setuptools as the package.
# Keep the python-distribute name active for a few releases.  Eventually we'll
# want to get rid of the Provides and just keep the Obsoletes
Provides: %{?scl_prefix}python-distribute = %{version}-%{release}
Obsoletes: %{?scl_prefix}python-distribute < 0.6.36-2
%endif # if with_python2

%description
Setuptools is a collection of enhancements to the Python distutils that allow
you to more easily build and distribute Python packages, especially ones that
have dependencies on other packages.

This package also contains the runtime components of setuptools, necessary to
execute the software that requires pkg_resources.py.

%if 0%{?with_python3}
%package -n %{?scl_prefix}python3-setuptools
Summary:        Easily build and distribute Python 3 packages
Group:          Applications/System

# Note: Do not need to Require python3-backports-ssl_match_hostname because it
# has been present since python3-3.2.  We do not ship python3-3.0 or
# python3-3.1 anywhere

%description -n %{?scl_prefix}python3-setuptools
Setuptools is a collection of enhancements to the Python 3 distutils that allow
you to more easily build and distribute Python 3 packages, especially ones that
have dependencies on other packages.

This package also contains the runtime components of setuptools, necessary to
execute the software that requires pkg_resources.py.

%endif # with_python3

%prep
%setup -q -n python3-nightly-%{srcname}

find -name '*.txt' -exec chmod -x \{\} \;
find . -name '*.orig' -exec rm \{\} \;

%if 0%{?with_python3}
rm -rf %{py3dir}
cp -a . %{py3dir}
pushd %{py3dir}
for file in setuptools/command/easy_install.py ; do
    sed -i '1s|^#!python|#!%{__python3}|' $file
done
popd
%endif # with_python3

%if 0%{?with_python2}
for file in setuptools/command/easy_install.py ; do
    sed -i '1s|^#!python|#!%{__python}|' $file
done
%endif # with_python2

%build
%{?scl:scl enable %{scl} - << \EOF}
%if 0%{?with_python2}
%if 0%{?build_wheel}
%{__python} setup.py bdist_wheel
%else
CFLAGS="$RPM_OPT_FLAGS" %{__python} setup.py build
%endif
%endif # with_python2

%if 0%{?with_python3}
pushd %{py3dir}
%if 0%{?build_wheel}
%{__python3} setup.py bdist_wheel
%else
CFLAGS="$RPM_OPT_FLAGS" %{__python3} setup.py build
%endif
popd
%endif # with_python3
%{?scl:EOF}

%install
rm -rf %{buildroot}

%{?scl:scl enable %{scl} - << \EOF}

# Must do the python3 install first because the scripts in /usr/bin are
# overwritten with every setup.py install (and we want the python2 version
# to be the default for now).
# Change to defaulting to python3 version in F22
%if 0%{?with_python3}
pushd %{py3dir}
%if 0%{?build_wheel}
pip3 install -I dist/%{python3_wheelname} --root %{buildroot} --strip-file-prefix %{buildroot}

%if 0%{?with_python2}
# TODO: we have to remove this by hand now, but it'd be nice if we wouldn't have to
# (pip install wheel doesn't overwrite)
rm %{buildroot}%{_bindir}/easy_install
%endif # with_python2

sed -i '/\/usr\/bin\/easy_install,/d' %{buildroot}%{python3_record}
%else
%{__python3} setup.py install --skip-build --root %{buildroot}
%endif

rm -rf %{buildroot}%{python3_sitelib}/setuptools/tests
%if 0%{?build_wheel}
sed -i '/^setuptools\/tests\//d' %{buildroot}%{python3_record}
%endif

find %{buildroot}%{python3_sitelib} -name '*.exe' | xargs rm -f
chmod +x %{buildroot}%{python3_sitelib}/setuptools/command/easy_install.py
popd
%endif # with_python3

%if 0%{?with_python2}
%if 0%{?build_wheel}
pip2 install -I dist/%{python2_wheelname} --root %{buildroot} --strip-file-prefix %{buildroot}
%else
%{__python} setup.py install --skip-build --root %{buildroot}
%endif

rm -rf %{buildroot}%{python_sitelib}/setuptools/tests
%if 0%{?build_wheel}
sed -i '/^setuptools\/tests\//d' %{buildroot}%{python2_record}
%endif

find %{buildroot}%{python_sitelib} -name '*.exe' | xargs rm -f
chmod +x %{buildroot}%{python_sitelib}/setuptools/command/easy_install.py
%endif # with_python2

install -p -m 0644 %{SOURCE1} %{SOURCE2} .
%{?scl:EOF}

%check
%{?scl:scl enable %{scl} - << \EOF}
%if 0%{?with_python2}
%{__python} setup.py test
%endif # with_python2

%if 0%{?with_python3}
pushd %{py3dir}
%{__python3} setup.py test
popd
%endif # with_python3
%{?scl:EOF}

%clean
rm -rf %{buildroot}


%if 0%{?with_python2}
%files
%defattr(-,root,root,-)
%doc *.txt docs
%{python_sitelib}/*
%{_bindir}/easy_install
%{_bindir}/easy_install-2.*
%endif # with_python2

%if 0%{?with_python3}
%files -n %{?scl_prefix}python3-setuptools
%defattr(-,root,root,-)
%doc *.txt docs
%{python3_sitelib}/*

%if ! 0%{?with_python2}
%{_bindir}/easy_install
%endif # !with_python2

%{_bindir}/easy_install-3.*
%endif # with_python3

%changelog
* Fri Jan 02 2015 Miro Hrončok <mhroncok@redhat.com> - 7.1-0.53.20150102hgaa23c45dbab3
- Update to hg: aa23c45dbab3

* Thu Jan 01 2015 Miro Hrončok <mhroncok@redhat.com> - 7.1-0.52.20150101hg41db17ef8356
- Update to hg: 41db17ef8356

* Wed Dec 31 2014 Miro Hrončok <mhroncok@redhat.com> - 7.1-0.51.20141231hg5970706c06f5
- Update to hg: 5970706c06f5

* Tue Dec 30 2014 Miro Hrončok <mhroncok@redhat.com> - 7.1-0.50.20141230hg5303b8865049
- Update to hg: 5303b8865049

* Tue Dec 30 2014 Miro Hrončok <mhroncok@redhat.com> - 7.1-0.49.20141230hg5aaed51c834c
- Update to hg: 5aaed51c834c

* Mon Dec 29 2014 Miro Hrončok <mhroncok@redhat.com> - 7.1-0.48.20141229hg6bed27694c5d
- Update to hg: 6bed27694c5d

* Sun Dec 28 2014 Miro Hrončok <mhroncok@redhat.com> - 7.1-0.47.20141228hge3d6b547ac05
- Update to hg: e3d6b547ac05

* Sat Dec 27 2014 Miro Hrončok <mhroncok@redhat.com> - 7.1-0.46.20141227hg5120dc55399c
- Update to hg: 5120dc55399c

* Fri Dec 26 2014 Miro Hrončok <mhroncok@redhat.com> - 7.1-0.45.20141226hgf87218c7421e
- Update to hg: f87218c7421e

* Thu Dec 25 2014 Miro Hrončok <mhroncok@redhat.com> - 7.1-0.44.20141225hgf233bfb10ed7
- Update to hg: f233bfb10ed7

* Wed Dec 24 2014 Miro Hrončok <mhroncok@redhat.com> - 7.1-0.43.20141224hg187639d13baf
- Update to hg: 187639d13baf

* Fri Dec 19 2014 Miro Hrončok <mhroncok@redhat.com> - 7.1-0.42.20141219hgc5f7235eaffa
- Update to hg: c5f7235eaffa

* Tue Dec 16 2014 Miro Hrončok <mhroncok@redhat.com> - 7.1-0.41.20141216hgb6669aaabee5
- Update to hg: b6669aaabee5

* Mon Dec 15 2014 Miro Hrončok <mhroncok@redhat.com> - 7.1-0.40.20141215hg6ba2f09c5749
- Update to hg: 6ba2f09c5749

* Sun Dec 14 2014 Miro Hrončok <mhroncok@redhat.com> - 7.1-0.39.20141214hg6da6946ab28e
- Update to hg: 6da6946ab28e

* Mon Dec 08 2014 Miro Hrončok <mhroncok@redhat.com> - 7.1-0.38.20141208hg4986103d77c7
- Update to hg: 4986103d77c7

* Wed Nov 26 2014 Miro Hrončok <mhroncok@redhat.com> - 7.1-0.37.20141126hg48a23a037ea2
- Update to hg: 48a23a037ea2

* Mon Nov 17 2014 Miro Hrončok <mhroncok@redhat.com> - 7.1-0.36.20141117hg8fcfefbe42a5
- Update to hg: 8fcfefbe42a5

* Fri Nov 14 2014 Miro Hrončok <mhroncok@redhat.com> - 7.1-0.35.20141114hg4338ea33572c
- Update to hg: 4338ea33572c

* Sun Oct 26 2014 Miro Hrončok <mhroncok@redhat.com> - 7.1-0.34.20141026hgdd8bb6bb99e0
- Update to hg: dd8bb6bb99e0

* Fri Oct 24 2014 Miro Hrončok <mhroncok@redhat.com> - 7.1-0.33.20141024hgb8451f8b0e81
- Update to hg: b8451f8b0e81

* Mon Oct 20 2014 Miro Hrončok <mhroncok@redhat.com> - 6.0.3-0.32.20141020hgf35c107404b4
- Update to hg: f35c107404b4

* Sun Oct 12 2014 Miro Hrončok <mhroncok@redhat.com> - 6.0.3-0.31.20141012hg98b6990c485e
- Update to hg: 98b6990c485e

* Fri Oct 10 2014 Miro Hrončok <mhroncok@redhat.com> - 6.0.3-0.30.20141010hg422cc543cb00
- Update to hg: 422cc543cb00

* Wed Oct 01 2014 Miro Hrončok <mhroncok@redhat.com> - 6.0.3-0.29.20141001hg312a67d000cb
- Update to hg: 312a67d000cb

* Tue Sep 30 2014 Miro Hrončok <mhroncok@redhat.com> - 5.8-0.28.20140930hgf5f18a6961a6
- Update to hg: f5f18a6961a6

* Sun Sep 28 2014 Miro Hrončok <mhroncok@redhat.com> - 5.8-0.27.20140928hgb01dd795c870
- Update to hg: b01dd795c870

* Sat Sep 27 2014 Miro Hrončok <mhroncok@redhat.com> - 5.8-0.26.20140927hg9fda11d40a17
- Update to hg: 9fda11d40a17

* Thu Sep 25 2014 Miro Hrončok <mhroncok@redhat.com> - 5.8-0.25.20140925hgc13770c5c76e
- Update to hg: c13770c5c76e

* Fri Sep 19 2014 Miro Hrončok <mhroncok@redhat.com> - 5.8-0.24.20140919hge278eb6f64b7
- Update to hg: e278eb6f64b7

* Thu Sep 11 2014 Miro Hrončok <mhroncok@redhat.com> - 5.8-0.23.20140911hga6daa77a00b2
- Update to hg: a6daa77a00b2

* Fri Aug 22 2014 Miro Hrončok <mhroncok@redhat.com> - 5.8-0.22.20140822hg01ec41e9b983
- Update to hg: 01ec41e9b983

* Mon Aug 18 2014 Miro Hrončok <mhroncok@redhat.com> - 5.5.2-0.21.20140818hg5267b920eeb9
- Update to hg: 5267b920eeb9

* Sun Aug 17 2014 Miro Hrončok <mhroncok@redhat.com> - 5.5.2-0.20.20140817hg42882466aa3b
- Update to hg: 42882466aa3b

* Sat Aug 16 2014 Miro Hrončok <mhroncok@redhat.com> - 5.5.2-0.19.20140816hgd15058738f96
- Update to hg: d15058738f96

* Fri Aug 15 2014 Miro Hrončok <mhroncok@redhat.com> - 5.5.2-0.18.20140815hg0e1e2e9f76bc
- Update to hg: 0e1e2e9f76bc

* Tue Aug 12 2014 Miro Hrončok <mhroncok@redhat.com> - 2.0-0.17.20140812hgb2eebb79cecb
- Update to hg: b2eebb79cecb

* Mon Aug 11 2014 Miro Hrončok <mhroncok@redhat.com> - 2.0-0.16.20140811hg1cf58151853e
- Update to hg: 1cf58151853e

* Fri Aug 08 2014 Miro Hrončok <mhroncok@redhat.com> - 2.0-0.15.20140808hgfba2455c461e
- Update to hg: fba2455c461e

* Tue Aug 05 2014 Miro Hrončok <mhroncok@redhat.com> - 2.0-0.14.20140805hg3c95d05aaad9
- Update to hg: 3c95d05aaad9

* Sat Aug 02 2014 Miro Hrončok <mhroncok@redhat.com> - 2.0-0.13.20140802hg60d0c9f24d88
- Update to hg: 60d0c9f24d88

* Mon Jul 28 2014 Miro Hrončok <mhroncok@redhat.com> - 2.0-0.12.20140728hge34c53dc1fa8
- Update to hg: e34c53dc1fa8

* Sun Jul 13 2014 Miro Hrončok <mhroncok@redhat.com> - 2.0-0.11.20140713hgb7581d108b87
- Update to hg: b7581d108b87

* Mon Jul 07 2014 Miro Hrončok <mhroncok@redhat.com> - 2.0-0.10.20140707hg9616be97e6a7
- Update to hg: 9616be97e6a7

* Sun Jul 06 2014 Miro Hrončok <mhroncok@redhat.com> - 2.0-0.9.20140706hgac801e423bb9
- Update to hg: ac801e423bb9

* Mon Jun 30 2014 Toshio Kuratomi <toshio@fedoraproject.org> - 2.0-8
- Remove the python-setuptools-devel Virtual Provides as per this Fedora 21
  Change: http://fedoraproject.org/wiki/Changes/Remove_Python-setuptools-devel

* Mon Jun 30 2014 Toshio Kuratomi <toshio@fedoraproject.org> - 2.0-7
- And another bug in sdist

* Mon Jun 30 2014 Toshio Kuratomi <toshio@fedoraproject.org> - 2.0-6
- Fix a bug in the sdist command

* Mon Jun 30 2014 Miro Hrončok <mhroncok@redhat.com> - 2.0-0.8.20140630hg2381b1160889
- Update to hg: 2381b1160889

* Sun Jun 29 2014 Miro Hrončok <mhroncok@redhat.com> - 2.0-0.7.20140629hg989c1f4044c6
- Update to hg: 989c1f4044c6

* Fri Jun 27 2014 Miro Hrončok <mhroncok@redhat.com> - 2.0-0.6.20140625hgb54ae9c52355
- Bootstrapping

* Wed Jun 25 2014 Miro Hrončok <mhroncok@redhat.com> - 2.0-0.5.20140625hgb54ae9c52355
- Update to hg: b54ae9c52355

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.0-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Fri Apr 25 2014 Matej Stuchlik <mstuchli@redhat.com> - 2.0-4
- Rebuild as wheel for Python 3.4

* Thu Apr 24 2014 Tomas Radej <tradej@redhat.com> - 2.0-3
- Rebuilt for tag f21-python

* Wed Apr 23 2014 Matej Stuchlik <mstuchli@redhat.com> - 2.0-2
- Add a switch to build setuptools as wheel

* Mon Dec  9 2013 Toshio Kuratomi <toshio@fedoraproject.org> - 2.0-1
- Update to new upstream release with a few things removed from the API:
  Changelog: https://pypi.python.org/pypi/setuptools#id139

* Mon Nov 18 2013 Toshio Kuratomi <toshio@fedoraproject.org> - 1.4-1
- Update to 1.4 that gives easy_install pypi credential handling

* Thu Nov  7 2013 Toshio Kuratomi <toshio@fedoraproject.org> - 1.3.1-1
- Minor upstream update to reign in overzealous warnings

* Mon Nov  4 2013 Toshio Kuratomi <toshio@fedoraproject.org> - 1.3-1
- Upstream update that pulls in our security patches

* Mon Oct 28 2013 Toshio Kuratomi <toshio@fedoraproject.org> - 1.1.7-1
- Update to newer upstream release that has our patch to the unittests
- Fix for http://bugs.python.org/issue17997#msg194950 which affects us since
  setuptools copies that code. Changed to use
  python-backports-ssl_match_hostname so that future issues can be fixed in
  that package.

* Sat Oct 26 2013 Toshio Kuratomi <toshio@fedoraproject.org> - 1.1.6-1
- Update to newer upstream release.  Some minor incompatibilities listed but
  they should affect few, if any consumers.

* Sun Aug 04 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.9.6-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Tue Jul 23 2013 Toshio Kuratomi <toshio@fedoraproject.org> - 0.9.6-1
- Upstream update -- just fixes python-2.4 compat

* Tue Jul 16 2013 Toshio Kuratomi <toshio@fedoraproject.org> - 0.9.5-1
- Update to 0.9.5
  - package_index can handle hashes other than md5
  - Fix security vulnerability in SSL certificate validation
  - https://bugzilla.redhat.com/show_bug.cgi?id=963260

* Fri Jul  5 2013 Toshio Kuratomi <toshio@fedoraproject.org> - 0.8-1
- Update to upstream 0.8  release.  Codebase now runs on anything from
  python-2.4 to python-3.3 without having to be translated by 2to3.

* Wed Jul  3 2013 Toshio Kuratomi <toshio@fedoraproject.org> - 0.7.7-1
- Update to 0.7.7 upstream release

* Mon Jun 10 2013 Toshio Kuratomi <toshio@fedoraproject.org> - 0.7.2-2
- Update to the setuptools-0.7 branch that merges distribute and setuptools

* Thu Apr 11 2013 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.36-1
- Update to upstream 0.6.36.  Many bugfixes

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.6.28-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Fri Aug 03 2012 David Malcolm <dmalcolm@redhat.com> - 0.6.28-3
- rebuild for https://fedoraproject.org/wiki/Features/Python_3.3

* Fri Aug  3 2012 David Malcolm <dmalcolm@redhat.com> - 0.6.28-2
- remove rhel logic from with_python3 conditional

* Mon Jul 23 2012 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.28-1
- New upstream release:
  - python-3.3 fixes
  - honor umask when setuptools is used to install other modules

* Sat Jul 21 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.6.27-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Mon Jun 11 2012 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.27-2
- Fix easy_install.py having a python3 shebang in the python2 package

* Thu Jun  7 2012 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.27-1
- Upstream bugfix

* Tue May 15 2012 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.24-2
- Upstream bugfix

* Sat Jan 14 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.6.24-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Mon Oct 17 2011 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.24-1
- Upstream bugfix
- Compile the win32 launcher binary using mingw

* Sun Aug 21 2011 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.21-1
- Upstream bugfix release

* Thu Jul 14 2011 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.19-1
- Upstream bugfix release

* Tue Feb 22 2011 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.14-7
- Switch to patch that I got in to upstream

* Tue Feb 22 2011 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.14-6
- Fix build on python-3.2

* Wed Feb 09 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.6.14-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Sun Aug 22 2010 Thomas Spura <tomspur@fedoraproject.org> - 0.6.14-4
- rebuild with python3.2
  http://lists.fedoraproject.org/pipermail/devel/2010-August/141368.html

* Tue Aug 10 2010 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.14-3
- Update description to mention this is distribute

* Thu Jul 22 2010 Thomas Spura <tomspur@fedoraproject.org> - 0.6.14-2
- bump for building against python 2.7

* Thu Jul 22 2010 Thomas Spura <tomspur@fedoraproject.org> - 0.6.14-1
- update to new version
- all patches are upsteam

* Wed Jul 21 2010 David Malcolm <dmalcolm@redhat.com> - 0.6.13-7
- generalize path of easy_install-2.6 and -3.1 to -2.* and -3.*

* Wed Jul 21 2010 David Malcolm <dmalcolm@redhat.com> - 0.6.13-6
- Rebuilt for https://fedoraproject.org/wiki/Features/Python_2.7/MassRebuild

* Sat Jul 3 2010 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.13-5
- Upstream patch for compatibility problem with setuptools
- Minor spec cleanups
- Provide python-distribute for those who see an import distribute and need
  to get the proper package.

* Thu Jun 10 2010 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.13-4
- Fix race condition in unittests under the python-2.6.x on F-14.

* Thu Jun 10 2010 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.13-3
- Fix few more buildroot macros

* Thu Jun 10 2010 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.13-2
- Include data that's needed for running tests

* Thu Jun 10 2010 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.13-1
- Update to upstream 0.6.13
- Minor specfile formatting fixes

* Thu Feb 04 2010 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.10-3
- First build with python3 support enabled.

* Fri Jan 29 2010 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.10-2
- Really disable the python3 portion

* Fri Jan 29 2010 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.10-1
- Update the python3 portions but disable for now.
- Update to 0.6.10
- Remove %%pre scriptlet as the file has a different name than the old
  package's directory

* Tue Jan 26 2010 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.9-4
- Fix install to make /usr/bin/easy_install the py2 version
- Don't need python3-tools since the library is now in the python3 package
- Few other changes to cleanup style

* Fri Jan 22 2010 David Malcolm <dmalcolm@redhat.com> - 0.6.9-2
- add python3 subpackage

* Mon Dec 14 2009 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.9-1
- New upstream bugfix release.

* Sun Dec 13 2009 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.8-2
- Test rebuild

* Mon Nov 16 2009 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.8-1
- Update to 0.6.8.
- Fix directory => file transition when updating from setuptools-0.6c9.

* Tue Nov 3 2009 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.7-2
- Fix duplicate inclusion of files.
- Only Obsolete old versions of python-setuptools-devel

* Tue Nov 3 2009 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.7-1
- Move easy_install back into the main package as the needed files have been
  moved from python-devel to the main python package.
- Update to 0.6.7 bugfix.

* Fri Oct 16 2009 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.6-1
- Upstream bugfix release.

* Mon Oct 12 2009 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.4-1
- First build from the distribute codebase -- distribute-0.6.4.
- Remove svn patch as upstream has chosen to go with an easier change for now.

* Sun Jul 26 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.6c9-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Tue Jul 14 2009 Konstantin Ryabitsev <icon@fedoraproject.org> - 0.6c9-4
- Apply SVN-1.6 versioning patch (rhbz #511021)

* Thu Feb 26 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.6c9-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild
