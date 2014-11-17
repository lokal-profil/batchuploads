#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
# Grab images from Imagicity 
# Date: March 2013
# Author: Fae, http://j.mp/faewm
# http://commons.wikimedia.org/wiki/Commons:Batch_uploading/Los_Angeles_County_Museum_of_Public_Art
'''

import wikipedia, upload, sys, config, urllib2, urllib, re, string, time, catlib, pagegenerators, os.path, hashlib, pprint
import webbrowser
from BeautifulSoup import BeautifulSoup
from sys import argv
import collections
from time import sleep
from colorama import Fore, Back, Style
from colorama import init
init()

def urltry(u):
	headers = { 'User-Agent' : 'Mozilla/5.0' } # Spoof header
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

def htmltry(u):
		countErr=0
		r=True
		x=urltry(u)
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

site = wikipedia.getSite('commons', 'commons')

baseurl="https://github.com/tategallery/collection/tree/master/artworks/"
html=htmltry(baseurl)
soup = BeautifulSoup(baseurl).findAll('a', {'class'='js-directory-link'})
print [j['href'] for j in soup]
