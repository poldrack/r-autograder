#!/usr/bin/env python
"""
send reports to students automatically

set up postfix gmail relay ala:
https://www.justinsilver.com/technology/osx/send-emails-mac-os-x-postfix-gmail-relay/
http://postfix.1071664.n5.nabble.com/MacOS-High-Sierra-10-13-and-Postfix-relaying-td93421.html

date | mail -s "Test Email" poldrack@gmail.com

"""

import os,glob
import numpy
import json

with open('config.json','r') as f:
    config = json.load(f)

infiles=glob.glob('reports/*.txt')
sunetDict={}
for i in infiles:
    sunetID=os.path.basename(i).split('_')[0]
    if sunetID.find('unknown') > -1:
        print('skipping', sunetID)
        continue
    sunetDict[sunetID]=i

with open('send_report.sh','w') as f:
    for sunetID in sunetDict:
        cmd='mail -s "Results from Week %d PSet automated tests for %s" %s@stanford.edu < %s'%(
            config['week'], sunetID,sunetID,sunetDict[sunetID])
        f.write(cmd+'\n')
        f.write('sleep %d\n'%(1+numpy.random.randint(18)))
