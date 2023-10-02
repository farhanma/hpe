cm health alert -s
/var/log/consoles
/var/log/HOSTS

ssh node_controller

/var/log/

nfags_print_args

/lee/mountain_notes

windom         AMD CPU Rome
antero         AMD CPU Genoa
bard peak      AMD CPU + AMD    GPU
grizzly peak   AMD CPU Milan with NVIDIA GPU A100
castle

/et/cray-pe.d

> filename

truncate -s 0 test.txt
echo -n "" > file.log

chgrp groupA ./folderA
chmod g+rwx  ./folderA

crontab -l
crontab -e

  [minute]  [hours]  [day of month]  [month]  [day of the week] command-to-execute
  {0..59}   {0..23}  {1..31}         {1..12}  {0..7}
                                               │  └─Friday
                                               └─Sunday
    - asterisk  (*)  matches all possible values of a given field
    - slash     (/)  denotes the increment of a given range
    - hyphen    (-)  signifies a continuous range
    - comma     (,)  separates a list of values
    - at        (@)  enables the usage of an inbuilt cron schedule
                     ( e.g., @reboot, @hourly, @daily, @monthly, @yearly )
    - semicolon (;)  appends the commands to the execution list

ssh root@192.168.1.1 'uptime'


I have to set my StoragePass=/var/run/munge/munge.socket.2 in slurmdb.conf and and AccountingStoragePass=/var/run/munge/munge.socket.2
ssh user@remote-host "cat /home/root/file_remote" | diff  - file_local 

slurmd -D -s --conf-server
slurmd --conf-server slurmctl-primary:6817

cm node zypper -n admin install sssd

module help


mail: liam-jon.jones@hpe.com
mail: aniello.esposito@hpe.com

mail: andrei.poenaru@hpe.com
mail: francois.thomas@hpe.com
mail: jan.thorbecke@hpe.com
mail: peter.wauligmann@hpe.com

mail: holly.judge@hpe.com
mail: mandava@hpe.com
mail: alistair.hart@hpe.com
mail: blaine.oliver-jones@hpe.com


dn: cn=swtools,ou=users,dc=hpc,dc=kaust,dc=edu,dc=sa
changetype: modify
add: memberUid
memberUid: khanmh

memberUid: x_thomasf
memberUid: x_esposia
memberUid: jonjl
memberUid: x_wauligp
memberUid: x_thorbej

# getent group swtools
swtools:*:53296:fekis,hadrib,zhuz,kathirn,shaima0d,akbudak,khurrar,x_poenaras,x_thomasf,x_esposia,x_wauligp,x_thorbej

# swtools, users, hpc.kaust.edu.sa
dn: cn=swtools,ou=users,dc=hpc,dc=kaust,dc=edu,dc=sa
objectClass: top
objectClass: posixGroup
description: tagGroup
gidNumber: 53296
cn: swtools
memberUid: khurrar
memberUid: fekis
memberUid: hadrib
memberUid: zhuz
memberUid: kathirn
memberUid: shaima0d
memberUid: akbudak
memberUid: x_poenaras
memberUid: x_thomasf
memberUid: x_esposia
memberUid: jonjl
memberUid: x_wauligp
memberUid: x_thorbej

pdcp -r -w x3110c0s18b0n0,x8000c0s0b0n[0-3],x8000c0s2b0n[0-3],x8000c0s3b0n[0-3],x8000c0s4b0n[0-3],x8000c0s5b0n[0-3],x8000c0s7b0n[0-3] /usr/diags/mpi/impi/2019.4.243/intel64/lib/libmpicxx.so.12 /opt/cray/pe/mpich/8.1.24/ofi/intel/19.0/lib-abi-pre-intel-5.0/libmpicxx.so.12

pdsh -w x3110c0s18b0n0,x8000c0s0b0n[0-3],x8000c0s2b0n[0-3],x8000c0s3b0n[0-3],x8000c0s4b0n[0-3],x8000c0s5b0n[0-3],x8000c0s7b0n[0-3] rm /opt/cray/pe/mpich/8.1.24/ofi/intel/19.0/lib/libmpicxx.so

pdsh -w x3110c0s18b0n0,x8000c0s0b0n[0-3],x8000c0s2b0n[0-3],x8000c0s3b0n[0-3],x8000c0s4b0n[0-3],x8000c0s5b0n[0-3],x8000c0s7b0n[0-3] ln -s /usr/diags/mpi/impi/2019.4.243/intel64/lib/libmpicxx.so /opt/cray/pe/mpich/8.1.24/ofi/intel/19.0/lib/libmpicxx.so

pdsh -w x3110c0s18b0n0,x8000c0s0b0n[0-3],x8000c0s2b0n[0-3],x8000c0s3b0n[0-3],x8000c0s4b0n[0-3],x8000c0s5b0n[0-3],x8000c0s7b0n[0-3] rm /opt/cray/pe/mpich/8.1.24/ofi/intel/19.0/lib-abi-pre-intel-5.0/libmpicxx.so.12

pdsh -w x3110c0s18b0n0,x8000c0s0b0n[0-3],x8000c0s2b0n[0-3],x8000c0s3b0n[0-3],x8000c0s4b0n[0-3],x8000c0s5b0n[0-3],x8000c0s7b0n[0-3] ln -s /usr/diags/mpi/impi/2019.4.243/intel64/lib/libmpicxx.so.12 /opt/cray/pe/mpich/8.1.24/ofi/intel/19.0/lib-abi-mpich/llibmpicxx.so.12

