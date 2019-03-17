#!/bin/bash
# Merge all logs from timestamped directory into a single log for each person.
rm -r merged
mkdir merged
for i in log-*; do cd $i; for file in *.txt; do cat $file >> ../merged/$file; done; cd ..; done
cd merged
for i in *.txt; do cat $i | sort | uniq > $i.uniqorder; done
cd ..
