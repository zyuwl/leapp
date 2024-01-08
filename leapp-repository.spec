%global leapp_datadir %{_datadir}/leapp-repository
%global repositorydir %{leapp_datadir}/repositories
%global custom_repositorydir %{leapp_datadir}/custom-repositories
# Defining py_byte_compile macro because it is not defined in old rpm (el7)
# Only defined to python2 since python3 is not used in RHEL7
%{!?py_byte_compile: %global py_byte_compile py2_byte_compile() {\
    python_binary="%1"\
    bytecode_compilation_path="%2"\
    find $bytecode_compilation_path -type f -a -name "*.py" -print0 | xargs -0 $python_binary -c 'import py_compile, sys; [py_compile.compile(f, dfile=f.partition("$RPM_BUILD_ROOT")[2]) for f in sys.argv[1:]]' || :\
    find $bytecode_compilation_path -type f -a -name "*.py" -print0 | xargs -0 $python_binary -O -c 'import py_compile, sys; [py_compile.compile(f, dfile=f.partition("$RPM_BUILD_ROOT")[2]) for f in sys.argv[1:]]' || :\
}\
py2_byte_compile "%1" "%2"}

%define anolis_release 2

Name:           leapp-repository
Version:        0.13.3
Release:        1.%{anolis_release}%{?dist}
Summary:        Repositories for leapp

License:        ASL 2.0
URL:            https://oamg.github.io/leapp/
Source0:        https://github.com/oamg/leapp-repository/archive/v%{version}.tar.gz#/%{name}-%{version}.tar.gz
Source1:        deps-pkgs-2.tar.gz
Source2:        leapp_upgrade_repositories.repo
Source3:        pes-events.json
Source4:        repomap.csv

BuildArch:      noarch
BuildRequires:  python-devel

### PATCHES HERE

# IMPORTANT: everytime the requirements are changed, increment number by one
# - same for Provides in deps subpackage
Requires:       leapp-repository-dependencies = 5

# IMPORTANT: this is capability provided by the python2-leapp rpm.
Requires:       leapp-framework >= 1.4
Requires:       python2-psutil
%if 0%{rhel} == 7
Requires:       python36-psutil
%else
Requires:       python3-psutil
%endif

# That's temporary to ensure the obsoleted subpackage is not installed
# and will be removed when the current version of leapp-repository is installed
Obsoletes:      leapp-repository-data <= 0.6.1
Provides:       leapp-repository-data <= 0.6.1

# Former leapp subpackage that was packacking a leapp sos plugin - the plugin
# is part of the sos package since RHEL 7.8
Obsoletes:      leapp-repository-sos-plugin <= 0.10.0

# requres for upgrade
Requires:       glib2 >= 2.56.1

%description
Repositories for leapp


# This metapackage should contain all RPM dependencies exluding deps on *leapp*
# RPMs. This metapackage will be automatically replaced during the upgrade
# to satisfy dependencies with RPMs from target system.
%package deps
Summary:    Meta-package with system dependencies of %{name} package

# IMPORTANT: everytime the requirements are changed, increment number by one
# - same for Requires in main package
Provides:  leapp-repository-dependencies = 5
##################################################
# Real requirements for the leapp-repository HERE
##################################################
Requires:   dnf >= 4
Requires:   pciutils
%if 0%{?rhel} && 0%{?rhel} == 7
# Required to gather system facts about SELinux
Requires:   libselinux-python
Requires:   python-pyudev
# required by SELinux actors
Requires:   policycoreutils-python
%else ## RHEL 8 dependencies ##
# Requires:   systemd-container
%endif
##################################################
# end requirement
##################################################


%description deps
%{summary}


%prep
%autosetup -p1
%setup -q  -n %{name}-%{version} -D -T -a 1

%build
# ??? what is supposed to be this? we do not have any build target in the makefile
make build
cp -a leapp*deps*rpm repos/system_upgrade/el7toel8/files/bundled-rpms/


