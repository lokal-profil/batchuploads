#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
# Generate Userlist report
# Author:F¾
# Date: 2014-11
# CC-BY-SA-4.0
#
wget -N https://www.dropbox.com/s/w960uxxyn7rb3o7/DBreportUsers.py
jsub -N userlist python ~/pywikibot-compat/DBreportUsers.py
"""
import urllib, re, time, pywikibot
import MySQLdb
from datetime import date
from datetime import datetime

start=time.time()
[y,m,d] = time.strftime('%Y-%m-%d').split('-')
now = date(int(y),int(m),int(d))

conn = MySQLdb.connect(
    read_default_file = "~/replica.my.cnf",
    host = "commonswiki.labsdb",
    db = "commonswiki_p",
)

# list of users with more than 10,000 edits and active in last 180 days
query="""
SELECT user_name,
	user_editcount,
	LEFT(user_registration,4) AS reg,
	MAX(dc.day) AS last_edit,
	GROUP_CONCAT(DISTINCT ug_group SEPARATOR ' ') AS grps,
	CONCAT(ipb_expiry, ' &mdash; ', ipb_reason) AS block
FROM user u
LEFT JOIN user_daily_contribs dc ON dc.user_id=u.user_id
	AND dc.day>DATE_FORMAT(DATE_ADD(NOW(), INTERVAL -180 DAY), "%Y-%m-%d")
LEFT JOIN user_groups ON u.user_id=ug_user
LEFT JOIN ipblocks ON ipb_user=u.user_id
WHERE user_editcount>=10000
GROUP BY user_name
HAVING MAX(dc.day)!="None"
ORDER BY user_editcount DESC;
"""

cursor = conn.cursor()
cursor.execute(query)

table = []
for user, editcount, reg, last_edit, group, block in cursor.fetchall():
		if reg=="NULL": reg = 'NA'
		groups=[]
		for g in ['sysop','OTRS-member', 'bot', 'bureaucrat', 'oversight', 'Image-reviewer']:
				if re.search(g, str(group)): groups.append(g)
		if block=="NULL" or block is None:
				block=""
		else:
				if re.search("\d{14}", block):
						bdate=re.search("\d{14}", block).group()
						if bdate is not None and bdate!='None':
								bdate=datetime.strptime(bdate, "%Y%m%d%H%M%S").strftime("%A %d %B %Y, %H:%M")
								block=re.sub("\d{14}", bdate, block)
		table.append([user, int(editcount), str(last_edit), '.'.join(groups), str(reg), block])

# Admins with low activity
query="""
SELECT
	user_name AS Name,
	SUM(IF(dc.day>DATE_FORMAT(DATE_ADD(NOW(), INTERVAL -365 DAY), "%Y-%m-%d"), dc.contribs, 0)) AS 12months,
	SUM(IF(dc.day>DATE_FORMAT(DATE_ADD(NOW(), INTERVAL -830 DAY), "%Y-%m-%d"), dc.contribs, 0)) AS 24months,
	GROUP_CONCAT(DISTINCT g.ug_group SEPARATOR ', ') AS groups,
	LEFT(user_registration,4) AS reg,
	user_editcount AS Total
FROM user u
INNER JOIN user_groups g ON u.user_id=g.ug_user
LEFT JOIN user_daily_contribs dc ON u.user_id=dc.user_id
WHERE
	g.ug_group IN ('sysop','checkuser','bureaucrat','OTRS-member')
	AND (SELECT count(*) from user_groups gg WHERE u.user_id=gg.ug_user AND gg.ug_group='sysop')=1
