%define anolis_release .0.4
# IMPORTANT: this is for the leapp-framework capability (it's not the real
# version of the leapp). The capability reflects changes in api and whatever
# functionality important from the point of repository. In case of
# incompatible changes, bump the major number and zero minor one. Otherwise
# bump the minor one.
# NOTE: we do not use this capability in the RHEL official rpms. But we provide
# it. In case of upstream, dependencies are set differently, but YUM is not
# capable enough to deal with them correctly all the time; we continue to use
# simplified deps in RHEL to ensure that YUM can deal with it.
%global framework_version 1.4

# IMPORTANT: everytime the requirements are changed, increment number by one
# - same for Provides in deps subpackage
%global framework_dependencies 3

# Do not build bindings for python3 for RHEL == 7
%if 0%{?rhel} && 0%{?rhel} == 7
%define with_python2 1
%else
%if 0%{?rhel} && 0%{?rhel} > 7
%bcond_with python2
%else
%bcond_without python2
%endif
%bcond_without python3
%endif

Name:       leapp
Version:    0.12.1
Release:    1%{anolis_release}%{?dist}
Summary:    OS & Application modernization framework

License:    ASL 2.0
URL:        https://oamg.github.io/leapp/
Source0:    https://github.com/oamg/%{name}/archive/v%{version}.tar.gz#/%{name}-%{version}.tar.gz
Source1:    answerfile
BuildArch:  noarch

%if !0%{?fedora}
%if %{with python3}
Requires: python3-%{name} = %{version}-%{release}
%else
Requires: python2-%{name} = %{version}-%{release}
%endif
# This is different from upstream! Read the note on the top of the spec file.
# Keep the direct dependency on leapp-repository here.
Requires: leapp-repository >= 0.13.0
%endif # !fedora

%description
Leapp tool for handling upgrades.


##################################################
# snactor package
##################################################
%package -n snactor
Summary: %{summary}
%if %{with python3}
Requires: python3-%{name} = %{version}-%{release}
%else
Requires: python2-%{name} = %{version}-%{release}
%endif

%description -n snactor
Leapp's snactor tool - actor development environment utility for creating and
managing actor projects.

##################################################
# Python 2 library package
##################################################
%if %{with python2}

%package -n python2-%{name}

Summary: %{summary}
%{?python_provide:%python_provide python2-%{name}}

%if 0%{?rhel} && 0%{?rhel} == 7
# RHEL 7
BuildRequires:  python-devel
BuildRequires:  python-setuptools
%else # rhel <> 7 or fedora
BuildRequires:  python2-devel
BuildRequires:  python2-setuptools
%endif # rhel <> 7

Provides: leapp-framework = %{framework_version}
Requires: leapp-framework-dependencies = %{framework_dependencies}

%description -n python2-%{name}
Python 2 leapp framework libraries.

%endif # with python2

# FIXME:
# this subpackages should be used by python2-%%{name} - so it makes sense to
# improve name and dependencies inside - do same subpackage for python3-%%{name}
%package deps
Summary:    Meta-package with system dependencies of %{name} package

# IMPORTANT: everytime the requirements are changed, increment number by one
# same for requirements in main package above
Provides: leapp-framework-dependencies = %{framework_dependencies}
##################################################
# Real requirements for the leapp HERE
##################################################
# NOTE: ignore Python3 completely now
%if 0%{?rhel} && 0%{?rhel} == 7
Requires: python-six
Requires: python-setuptools
Requires: python-requests
%else
%if %{with python3}
Requires: python3-six
Requires: python3-setuptools
Requires: python3-requests
%else # with python2
Requires: python2-six
Requires: python2-setuptools
Requires: python2-requests
%endif
%endif
Requires: findutils
##################################################
# end requirements here
##################################################
%description deps
%{summary}

##################################################
# Python 3 library package
##################################################
%if %{with python3}

%package -n python3-%{name}
Summary: %{summary}
%{?system_python_abi}
%{?python_provide:%python_provide python3-%{name}}

BuildRequires:  python3-devel
BuildRequires:  python3-setuptools

Requires: leapp-framework-dependencies = %{framework_dependencies}

%description -n python3-%{name}
Python 3 leapp framework libraries.

%endif # with python3

##################################################
# Prep
##################################################
%prep
%setup -n %{name}-%{version}

##################################################
# Build
##################################################
%build

%if %{with python2}
%py2_build
%endif

%if %{with python3}
%py3_build
%endif


