#!/usr/bin/env bash

[ "$EUID" -eq 0 ] || {
  echo "Please run this script as a root user"
  exit 1
}

mirror_site="${MIRROR_SITE:-https://mirrors.openanolis.cn}"

report_error_in_jsonfile() {
  unixtime=`date +%s`
  errMsg_inline=$(echo "$3" | tr -d '\n\r\t"\\')
  printf '{"Timestamp":%s,"ProgressInfo":"%s","Progress":0,"ErrorCode":%s,"ErrorMsg":"%s"}' "$unixtime" "$1" "$2" "$errMsg_inline" >$jsonfile
}

check_if_centos_or_rhel() {
  [ -f /etc/centos-release ] && return 0
  [ -f /etc/redhat-release ] && return 0
  echo "CANNOT find /etc/centos-release or /etc/redhat-release, WONT install migration tool" && exit 1
}

disable_migration_repo() {
  sed -i "s/enabled=1/enabled=0/" /etc/yum.repos.d/anolis-migration.repo
}

# config epel
epel_repo_config() {
  rpm -q epel-release && [ -f /etc/yum.repos.d/epel.repo ] && return 0
  # maybe using filename epel-7.repo since this guide https://developer.aliyun.com/mirror/epel
  rpm -q epel-release && [ -f /etc/yum.repos.d/epel-7.repo ] && return 0
  rpm -q epel-release && [ -f /etc/yum.repos.d/CentOS-Linux-epel.repo ] && return 0

  major_release=`rpm --eval '%{centos_ver}'`
  [ "$?" -eq 0 ] || {
    echo "failed to get os major release"
    exit 1
  }

  out=$(yum install -y epel-release 2>&1)
  exit_code=$?
  if [ "$exit_code" -ne 0 ]
  then
    echo "failed to install epel-release"
    out="$out\n `ls /etc/yum.repos.d` `cat /etc/yum.conf`"
    report_error_in_jsonfile "install epel-release" 103 "$out"
    exit 1
  fi

  # set better mirror site
  sed -i 's|^enabled=1|enabled=0|' /etc/yum.repos.d/epel*
  if [ "$major_release" -eq 7 ]
  then
    cat << EOF > /etc/yum.repos.d/epel.repo
[epel]
name=Extra Packages for Enterprise Linux 7 - \$basearch
enabled=1
failovermethod=priority
baseurl=https://mirrors.aliyun.com/epel/7/\$basearch
        http://mirrors.cloud.aliyuncs.com/epel/7/\$basearch
gpgcheck=0
EOF
  fi
  if [ "$major_release" -eq 8 ]
  then
    cat << EOF > /etc/yum.repos.d/epel.repo
[epel]
name=Extra Packages for Enterprise Linux 8 - \$basearch
baseurl=https://mirrors.aliyun.com/epel/8/Everything/\$basearch
        http://mirrors.cloud.aliyuncs.com/epel/8/Everything/\$basearch
failovermethod=priority
enabled=1
gpgcheck=0
EOF
  fi
}

# config anolis migration repo
migration_repo_config() {
  rm -rf /etc/yum.repos.d/alinux-migration.repo /etc/yum.repos.d/anolis-migration.repo
  yum clean all
  curl "$mirror_site/anolis/migration/anolis-migration.repo" -o /etc/yum.repos.d/anolis-migration.repo || {
    echo "failed to get migration repo"
    exit 1
  }
  sed -i "s|https://mirrors.openanolis.cn|$mirror_site|" /etc/yum.repos.d/anolis-migration.repo
}

install_7to7() {
  out=$(yum -y install centos2anolis-*.an7.noarch --enablerepo=migration 2>&1)
  exit_code=$?
  if [ "$exit_code" -ne 0 ]
  then
    echo "failed to install centos2anolis"
    out="$out\n `ls /etc/yum.repos.d` `cat /etc/yum.conf`"
    report_error_in_jsonfile "install centos2anolis" 103 "$out"
    exit 1
  fi
  disable_migration_repo
}

install_8to8() {
  out=$(yum -y install centos2anolis-*.an8.noarch --enablerepo=migration 2>&1)
  exit_code=$?
  if [ "$exit_code" -ne 0 ]
  then
    echo "failed to install centos2anolis"
    out="$out\n `ls /etc/yum.repos.d` `cat /etc/yum.conf`"
    report_error_in_jsonfile "install centos2anolis" 103 "$out"
    exit 1
  fi
  disable_migration_repo
}

install_7to8() {
  yum install -y python-pip
  yum remove -y python-requests python-urllib3
  /usr/bin/pip2 uninstall requests urllib3 -y 2>/dev/null
  out=$(yum -y install leapp --enablerepo=migration 2>&1)
  exit_code=$?
  if [ "$exit_code" -ne 0 ]
  then
    echo "failed to install leapp"
    out="$out\n `ls /etc/yum.repos.d` `cat /etc/yum.conf`"
    report_error_in_jsonfile "install centos2anolis" 103 "$out"
    exit 1
  fi
  disable_migration_repo
}

main() {
  [ x"$1" = "x7to7" ] || [ x"$1" = "x7to8" ] || [ x"$1" = "x8to8" ] || {
    echo "please run command: $0 7to7, $0 8to8, or $0 7to8"
    exit 1 
  }
  case $1 in
    7to7) jsonfile="/var/log/centostoanolis.json";;
    8to8) jsonfile="/var/log/centostoanolis.json";;
    7to8) jsonfile="/var/tmp/state.json";;
  esac
  check_if_centos_or_rhel
  epel_repo_config
  migration_repo_config
  case $1 in
    7to7) install_7to7;;
    8to8) install_8to8;;
    7to8) install_7to8;;
  esac
}

main $@
