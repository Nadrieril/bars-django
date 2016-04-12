#!/bin/sh
cd $(dirname $0)
LOGFILE=../cron.log

. venv/bin/activate

date >> $LOGFILE
python manage.py runscript agios >> $LOGFILE 2>&1