##################################################
# Install
##################################################
%install

install -m 0755 -d %{buildroot}%{_mandir}/man1
install -m 0644 -p man/snactor.1 %{buildroot}%{_mandir}/man1/

%if !0%{?fedora}
install -m 0755 -d %{buildroot}%{_datadir}/leapp
install -m 0755 -d %{buildroot}%{_datadir}/leapp/report_schema
install -m 0644 -p report-schema-v110.json %{buildroot}%{_datadir}/leapp/report_schema/report-schema.json
install -m 0755 -d %{buildroot}%{_sharedstatedir}/leapp
install -m 0755 -d %{buildroot}%{_sysconfdir}/leapp
install -m 0755 -d %{buildroot}%{_sysconfdir}/leapp/repos.d
install -m 0600 -d %{buildroot}%{_sysconfdir}/leapp/answers
# standard directory should have permission set to 0755, however this directory
# could contain sensitive data, hence permission for root only
install -m 0700 -d %{buildroot}%{_sysconfdir}/leapp/answers
# same for this dir; we need it for the frontend in cockpit
install -m 0700 -d %{buildroot}%{_localstatedir}/log/leapp
install -m 0644 etc/leapp/*.conf %{buildroot}%{_sysconfdir}/leapp
install -m 0644 -p man/leapp.1 %{buildroot}%{_mandir}/man1/
install -m 0644 -p %{SOURCE1} %{buildroot}%{_localstatedir}/log/leapp/
%endif # !fedora

%if %{with python2}
%py2_install
%endif

%if %{with python3}
%py3_install
%endif

%if 0%{?fedora}
rm -f %{buildroot}/%{_bindir}/leapp
%endif


##################################################
# leapp files
##################################################

%if !0%{?fedora}
%files
%doc README.md
%license COPYING
%{_mandir}/man1/leapp.1*
%config(noreplace) %{_sysconfdir}/leapp/leapp.conf
%config(noreplace) %{_sysconfdir}/leapp/logger.conf
%config(noreplace) %{_localstatedir}/log/leapp/answerfile
%dir %{_sysconfdir}/leapp
%dir %{_sysconfdir}/leapp/answers
%dir %{_sysconfdir}/leapp/repos.d
%{_bindir}/leapp
%dir %{_sharedstatedir}/leapp
%dir %{_localstatedir}/log/leapp
%dir %{_datadir}/leapp/
%dir %{_datadir}/leapp/report_schema/
%{_datadir}/leapp/report_schema
%{python2_sitelib}/leapp/cli
%endif



##################################################
# snactor files
##################################################
%files -n snactor
%license COPYING
%{python2_sitelib}/leapp/snactor
%{_mandir}/man1/snactor.1*
%{_bindir}/snactor


##################################################
# python2-leapp files
##################################################
%if %{with python2}

%files -n python2-%{name}
%license COPYING
%{python2_sitelib}/*
# this one is related only to leapp tool
%exclude %{python2_sitelib}/leapp/cli
%exclude %{python2_sitelib}/leapp/snactor

%endif

##################################################
# python3-leapp files
##################################################
%if %{with python3}

%files -n python3-%{name}
%license COPYING
%{python3_sitelib}/*
#TODO: ignoring leapp and snactor in separate rpms now as we do not provide
# entrypoints for Py3 in those subpackages anyway

%endif

#FIXME: in case of rename, put those subpkgs under relevant if statement
%files deps
# no files here

%changelog
* Tue Sep 26 2023 wangzhe <wanglan.wz@alibaba-inc.com> - 0.12.1-1.0.4
- Simplified preupgrade steps

* Tue Aug 15 2023 wangzhe <wanglan.wz@alibaba-inc.com> - 0.12.1-1.0.3
- Simplified preupgrade steps

* Wed Jun 21 2023 wangzhe <wanglan.wz@alibaba-inc.com> - 0.12.1-1.0.2
- Release 0.12.1 
- fix install script
- confirm some inhibitors

* Fri May 26 2023 Weitao Zhou <yunqi.zwt@alibaba-inc.com> - 0.12.1-1.0.1
- bug fix: update source package

* Fri May 26 2023 wangzhe <wanglan.wz@alibaba-inc.com> - 0.12.0-1.0.12
- switch from rpm tree to source tree, remove all patch 

* Thu May 18 2023 Cichen Wang <wangcichen_yewu@cmss.chinamobile.com> - 0.12.0-1.0.11
- Enforce locale when running the IPU workflow.

* Mon Mar  13 2023 Weitao Zhou <yunqi-zwt@linux.alibaba.com> - 0.12.0-1.0.10
- set confirm=True if need to update grub2-tools

* Mon Mar  6 2023 Weisson <Weisson@linux.alibaba.com> - 0.12.0-1.0.9
- Provides exceptions for system environment check failure.

* Tue Dec 27 2022 Weisson <Weisson@linux.alibaba.com> - 0.12.0-1.0.8
- Provide more failure information for debug propose.

* Fri Dec 23 2022 Weisson <Weisson@linux.alibaba.com> - 0.12.0-1.0.7
- [Bugfix] Leapp stops if any exception is thrown, the shortcut on exit-code check might cause problem.

* Fri Dec 16 2022 Weitao Zhou <zhouwt@linux.alibaba.com> 0.12.0-1.0.6
- spec: set answer remove_pam_pkcs11 and remove_pam_krb5 as default

* Tue Dec 6 2022 Yuanhe Shu <xiangzao@linux.alibaba.com> 0.12.0-1.0.5
- patch:  add customrepo command
- bug fix: patch external link

* Mon Nov 28 2022 Weisson <Weisson@linux.alibaba.com> - 0.12.0-1.0.4
- SMC progress indicator

* Sat Sep 24 2022 Weitao Zhou <zhouwt@linux.alibaba.com> - 0.12.0-1.0.3
- patch:  report a default external link

* Tue Sep 13 2022 mgb01105731 <mgb01105731@alibaba-inc.com> - 0.12.0-1.0.2
- patch:  add disablerepo option to upgrade kernel to RHCK

* Tue Jun 14 2022 Weitao Zhou <zhouwt@linux.alibaba.com> - 0.12.0-1.0.1
- patch:  add parament remove-actor (yuki1109)
- patch:  add command no rhsm_skip (FrankCui713)

* Thu Feb 04 2021 Dominik Rehak <drehak@redhat.com> - 0.12.0-1
- Rebase to v0.12.0
- Bump leapp-framework capability to 1.4
- Add JSON schema of leapp reports for validation
- Add a stable report identifier for each generated report
- Resolves: #1915508

* Wed Oct 21 2020 Dominik Rehak <drehak@redhat.com> - 0.11.1-1
- Rebase to v0.11.1
- Fix conversion of deprecation messages to reports
- Fix various issues regarding suppressing of deprecation
- Remove pytest residuals in spec file
- Update documentation and manpages
- Resolves: #1887913

* Tue Aug 18 2020 Michal Bocek <mbocek@redhat.com> - 0.11.0-1
- Rebase to v0.11.0
- Bump leapp-framework capability to 1.3
- Preserve verbose/debug options during the whole upgrade workflow
- Print the informative error block to the STDOUT instead of STDERR
- Add new reporting tags: `PUBLIC_CLOUD` and `RHUI`
- Add the possibility to skip actor discovery to improve performance of tests when an actor context is injected directly
- Introduce the `deprecated` and `suppress_deprecation` decorators to support the deprecation process
- Store dialog answers in the leapp.db
- Update and improve man pages
- Raising a missing exception with tests failing under py3
- Adde the --actor-config option to `snactor run` to specify a workflow configuration model that should be consumed by actors
- The `call` function has been improved to be working on MacOS
- Known issue: the `suppress_deprecation` decorator causes a traceback in certain cases

* Thu Jul 30 2020 Michal Bocek <mbocek@redhat.com> - 0.10.0-3
- A temporary build to run TPS tests against
- Relates: #1860373

* Mon Apr 20 2020 Michal Bocek <mbocek@redhat.com> - 0.10.0-2
- Make debug/verbose setting persistent across the upgrade
- Relates: #1821712

* Thu Apr 16 2020 Petr Stodulka <pstodulk@redhat.com> - 0.10.0-1
- Rebase to v0.10.0
- Add the --enablerepo option for Leapp to use an existing custom yum/dnf
  repository during the upgrade
- Add the --no-rhsm option for Leapp for use without subscription-manager
  (#622)
- Add `leapp answer` to answer Dialog questions in CLI (#592)
- Add `stdin` and `encoding` parameters in the run function (#583, #595)
- Add new dependency on python-requests
- Add the DESKTOP tag for the leapp report (#612)
- Display a warning when leapp is used in an unsupported (devel/testing) mode
  (#577)
- Drop dependency on python-jinja2
- Error messages are now part of the preupgrade report
- Fix json export capabilities using serialization (#598)
- Introduce DialogModel that could be processed by actors to add related
  information into the report (#589)
- Introduce Workflow API (#618)
- Move all leapp and snactor files into related rpms instead of python2-leapp
  (#591)
- Print errors on stdout in pretty format (#593)
- Report inhibitors separately from errors on stdout (#620)
- Show progress in non-verbose executions (#621)
- The verbosity options (--verbose | --debug) are available for leapp commands
  as well
- Resolves: #1821712


* Thu Oct 24 2019 Petr Stodulka <pstodulk@redhat.com> - 0.9.0-1
- Rebase to v0.9.0
- Add sanity-check command for snactor
- Add the /var/log/leapp directory to the leapp RPM
- Handle string types in compatible way
- Introduce answerfile generation & usage
- Introduce report composability, remove renders (#543)
- Show help message for proper subcommand of leapp
- Stop adding 'process-end' audit entry (#538)
- Various fixes in displaying of generated reports
- Resolves: #1753583

* Wed Jul 24 2019 Petr Stodulka <pstodulk@redhat.com> - 0.8.1-1
- Rebase to v0.8.1
  Relates: #1723113
- Fix issue undefined ReportReference

* Mon Jul 15 2019 Petr Stodulka <pstodulk@redhat.com> - 0.8.0-1
- Rebase to v0.8.0
  Relates: #1723113
- add the preupgrade subcommand to be able check system and generate report for
  upgrade without run of the upgrade itself
- add checks of arguments for cmdline parameters
- log output of commands to logfile (#520)
- avoid spurious output about missing logger
- exit non-zero on unhandled exceptions and errors
- fix actor library loading, so libraries do not have to be imported in
  lexicographical order
- log on the ERROR level by default instead of DEBUG
- create a dynamic configuration phase that allows creation of configuration
  for repository workflow
- add JSON report generation
- stdlib: add option to `run()` to ignore exit code

* Sun Jun 23 2019 Vojtech Sokol <vsokol@redhat.com> - 0.7.0-3
- Rebuild
  Resolves: #1723113

* Mon Apr 29 2019 Petr Stodulka <pstodulk@redhat.com> - 0.7.0-2
- load checkpoints ordered by 'id' instead of timestamp
  Relates: #1636478

* Wed Apr 17 2019 Vojtech Sokol <vsokol@redhat.com> - 0.7.0-1
- Rebase to v0.7.0
  Relates: #1636478
- add the ability to stop and resume workflow in any phase
- fix incompatibilities with Python3
- store logs in one place and support archiving of previous logs
- fix handling of Unicode in the run function of leapp stdlib

* Mon Apr 08 2019 Vojtech Sokol <vsokol@redhat.com> - 0.6.0-2
- Fix specfile
  Relates: #1636478

* Mon Apr 08 2019 Vojtech Sokol <vsokol@redhat.com> - 0.6.0-1
- Rebase to v0.6.0
  Relates: #1636478
- snactor
  - `repo new` subcommand: display message if directory with same name exists
  - `discover subcommand`: fix wrong path
  - `workflow run` subcommand: introduce `--save-output` parameter
  - fix cryptic message without user repo config
  - show global repos in repo list
  - fix trace on topic creation
- stdlib
  - make api directly available in stdlib
  - external program exec function - audit data generation and storage
- models
  - introduction of the JSON field type
- new debug and verbose modes
- new reporting capabilities
- change default loglevel to ERROR

* Thu Jan 24 2019 Petr Stodulka <pstodulk@redhat.com> - 0.5.0-1
- Rebase to v0.5.0
  Relates: #1636478
- Models has been refactored to be more comprehensible and reliable
- Introduced standard library
- Introduced the actor convenience api for actors and repository libraries
- Added localization support
- Extended serialization support
- Added exception to be able to stop actor execution
- Packaging: Move system dependencies into the metapackage

* Fri Nov 23 2018 Petr Stodulka <pstodulk@redhat.com> - 0.4.0-1
- Rebase to v0.4.0
  Relates: #1636478

* Wed Nov 07 2018 Petr Stodulka <pstodulk@redhat.com> - 0.3.1-1
- Rebase to v0.3.1
  Relates: #1636478

* Wed Nov 07 2018 Petr Stodulka <pstodulk@redhat.com> - 0.3-1
- Initial rpm
  Resolves: #1636478