%install
install -m 0755 -d %{buildroot}%{custom_repositorydir}
install -m 0755 -d %{buildroot}%{repositorydir}
cp -r repos/* %{buildroot}%{repositorydir}/
install -m 0755 -d %{buildroot}%{_sysconfdir}/leapp/repos.d/
install -m 0755 -d %{buildroot}%{_sysconfdir}/leapp/transaction/
install -m 0755 -d %{buildroot}%{_sysconfdir}/leapp/files/
install -m 644 %{SOURCE2} %{buildroot}%{_sysconfdir}/leapp/files/
install -m 644 %{SOURCE3} %{buildroot}%{_sysconfdir}/leapp/files/
install -m 644 %{SOURCE4} %{buildroot}%{_sysconfdir}/leapp/files/

install -m 0644 etc/leapp/transaction/* %{buildroot}%{_sysconfdir}/leapp/transaction

# Remove irrelevant repositories - We don't want to ship them
rm -rf %{buildroot}%{repositorydir}/containerization
rm -rf %{buildroot}%{repositorydir}/test

# remove component/unit tests, Makefiles, ... stuff that related to testing only
rm -rf %{buildroot}%{repositorydir}/common/actors/testactor
find %{buildroot}%{repositorydir}/common -name "test.py" -delete
rm -rf `find %{buildroot}%{repositorydir} -name "tests" -type d`
find %{buildroot}%{repositorydir} -name "Makefile" -delete

for DIRECTORY in $(find  %{buildroot}%{repositorydir}/  -mindepth 1 -maxdepth 1 -type d);
do
    REPOSITORY=$(basename $DIRECTORY)
    echo "Enabling repository $REPOSITORY"
    ln -s  %{repositorydir}/$REPOSITORY  %{buildroot}%{_sysconfdir}/leapp/repos.d/$REPOSITORY
done;

%py_byte_compile %{__python2} %{buildroot}%{repositorydir}/*


%files
%doc README.md
%license LICENSE
%dir %{_sysconfdir}/leapp/transaction
%dir %{_sysconfdir}/leapp/files
%dir %{leapp_datadir}
%dir %{repositorydir}
%dir %{custom_repositorydir}
%{_sysconfdir}/leapp/repos.d/*
%{_sysconfdir}/leapp/transaction/*
%{repositorydir}/*
%{_sysconfdir}/leapp/files/*


%files deps
# no files here

%changelog
* Tue Sep 26 2023 wangzhe <wanglan.wz@alibaba-inc.com> - 0.13.3-1.2
- Release 0.13.3-1.2
- Simplified preupgrade steps

* Tue Aug 15 2023 wangzhe <wanglan.wz@alibaba-inc.com> - 0.13.3-1.1
- Release 0.13.3
- Simplified preupgrade steps 
- Fix some bugs

* Wed Jun 21 2023 wangzhe <wanglan.wz@alibaba-inc.com> - 0.13.2-1.1
- Release 0.13.2
- Add checkcifs and checkossfs, fix checknfs
- Support docker-ce repo
- Fix some bugs 

* Fri May 26 2023 Weitao Zhou <yunqi.zwt@alibaba-inc.com> - 0.13.1-1.1
- Release 0.13.1
- switch from rpm tree to source tree, remove all patch
- comment configure pam_tally2 out if confirmed
- support to remove multiple kernel-devel&kernel-debug

* Thu May 18 2023 Cichen Wang <wangcichen_yewu@cmss.chinamobile.com> - 0.13.0-2.24
- Fix bug with existing symlink in handleyumconfig

* Wed May 17 2023 Weitao Zhou <yunqi.zwt@alibaba-inc.com> - 0.13.0-2.23
- Support nodesource, zabbix 3rd repos migrate

* Fri May 12 2023 wangzhe <wanglan.wz@alibaba-inc.com> - 0.13.0-2.22
- Fix the memory unit error 

* Tue Apr 25 2023 wangzhe <wanglan.wz@alibaba-inc.com> - 0.13.0-2.21
- Report inhibitor message to SMC.

* Wed Apr 12 2023 wangzhe <wanglan.wz@alibaba-inc.com> - 0.13.0-2.20
- Add python-devel version check and update.
- Fix bug in grub2 version check

* Sat Mar 25 2023 guo chuang <guo.chuang@zte.com.cn> - 0.13.0-2.19
- Fixed the issue that collecting virtio type NIC information failed from the centos 7.4

* Mon Mar 7 2023 Bitao Hu <Bitao Hu@linux.alibaba.com> - 0.13.0-2.18
- Add grub2-tools update into answerfile.
- Comment patch 0025 out since openssl11-compat fixed it

* Mon Mar 6 2023 Weisson <Weisson@linux.alibaba.com> - 0.13.0-2.17
- Provides more information for debug purpose when exception happens in system requirement check.

* Fri Feb 24 2023 Weisson <Weisson@linux.alibaba.com> - 0.13.0-2.16
- Correct python3-psutil requirement branch make migration ARM-EPEL-compatible.

* Sat Feb 18 2023 Weitao Zhou <yunqi.zwt@alibaba-inc.com> - 0.13.0-2.15
- set a reasonable 600M mem in system requirements check

* Thu Feb 16 2023 Weisson <Weisson@linux.alibaba.com> - 0.13.0-2.14
- Add RPMDownloadOrInstallError and its exit code.
- comment patch 0031-Deal-with-EPEL-repositories-create-by-user-mannally.patch

* Wed Jan 18 2023 Weisson <Weisson@linux.alibaba.com> - 0.13.0-2.13
- Perform system requirements check to ensure migration.

* Tue Jan 10 2023 <Weisson@linux.alibaba.com> - 0.13.0-2.12
- GRUB2-EFI support.

* Mon Dec 12 2022 Weisson <Weisson@linux.alibaba.com> - 0.13.0-2.11
- Migrear grub2 entry recovery is supported.

* Fri Dec 9 2022 Bitao Hu <yaoma@linux.alibaba.com> - 0.13.0-2.10
- Add debug repo into leapp_upgrade_repositories.repo.

* Thu Nov 15 2022 Bitao Hu <yaoma@linux.alibaba.com> - 0.13.0-2.9
- Read the driver list supported by ANCK to determine driver compatibility problem, when migrating to Anolis8 with ANCK.
 
* Sun Nov 13 2022 Weisson <Weisson@linux.alibaba.com> - 0.13.0-2.8
- Keep PermitRootLogin authentication behavior after migration.

* Thu Sep 29 2022 Weisson <Weisson@linux.alibaba.com> - 0.13.0-2.7
- deal with user create EPEL repository file

* Tue Sep 13 2022 mgb01105731 <mgb01105731@alibaba-inc.com> - 0.13.0-2.6
- add disablerepo option to upgrade kernel to RHCK

* Tue Sep 6 2022 Weisson <Weisson@linux.alibaba.com> - 0.13.0-2.5
- Service configuration remains after migration

* Tue Sep 6 2022 mgb01105731 <mgb01105731@alibaba-inc.com> - 0.13.0-2.4
- support upgrade kernel to ANCK

* Thu Sep  1 2022 Liwei Ge <liwei.glw@linux.alibaba.com> - 0.13.0-2.3
- Write efi vars for ecs firmware

* Tue Jun 14 2022 Weitao Zhou <zhouwt@linux.alibaba.com> - 0.13.0-2.2
- Add checkbaota actor

* Fri Feb 18 2022 Chunmei Xu <xuchunmei@linux.alibaba.com> - 0.13.0-2.1
- Add support for centos 7.x and support upgrade to anolis8
- update description from RHEL8 to Anolis8 and add data files
- add checkopenssl and checkextramodule
- compat alinux3 platform
- add checkaudit, checksysstat and checkmandb
- add checkpkgforupgrade, checksystemd and checkglibc
- some bugfix for upgrade
- add key of aarch64 kernel for centos7.x
- add HighAvaliability repo
- update glib2 version to make sure dnf can work
- add checkdocker, checksysvinittools and checktomcat
- support migration anolis7 to anolis8
- add checklvm2cluster
- fix kernel version check of anolis kernel
- remove unofficial url and info
- add check openssl11-libs

* Thu Feb 04 2021 Dominik Rehak <drehak@redhat.com> - 0.13.0-2
- Rebuild
- Relates: #1915509 

* Thu Feb 04 2021 Dominik Rehak <drehak@redhat.com> - 0.13.0-1
- Rebase to v0.13.0
- Add actors to migrate Quagga to FRR
- Add stable uniq Key id for every dialog
- Add upgrade support for SAP HANA
- Allow upgrade with SCA enabled manifest
- Fix comparison of the newest installed and booted kernel
- Fix crash due to missing network interfaces during upgrade phases
- Fix error with /boot/efi existing on non-EFI systems
- Fix false positive detection of issue in /etc/default/grub that led into GRUB
  prompt
- Fix remediation command for ipa-server removal
- Fix syntax error in upgrade script
- Inhibit upgrade if multiple kernel-debug pkgs are installed
- Inhibit upgrade on s390x machines with /boot on a separate partition
- Inhibit upgrade with mount options in fstab that break mounting on RHEL 8
- Remove the *leapp-resume* service after the *FirstBoot* phase to prevent kill
  of the leapp process on `systemctl daemon-reload`
- Remove the initial-setup package to avoid it asking for EULA acceptance during
  upgrade
- Require the leapp-framework capability 1.4
- Respect the *kernel-rt* package
- Resolves: #1915509 #1872356 #1873312 #1899455 #1901002 #1905247 #1870813
- Relates: #1901440

* Sun Oct 25 2020 Petr Stodulka <pstodulk@redhat.com> - 0.12.0-2
- Add actors to migrate Quagga to FRR
- Fixes issues with interrupted leapp during the FirstBoot phase when reload
  of daemons is required
  Resolves: #1883218
- Relates: #1887912

* Wed Oct 21 2020 Dominik Rehak <drehak@redhat.com> - 0.12.0-1
- Rebase to v0.12.0
- Enable upgrades on AWS and Azure
- Check usage of removed/deprecated leapp env vars
- Do not inhibit if winbind or wins is used in nsswitch.conf
  (as the issue is fixed in RHEL 8.2)
- Do not remove java from the upgrade transaction
- Fix handling of events with same initial releases and input packages
- Fix mkhomedir issues after authselect conversion
- Fix python macro error in spec file
- Fix storing of logs from initramfs
- Handle migration of authselect and PAM
- Improve remediation instructions for HA clusters
- Make sure "default.target.wants" dir exists
- Resolves: #1887912

* Tue Sep 15 2020 Dominik Rehak <drehak@redhat.com> - 0.11.0-4
- Remove java from the upgrade transaction
  Relates: #1860375

* Tue Sep 08 2020 Petr Stodulka <pstodulk@redhat.com> - 0.11.0-3
- Set authselect and PAM actors experimental again
  Relates: #1860375

* Wed Sep 02 2020 Petr Stodulka <pstodulk@redhat.com> - 0.11.0-2
- Make possible upgrade with the java-11-openjdk-headless package
- Fix check of local repositories when metalink or mirrorlist is specified
- Relates: #1860375

* Tue Aug 18 2020 Michal Bocek <mbocek@redhat.com> - 0.11.0-1
- Rebase to v0.11.0
- Do not crash when the /root/temp_leapp_py3 directory exists (when upgrade is executed multiple times)
  Relates: #1858479
- Do not detect grub device on the s390x architecture (ZIPL is used there)
- Consider the katello rpm being signed by Red Hat
- Omit printing grub binary data on terminal which could break terminal output
- Provide just a single remedition command in the pre-upgrade report to be compatible with Satellite and Cockpit
- Search repository files only in directories used by DNF
- Change supported upgrade paths: RHEL-ALT 7.6 -> 8.2; RHEL 7.9 -> 8.2
- Check whether PAM modules, that are not present on RHEL 8, are used
- Inhibit upgrade when local repositories (referred by file://) are detected
- Introduce actors for migration of Authconfig to Authselect
- Support for an in-place upgrade for z15 machines - s390x architecture
- Update list of removed drivers on RHEL 8
- Resolves: #1860375

* Mon Apr 20 2020 Michal Bocek <mbocek@redhat.com> - 0.10.0-2
- Fixed broken cli output due to printing binary data
- Relates: #1821710

* Thu Apr 16 2020 Petr Stodulka <pstodulk@redhat.com> - 0.10.0-1
- Rebase to v0.10.0
- Changed upgrade paths: RHEL-ALT 7.6 -> 8.2; RHEL 7.8 -> 8.2
- Add initial multipath support (it doesn't handle all cases yet)
- Use the new framework mechanism to inhibit the upgrade without reporting errors
- Support the upgrade without the use of subscription-manager
- Add dependency on leapp-framework
- Check if the latest installed kernel is booted before the upgrade
- Check that the system satisfies minimum memory requirements
  for the upgrade (#413)
- Do not mount pseudo and unsupposrted FS to overlayfs (e.g. proc)
- Drop leapp sos plugin (it's part of the sos rpm in RHEL 7.7+)
- Evaluate PES events transitively to create correct data for the upgrade
  transaction
- Fix checking of kernel drivers (#400)
- Fix failures caused by local rpms added into the upgrade transaction
- Fix getting mount information with mountpoints with spaces in the path
- Fix handling of XFS without ftype for every such mounted FS
- Fix issue with random booting into old RHEL 7 kernel after the upgrade
- Fix issues on systems with statically mapped IPs in /etc/hosts
- Fix issues with device mapper and udev in a container
- Fix issues with failing rpm transaction calculation because of duplicate
  instructions for dnf
- Fix various issues related to RHSM (including rhbz rhbz#1702691)
- Fix yum repository scan in case of repositories with invalid URL
- Improved report related to KDE/GNOME
- Inhibit the upgrade for ipa-server (#481)
- Inhibit the upgrade if multiple kernel-devel rpms are installed
- Inhibit the upgrade on FIPS systems
- Inhibit the upgrade when links on root dir '/' are not absolute to save the world
- Inhibit the upgrade when the raised dialogs are missing answers (#589)
- Introduce new ways of using custom repositories during the transaction
- Make report messages more explicit about Dialogs (#600)
- Migrate SpamAssassin
- Migrate cups-filters
- Migrate sane-backend
- Modify vim configuration to keep the original behaviour
- Parse correctly kernel cmdline inside the initrd (#383) (fixes various issues on s390x)
- Print warnings instead of a hard failure when expected rpms cannot be found
  (e.g. python3-nss inside an rpm module) (#405)
- Remove java11-openjdk-headless during the upgrade (rhbz#1820172)
- Report changes in wireshark
- The name and baseurl field in the CustomTargetRepository message are optional now
- Throw a nice error when invalid locale is set (#430)
- Various texts are improved based on the feedback
- Resolves: #1821710

* Tue Nov 5 2019 Petr Stodulka <pstodulk@redhat.com> - 0.9.0-5
- Do not use efibootmgr on non-efi systems
  Resolves: #1768904

* Mon Nov 4 2019 Petr Stodulka <pstodulk@redhat.com> - 0.9.0-4
- Inhibit upgrade on EFI systems when efibootmgr is not installed
  Relates: #1753580

* Fri Nov 1 2019 Petr Stodulka <pstodulk@redhat.com> - 0.9.0-3
- Inhibit upgrade on s390x machines with rd.znet in kernel cmdline to prevent
  troubles with networking (temporary)
- Fix issues with failing rpm transaction calculation because of duplicates
- Fix boot order on EFI systems
  Relates: #1753580

* Wed Oct 30 2019 Michal Bocek <mbocek@redhat.com> - 0.9.0-2
- Fixed some remediation instructions
- Not trying to make an overlay over /boot/efi
  Relates: #1753580

* Thu Oct 24 2019 Petr Stodulka <pstodulk@redhat.com> - 0.9.0-1
- Rebase to v0.9.0
- Added dependency on policycoreutils-python
- Change upgrade path from RHEL(-ALT) 7.6 (EUS) to RHEL 8.1
- Changed the title of the upgrade boot entry to be valid for ZIPL
- Check NSS configuration for use of wins or winbind
- Check SSSD configuration
- Check use of removed PAM modules
- Check whether CPU on s390x is supported on RHEL 8
- Do not remove packages which shall be installed/kept on target system
- Do not waste time by downloading of RPMs if upgrade has been inhibited already
- Enable and make possible upgrades on all architectures
- Enable repositories used for upgrade on the upgraded system
- Fix adding of local rpms into the upgrade transaction
- Fix check of active kernel modules
- Fix handling of XFS filesystems with ftype=0 (rhbz#1746956)
- Fix ntp migration: extract configs into the right directories
- Fix traceback when RHSM is skipped
- Handle possible error when setting release on upgraded system
- Handle systems with EFI boot
- Handle upgrade on systems with multiple partitions
- Improve message on failed subscription-manager and dnf
- Improved the reporting capability
- Migrate SELinux customizations
- No size limit on leapp.db in sosreport
- Process new PES data format + process PES events in order of releases
- Require the biosdevname dracut module on the intel architecture only
- Retry some actions of subscription-manager on failure to reduce number of issues
- Update the list of packages supposed to be removed during the upgrade
- Upgrade only packages signed by Red Hat
  Resolves: #1753580

* Thu Jul 25 2019 Petr Stodulka <pstodulk@redhat.com> - 0.8.1-2
- attempt to (un)set rhsm release several times to omit possible problems with
  server
  Relates: #1723115

* Wed Jul 24 2019 Petr Stodulka <pstodulk@redhat.com> - 0.8.1-1
- Rebase to v0.8.1
  Relates: #1723115
- enable installation of RPMs that were previously blacklisted due to problems
  with rich dependencies

* Mon Jul 15 2019 Petr Stodulka <pstodulk@redhat.com> - 0.8.0-1
- Rebase to v0.8.0
  Relates: #1723115
- improve handling of RPM transaction to be able to process RPMs with
  rich dependencies
- add missing dependency on python-udev & python3-udev
- fix processing of last phase during the first boot of the upgraded system
- set RHSM target release after the upgrade to expected version of the system
- enable the CRB repository when the Optional repository is enabled
- check tcp wrappers
- check OpenSSH configuration
- check and handle vftpd configuration
- check kernel drivers
- improve checks related to subscriptions
- improve parsing of /etc/fstab
- ensure the new target kernel is default boot entry
- handle better cases when no target repositories has been found
- migrate NTP to chronyd
- migrate brltty configuration
- migrate sendmail
- avoid removal of /etc/localtime and /etc/resolv.conf during the upgrade
- add informational actors for: acpid, chrony, dosfstools, grep, irssi,
  postfix, powertop

* Sun Jun 23 2019 Vojtech Sokol <vsokol@redhat.com> - 0.7.0-6
- Rebuild
  Resolves: #1723115

* Fri Apr 26 2019 Petr Stodulka <pstodulk@redhat.com> - 0.7.0-5
- build rhel8 initrd on the fly during the upgrade process
- do not bundle initrd and vmlinuz file in the rpm
  Relates: #1636481

* Fri Apr 26 2019 Petr Stodulka <pstodulk@redhat.com> - 0.7.0-4
- add python2-docs and python3-docs to the list of rpms for removal as
  currently it causes troubles with RPM transaction
  Relates: #1636481

* Fri Apr 26 2019 Petr Stodulka <pstodulk@redhat.com> - 0.7.0-3
- set selinux into the permissive mode on RHEL 8 when enforcing was set
  originally
- add python-docs and squid rpms to the list of rpms for removal
  Relates: #1636481

* Wed Apr 17 2019 Petr Stodulka <pstodulk@redhat.com> - 0.7.0-2
- fix inhibition when ethX network interface exists and more additional NIC
  exist as well
  Relates: #1636481

* Wed Apr 17 2019 Petr Stodulka <pstodulk@redhat.com> - 0.7.0-1
- Rebase to v0.7.0
  Relates: #1636481
- new dependencies: python3, python*-pyudev
- upgrade process is interrupted after RPMUpgradePhase and resumed with Python3
- upgrade of NetworkManager is fixed
- upgrade of firewalld is handled
- name changes of network interfaces are handled
- HTB repositories used for upgrades are replaced with the ones used for GA
- tpm2-abrmd and all packages that depend on redhat-rpm-config are removed
  during upgrade
- handling of the upgrade RPM transaction is improved
- sync command is used in initrd to avoid issues related to cache
- networking naming changes are handled
- disable udev's persistent network interface naming scheme when the only NIC
  is eth0
- inhibit upgrade when ethX is detected and more NICs exist
- check whether all target upgrade repositories are available
- output of dnf tool is always showed during the upgrade
- all logs and reports are stored in /var/log/leapp/ directory


* Tue Apr 09 2019 Vojtech Sokol <vsokol@redhat.com> - 0.6.0-4
- Remove wrong license for sos subpackage
  Relates: #1636481

* Mon Apr 08 2019 Vojtech Sokol <vsokol@redhat.com> - 0.6.0-3
- Fix patch
  Relates: #1636481

* Mon Apr 08 2019 Vojtech Sokol <vsokol@redhat.com> - 0.6.0-2
- Fix specfile
  Relates: #1636481

* Mon Apr 08 2019 Vojtech Sokol <vsokol@redhat.com> - 0.6.0-1
- Rebase to v0.6.0
  Relates: #1636481
- Change license to Apache 2.0
- leapp-repository-data subpackage is removed (it included data files)
  - data files are required to be delivered by user manually now
- udev database is accessible during the upgrade
- downtime of some machines is significantly reduced
- sos plugin is introduced for collecting data needed for debugging
- redhat-rpm-config package is removed during upgrade
- system is checked for NFS filesystems usage and upgrade is inhibited when
  detected
- /boot is checked for sufficient free space
- upgrade is not inhibited any more when Logic SCSI Controllers are present
- repositories used to upgrade the system are based on provided data files
- specific syntax errors in grub configuration are handled when detected
- SCTP is handled during the upgrade
- migration of yum is handled (yum is available after the upgrade)
- upgrade of NetworkManager is handled
- upgrades with XFS filesystems without ftype is handled better
- new reporting functionality is introduced and used
- new dependencies: python2-jinja2, pciutils, sos
- new directory /etc/leapp/files for data files is introduced
- python files are precompiled to avoid left over pyc files

* Thu Jan 24 2019 Petr Stodulka <pstodulk@redhat.com> - 0.5.0-1
- Rebase to v0.5.0
  Relates: #1636481
- Require DNF v4+ and Leapp framework v0.5.0
- Improved handling of RPM transaction using own DNF plugin and PES
  data
- Models have been refactored to use new format supported by framework
- Handle transaction preparation when release is set through RHSM
- Fix failing overlayfs unmounting
- Reduce the IPUWorkflo workflow
- Include all required directories inside RPMs
- Handle repositories using metalink and mirrorlist
- Handle better installation of local RPMs
- Move system dependencies into the RPM metapackage
- Satisfy leapp and leapp-repository RPM dependencies during the
  upgrade

* Thu Jan 03 2019 Petr Stodulka <pstodulk@redhat.com> - 0.4.0-4
- Activate LVM LVs during upgrade
- Resolve file conflict of python-inotify during the RPM transaction
  Relates: #1636481

* Thu Nov 29 2018 Petr Stodulka <pstodulk@redhat.com> - 0.4.0-3
- Add empty empty events for leapp-repository-data.
- Requiring now DNF 2.7.5-19 or higher
  Relates: #1636481

* Wed Nov 21 2018 Petr Stodulka <pstodulk@redhat.com> - 0.4.0-2
- update leapp-repository-data source
  Relates: #1636481

* Wed Nov 21 2018 Petr Stodulka <pstodulk@redhat.com> - 0.4.0-1
- Rebase to 0.4.0
- change hierarchy of repositories
- scan RHEL system for custom and 3rd-party packages
- improve error messages
  Relates: #1636481

* Fri Nov 09 2018 Petr Stodulka <pstodulk@redhat.com> - 0.3.1-1
- Rebase to 0.3.1
- move data to separate subpackage
  Relates: #1636481

* Wed Nov 07 2018 Petr Stodulka <pstodulk@redhat.com> - 0.3-1
- Initial RPM
  Resolves: #1636481

