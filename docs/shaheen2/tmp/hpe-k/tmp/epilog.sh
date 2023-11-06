#!/bin/bash

shopt -s extglob
###############################################################################
# Clean up functions
###############################################################################
function clean_tmp ()
{
        #echo "Cleaning /tmp"
        find /tmp ! -user root -exec rm -rf {} \; &> /dev/null
}
function clean_shared_mem ()
{
        #echo "Cleaning shared memory"
        # Clean semaphores
        for i in `ipcs -s | grep -v root | awk '{print $2}' | grep ^[0-9]`
        do
                ipcrm -s $i
        done
        # Clean shared mem
        for i in `ipcs -m | grep -v root | awk '{print $2}' | grep ^[0-9]`
        do
                ipcrm -m $i
        done
}
function clean_dev_shm ()
{
    cwd=$PWD
    cd /dev/shm
    rm  -rf -v !("lldpad.state") &>/dev/null
    cd $cwd
}
function clean_memory_cache ()
{
        sync; echo 3 > /proc/sys/vm/drop_caches
        #sync; sudo /sbin/sysctl vm.drop_caches=3 >/dev/null
}

#Author: Daniel Faraj, HPE
#util functions to log and grab counters

function endLog()
{
  local jid=$1
  logger "END_JOB_$jid"
  echo   "END_JOB_$jid" > /dev/kmsg
  grep . /sys/class/infiniband/mlx5_0/ports/1/counters/* /sys/class/infiniband/mlx5_0/ports/1/hw_counters/* |xargs -I % basename %|sed 's/:/ /' > /tmp/slurm_$jid.end.log

}

function dumpLog()
{
  local jid=$1
  echo "DMESG"
  dmesg -T| sed -n "/START_JOB_$jid/,/END_JOB_$jid/p" |sed '1d; $d'
  echo "SYSLOG"
  sed -n "/journal: START_JOB_$jid/,/journal: END_JOB_$jid/p" /var/log/messages | grep -v "root.* END_JOB" | sed '1d; $d'
  echo "NIC_COUNTERS"
  diff -y /tmp/slurm_$jid.start.log /tmp/slurm_$jid.end.log |grep \| |awk '{print $1,$5-$2}'
  rm -rf /tmp/slurm_$jid.start.log /tmp/slurm_$jid.end.log
}

function checkFlaps()
{
  local  jid=$1
  log=`dmesg | sed -n "/START_JOB_$jid/,/END_JOB_$jid/p" |sed '1d; $d'`

  flap_events=`echo "$log" |  grep -e 'Link down' -e 'Link up' | tail -n2 | sed "s/\[//; s/\]//"`
  if [[ `echo "$flap_events" | head -n1` =~ down && `echo "$flap_events" | tail -n1` =~ up ]]; then
    t0=`echo "$flap_events" | head -n1 |awk '{print $1}'`
    t1=`echo "$flap_events" | tail -n1 |awk '{print $1}'`
    diff=`echo |  awk -v T0=$t0 -v T1=$t1 '{printf "%.0f", T1-T0}'`
    if [ $diff -lt 120 ]; then
      echo "FAIL: Encountered hsn flap.  Offline the node!"
      scontrol update nodename=$(cat /etc/hostname)  state=drain reason="NIC flap"
    fi
  fi
}


###############################################################################
# Main Script
###############################################################################

# make sure no epilog is still active
#while [ `ps ax|grep -c clean-node.sh` -gt 1 ]; do
#       sleep 1
#done
# do not clean /tmp on UAN nodes

SLURM_JOB_NODE_NAME=`hostname | cut -b 1-5`
#if [ "$SLURM_JOB_PARTITION" == "access" ]
if [ "$SLURM_JOB_NODE_NAME" == "plcgm" ]
then
        exit 0

else
        clean_shared_mem
        clean_dev_shm
        clean_memory_cache
        endLog $SLURM_JOBID
        NODE=$(cat /etc/hostname)
        dumpLog $SLURM_JOBID | sed "s/^/$NODE: /g" >> /red/ghw1/slurm-logs/postjob.$SLURM_JOBID.txt
        echo >> /red/ghw1/slurm-logs/postjob.$SLURM_JOBID.txt
        checkFlaps $SLURM_JOBID >> /red/ghw1/slurm-logs/postjob.$SLURM_JOBID.txt
fi


[shaiksj@plcgm04 ghw1]$ cat prolog.sh
#!/bin/bash
shopt -s extglob
###############################################################################
# Clean up functions
###############################################################################
function clean_tmp ()
{
        #echo "Cleaning /tmp"
        find /tmp ! -user root -exec rm -rf {} \; &> /dev/null
}
function clean_shared_mem ()
{
        #echo "Cleaning shared memory"
        # Clean semaphores
        for i in `ipcs -s | grep -v root | awk '{print $2}' | grep ^[0-9]`
        do
                ipcrm -s $i
        done
        # Clean shared mem
        for i in `ipcs -m | grep -v root | awk '{print $2}' | grep ^[0-9]`
        do
                ipcrm -m $i
        done
}
function clean_dev_shm ()
{
    cwd=$PWD
    cd /dev/shm
    rm  -rf -v !("lldpad.state") &>/dev/null
    cd $cwd
}
function clean_memory_cache ()
{
        sync; echo 3 > /proc/sys/vm/drop_caches
        #sync; sudo /sbin/sysctl vm.drop_caches=3 >/dev/null
}

#Author: Daniel Faraj, HPE
#util functions to log and grab counters

function startLog()
{
  local jid=$1
  logger "START_JOB_$jid"
  echo   "START_JOB_$jid" > /dev/kmsg
  grep . /sys/class/infiniband/mlx5_0/ports/1/counters/* /sys/class/infiniband/mlx5_0/ports/1/hw_counters/* |xargs -I % basename %|sed 's/:/ /' > /tmp/slurm_$jid.start.log

}


###############################################################################
# Main Script
###############################################################################

# make sure no epilog is still active
#while [ `ps ax|grep -c clean-node.sh` -gt 1 ]; do
#       sleep 1
#done

# do not clean /tmp on UAN nodes
env > /tmp/env_pro
if [ "$SLURM_JOB_PARTITION" == "access" ]
then
        exit 0

else
        clean_shared_mem
        clean_dev_shm
        clean_memory_cache
        clean_tmp
        startLog $SLURM_JOBID
fi