pdsh -w x3110c0s18b0n0,x8000c0s0b0n[0-3],x8000c0s2b0n[0-3],x8000c0s3b0n[0-3],x8000c0s4b0n[0-3],x8000c0s5b0n[0-3],x8000c0s7b0n[0-3] rm /opt/cray/pe/mpich/8.1.24/ofi/intel/19.0/lib-abi-mpich/libmpicxx.so.12

pdcp -w x8000c0s0b0n[0-3],x8000c0s2b0n[0-3],x8000c0s3b0n[0-3],x8000c0s4b0n[0-3],x8000c0s5b0n[0-3],x8000c0s7b0n[0-3] /etc/sssd/sssd.conf /etc/sssd/sssd.conf

#!/bin/sh

MAIL_LIST=mohammed.alfarhan@hpe.com
DATE=`date | cut -d" " -f2-7`
date1=`date +%Y%m%d`
file1=/lustre/hpe/admin/daily_check/logs/email/$date1
touch $file1
SUBJECT="Shaheen 3 TDS daily checks: STREAM. MPI all-to-all, and HPL -- ${DATE}"
echo "
################################################################################
STREAM TRIAD
################################################################################">$file1
echo "" >> $file1
echo "NODE HOSTNAME    MB/s" >> $file1
cat /lustre/hpe/admin/daily_check/logs/stream.20230417-071928/* >> $file1

#!/bin/sh

NCPUS=$(lscpu | awk '/^CPU\(s\)/{print $2}')
HT=$(lscpu | awk '/^Thread\(s\) per core:/{print $4}')
NCORES=$((NCPUS/HT))
STREAM_BIN=/lustre/hpe/admin/daily_check/stream/STREAM/stream_amd_icc2
HOST=$(hostname | cut -f 4-9)
STREAM_TRIAD_RES=$(env OMP_NUM_THREADS=${NCORES} OMP_PLACES=CORES OMP_PROC_BIND=TRUE ${STREAM_BIN} | awk '/Triad/{print $2}')

echo "${HOST}    ${STREAM_TRIAD_RES}" >> "stream-triad_${HOST}.`date +"%Y%m%d-%H%M%S"`"








pdsh -g oss 'tests_str="write read" nobjlo=1 nobjhi=1 thrlo=1024 thrhi=1024 rszlo=4096 rszhi=4096 size=522264 obdfilter-survey' 2>&1 | tee OUT.obdfilter.write+read.txt
pdsh -g oss '                       nobjlo=4 nobjhi=4 thrlo=1408 thrhi=1408                       size=327680 obdfilter-survey' 2>&1 | tee obdfilter-survey_after.$(date +%s)

  nobjlo, nobjhi    number of concurrent objects to create on each iteration, per OST. Starting at nobjlo, the number of objects is doubled on each iteration until nobjhi is reached.
                    they control how many independent objects on the OST will be read or written simultaneously, which is intended to simulate multiple Lustre clients accessing each OST.


#!/bin/bash

# what tests to run (first must be write)
TESTS_TO_RUN=${1:-""}
NUMBER_OF_OBJECTS_LOW=${2:-""}


pdsh -g oss 'tests_str="$TESTS_TO_RUN" nobjlo=1 nobjhi=1 thrlo=1024 thrhi=1024 rszlo=4096 rszhi=4096 size=522264  obdfilter-survey'


#!/bin/bash

while getopts ':abc:h' opt; do
  case "$opt" in
    a)
      echo "Processing option 'a'"
      ;;

    b)
      echo "Processing option 'b'"
      ;;

    c)
      arg="$OPTARG"
      echo "Processing option 'c' with '${OPTARG}' argument"
      ;;

    h)
      echo "Usage: $(basename $0) [-a] [-b] [-c arg]"
      exit 0
      ;;

    :)
      echo -e "option requires an argument.\nUsage: $(basename $0) [-a] [-b] [-c arg]"
      exit 1
      ;;

    ?)
      echo -e "Invalid command option.\nUsage: $(basename $0) [-a] [-b] [-c arg]"
      exit 1
      ;;
  esac
done
shift "$(($OPTIND -1))"


tracd -p 9965 --basic-auth="system,/opt/clmgr/.htpasswd,hpeadmin" /opt/clmgr/trac/system
/opt/clmgr/trac/.htaccess
tracd -s -p 8000 --basic-auth=system,/opt/clmgr/trac/.htpasswd,System /opt/clmgr/trac/system


fmn1:~ # fmn_status --details

x3110c0s18b0n0:~ # grep "gitlab.com" /etc/hosts
172.65.251.78   gitlab.com

egrep write obdfilter-survey.1562314356 | awk '{OST=substr($1,10)-4;printf "%3.3d",OST;for(ii=2;ii<NF;++ii){if($ii=="write"||$ii=="rewrite"||$ii=="read"){printf "%8.2f",$(ii+1)}};printf "\n"}' | sort -Vk1,1



egrep write obdfilter-survey.1562314356 | awk '{OST=substr($1,10)-4;printf "%3.3d",OST;for(ii=2;ii<NF;++ii){if($ii=="write"||$ii=="rewrite"||$ii=="read"){printf "%8.2f",$(ii+1)}};printf "\n"}' | sort -Vk1,1


[farhanma@cdl5 /scratch/farhanma/hpe/shaheen2/ior/e1000/output.20230521-142539]$ ls
out-ior-128-nodes-128x32-4096-procs-job-31986094.ior
[farhanma@cdl5 /scratch/farhanma/hpe/shaheen2/ior/e1000/output.20230521-142539]$ grep "Max Write:" *


