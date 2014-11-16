#!/usr/bin/python
# -*- coding: utf-8 -*-
# Author: Fæ
# Date: 2014 November
# Reports supporting the Wellcome Images batch upload project
# CC-BY-SA-4.0
#
# Comments
# The colour stuff around urltry() ought to be stripped out, consider it trivial dead legacy code.

import urllib
import pywikibot, re

import MySQLdb
conn = MySQLdb.connect(
    read_default_file = "~/replica.my.cnf",
    host = "commonswiki.labsdb",
    db = "commonswiki_p",
)

cursor = conn.cursor()
site = pywikibot.getSite()

# Most popular categories list
cursor.execute("""
SELECT c.cl_to AS category,
	COUNT(page_id) AS total
FROM page
INNER JOIN categorylinks AS c ON page_id=c.cl_from AND c.cl_to!="Files_from_Wellcome_Images"
INNER JOIN categorylinks AS cc on page_id=cc.cl_from AND cc.cl_to="Files_from_Wellcome_Images"
WHERE c.cl_to NOT REGEXP "Fæ|Files_from|CC-BY|Files_with|test_"
GROUP BY c.cl_to
ORDER BY COUNT(page_id) DESC
LIMIT 50;
""")

table = "{{flatlist|"
for cat, total in cursor.fetchall():
        table+="\n*{{c|"+re.sub("_"," ",cat)+"}}"+" ({:,})".format(total)
table+="\n}}"

pywikibot.setAction("Update")
page = pywikibot.Page(site, "Commons:Batch_uploading/Wellcome_Images/categories")
page.put(table)

sys.exit()

cursor.execute("""SELECT DISTINCT rev_user_text, COUNT(page_title) AS edit_count FROM categorylinks
RIGHT JOIN page ON cl_from = page_id 
LEFT JOIN revision ON page_id = rev_page
WHERE page_namespace=6 AND cl_to = 'Files_from_Wellcome_Images' AND rev_user_text NOT REGEXP '[Bb]ot'
GROUP BY 1
HAVING edit_count>0 
ORDER BY 2 DESC;"""
)

table = []
for userx, count in cursor.fetchall():
	table.append([count, "<abbr title='{} edits to Wellcome Images'>[[User talk:".format(count) + userx + "|" +userx +"]]</abbr>"])

result = "{| class='wikitable sortable'\n!Edits!!#!!Volunteers"
r = [u[1] for u in table if u[0]>999]
result+= "\n|-\n|1000+||" + str(len(r)) +"||"+"{{middot}}".join(r)
r = [u[1] for u in table if u[0]>99 and u[0]<1000]
result+= "\n|-\n|100+ ||" + str(len(r)) +"||"+"{{middot}}".join(r)
r = [u[1] for u in table if u[0]>9 and u[0]<100]
result+= "\n|-\n|10+  ||" + str(len(r)) +"||"+"{{middot}}".join(r)
r = [u[1] for u in table if u[0]<10]
result+= "\n|-\n|     ||" + str(len(r)) +"||"+"{{middot}}".join(r)
result+= "\n|}"

pywikibot.setAction("Update")
page = pywikibot.Page(site, "Commons:Batch_uploading/Wellcome_Images/volunteers")
page.put(result.decode('utf-8'))

# Most edited pages list
cursor.execute("""SELECT DISTINCT page_title, (SELECT COUNT(rev_timestamp) FROM revision WHERE page_id=rev_page) AS Edits
FROM page
JOIN categorylinks ON page_id=cl_from
JOIN revision ON page_id=rev_page
WHERE cl_to = "Files_from_Wellcome_Images"
ORDER BY (SELECT COUNT(rev_timestamp) FROM revision WHERE page_id=rev_page) DESC
LIMIT 24;""")

table = []
for page_title, edits in cursor.fetchall():
	table.append("File:"+page_title+"|<center>"+ str(edits) +" edits</center>")

table = "<gallery>\n"+"\n".join(table) +"\n</gallery>"

