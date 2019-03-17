#!/bin/bash
# Grabs the /log directory contents from the machine running
# the fetcher and puts it in a local timestamped directory.
scp -r rez@openwrt.lan:/log log-`date +%s`
ssh rez@openwrt.lan rm /log/*.txt