GROUP BY user_name
HAVING 12months<100 AND 24months<200
ORDER BY 12months;
"""
cursor.execute(query)
table_admins=[]
for user, yearone, yeartwo, grps, reg, total in cursor.fetchall():
		table_admins.append([user, int(yearone), int(yeartwo), grps, str(reg), int(total)])

report="{{anchor|top}}\n{|class='wikitable sortable'\n!#!!User!!Edit count!!Last edit!!Admin!!OTRS!!Reg"
breport="{{anchor|bots}}\n{|class='wikitable sortable' style='background:lightblue;'\n!#!!User!!Edit count!!Last edit!!Admin!!OTRS!!Reg"
oreport="\n{{anchor|lostusers}}\n{|class='wikitable sortable' style='background:lightyellow;'\n!#!!User!!Edit count!!Last edit!!Admin!!OTRS!!Reg\n|+Users with more than 10,000 edits inactive for more than 30 days (and less than 180)"
count=0;bcount=0;ocount=0
for row in table:
		[y,m,d]=row[2].split('-')
		ledate = date(int(y),int(m),int(d))
		daysago= (now-ledate).days
		rowtext ="\n|-\n| {0:0>4} "
		# User
		if row[5]=="" or row[5] is None:
				rowtext+="|| "+row[0].decode('utf-8')
		else:
				rowtext+="|| <abbr title='Account blocked until "+row[5]+"' style='color:red;'>"+row[0].decode('utf-8')+"</abbr>"
		rowtext+=" <small style='float:right'>[[Special:CentralAuth/"+re.sub(" ","_", row[0].decode('utf-8'))+"|GAM]]</small>"
		# Edit count
		rowtext+="||align=right|{:,}".format(row[1])
		# Last edit
		rowtext+="||align=center| "+row[2]+" "
		# Groups
		rowtext+="||align=center|"
		if re.search('bureaucrat', row[3]):
				rowtext+='<abbr title="Bureaucrat" style="color:red">Y</abbr>'
		elif re.search('sysop', row[3]):
				rowtext+='Y'
		else:
				rowtext+=' '
		if re.search('oversight', row[3]): rowtext+='<abbr title="Oversight" style="color:blue">O</abbr>'
		rowtext+="||align=center|"
		if re.search('OTRS', row[3]):
				rowtext+='Y'
		else:
				rowtext+=' '
		if row[4]=="None":
				rowtext+="||align=center|<div style='color:silver'>"+row[4]+"</div>"
		else:
				rowtext+="||align=center|"+row[4]
		if daysago>30:
				if daysago<=180:
						ocount+=1
						rowtext=rowtext.format(ocount)
						oreport+=rowtext
		elif re.search("bot", row[3]) or re.search("[\s\-]bot|\bbot|bot\b|Bot| AWB|Delinker|Wikimedia Commons",row[0]):
				bcount+=1
				rowtext=rowtext.format(bcount)
				breport+=rowtext
		else:
				count+=1
				rowtext=rowtext.format(count)
				report+=rowtext
report+="\n|}"
breport+="\n|}"
oreport+="\n|}"

areport="{{anchor|admins}}\n{|class='wikitable sortable' style='background:lightgreen;'\n!#!!User!!12 months!!24 months!!Groups!!Reg!!Total\n|+Administrators with fewer than 100 edits in the past year and fewer than 200 edits in the past 2 years."
acount=0
for row in table_admins:
		acount+=1
		rowtext="\n|-\n| {0:0>2} ".format(acount)
		rowtext+="||"+row[0].decode('utf-8')+" <small style='float:right'>[[Special:CentralAuth/"+re.sub(" ","_", row[0].decode('utf-8'))+"|GAM]]</small>"
		rowtext+="||align=right|{:,}".format(row[1])
		rowtext+="||align=right|{:,}".format(row[2])
		rowtext+="||align=center| "+re.sub(", sysop|sysop, |^sysop$","", row[3])
		if row[4]=="None":
				rowtext+="||align=center|<div style='color:silver'>"+row[4]+"</div>"
		else:
				rowtext+="||align=center|"+row[4]
		rowtext+="||align=right|{:,}".format(row[5])
		areport+=rowtext
areport+="\n|}"

hreport=u'''''Report last updated on {{subst:today}}

Total number of [[#top|users active]] in the last 30 days on Wikimedia Commons with more than 10,000 edits is '''+str(count)+''', there are [[#bots| '''+str(bcount)+''' active bots]], '''+ str(ocount) +''' [[#lostusers|recently inactive users]] and [[#admins|'''+str(acount)+''' administrators]] with low activity over two years.
'''

end=time.time()-start
endm=int(end/60)
ends=end % 60
if endm>0:
		endm=str(endm)+"m "
else:
		endm=""
endline=u"Report completed: "+time.strftime("%a, %d %b %Y %H:%M")+u" ("+endm+"{:0.1f}".format(ends)+"s runtime)."
#print '',"\n\n",endline,"\n\n",''
endline=("\n<small>"+endline+"</small>").encode('utf-8')

site=pywikibot.getSite("commons","commons")
out=pywikibot.Page(site, u"User:F\u00E6/Userlist")
pywikibot.setAction("Update report with {:,} active users".format(count))
out.put(hreport+report+'\n\n'+oreport+'\n\n'+breport+'\n\n'+areport+endline)