pywikibot.setAction("Update")
page = pywikibot.Page(site, "Commons:Batch_uploading/Wellcome_Images/most_edited")
page.put(table)

# Largest images list
cursor.execute("""
SELECT CONCAT("File:",img_name) AS File,
     CONCAT( ROUND(img_width*img_height/1000000), " MP<br><small>", img_width, "x", img_height, " pixels</small>" ) AS Size
     FROM image
     JOIN page ON page_title=img_name
     JOIN categorylinks ON page_id=cl_from
     WHERE cl_to = "Files_from_Wellcome_Images"
     ORDER BY img_width*img_height DESC
     LIMIT 24;
""")

table = []
for File, Size in cursor.fetchall():
	table.append(File+"|<center>"+Size+"</center>")
table="<gallery>\n"+"\n".join(table)+"\n</gallery>"

pywikibot.setAction("Update")
page = pywikibot.Page(site, "Commons:Batch_uploading/Wellcome_Images/largest")
page.put(table)

# Images by usage (using pywikibot rather than sql)
import wikipedia, sys, config, urllib2,re, time
from BeautifulSoup import BeautifulSoup

#	Colours only on mac
Red="\033[0;31m"     #Red
Green="\033[0;32m"   #Green
GreenB="\033[1;32m"	#Green bold
GreenU="\033[4;32m"	#Green underlined
Yellow="\033[0;33m"  #Yellow
Blue="\033[0;34m"    #Blue
Purple="\033[0;35m"  #Purpley
Cyan="\033[0;36m"    #Cyan
White="\033[0;37m"   #White

site = wikipedia.getSite('commons', 'commons')

def urltry(u, headers = { 'User-Agent' : 'Mozilla/5.0' } ):
	countErr=0
	x=''
	while x=='':
			try:
					req = urllib2.Request(u,None,headers)
					x = urllib2.urlopen(req)
					time.sleep(1)
			except:
					x=''
					countErr+=1
					if countErr>300: countErr=300	#	5 minutes between read attempts, eventually
					print Cyan,'** ERROR',countErr,'\n ** Failed to read from '+Yellow+u+Cyan+'\n ** Pause for '+str(countErr*1)+' seconds and try again ['+time.strftime("%H:%M:%S")+']',White
					time.sleep(1*countErr)
	return x

def htmltry(x,u):
		countErr=0
		r=True
		while r:
				try:
						return x.read()
				except:
						x=urltry(u)
						countErr+=1
						if countErr>200:
								p=300
						else:
								p=countErr*2
						print Cyan,'** ERROR',countErr,'\n ** Failed to read xml'
						if countErr==1:
								print Blue+'xml ='+str(x)
								print 'url ='+u+Cyan
						print ' ** Pause for '+str(p)+' seconds and try again'+White
						time.sleep(p)
				else:
						r=False
		return


url =" https://tools.wmflabs.org/glamtools/glamorous.php?doit=1&category=Files_from_Wellcome_Images&use_globalusage=1&show_details=1&projects[wikipedia]=1&projects[wikimedia]=1&projects[wikisource]=1&projects[wikibooks]=1&projects[wikiquote]=1&projects[wiktionary]=1&projects[wikinews]=1&projects[wikivoyage]=1&projects[wikispecies]=1&projects[mediawiki]=1&projects[wikidata]=1&projects[wikiversity]=1&format=xml"


html = htmltry(urltry(url), url)
soup = BeautifulSoup(html)

images = [[i['name'], str(i['usage'])] for i in soup.findAll('image')][:24]
report = "<gallery>\n"
for i in images:
		report += "File:{0}|<center>{1}</center>\n".format(i[0], i[1])
report+="</gallery>"

if len(images)>10: # If less than 10 I think something went wrong.
	pywikibot.setAction("Update")
	page = pywikibot.Page(site, "Commons:Batch_uploading/Wellcome_Images/usage")
	page.put(report)
