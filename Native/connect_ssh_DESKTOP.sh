#!/bin/sh
#--remote-debug after gdbserver
DIR='c:&&cd c:\tizen-studio\tools'
CMD_SDB='sdb.exe shell /usr/bin/gdbserver localhost:2727 /opt/usr/home/owner/apps_rw/org.example.test001/bin/test001'
SSH_IP=$1
CMD_SDB_ARGS=$2
SSH_USERNAME=$3
SSH_PASSWORD=$4

echo $CMD_SDB_ARG
FINAL_CMD="${DIR}&&${CMD_SDB} ${CMD_SDB_ARGS}"
sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no $SSH_USERNAME@$SSH_IP $FINAL_CMD

