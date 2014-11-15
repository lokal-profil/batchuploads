#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
# Check and update Xeno-Canto audio files
# Date: July 2013
# Author: Fae, http://j.mp/faewm
# CC-BY-SA
'''

import wikipedia, upload, sys, config, urllib2, urllib, re, string, time, catlib, pagegenerators, os.path, hashlib, pprint
import json,subprocess
from BeautifulSoup import BeautifulSoup
from sys import argv, stdout
import collections
from time import sleep
from os import remove
from colorama import Fore, Back, Style, init
init()

site = wikipedia.getSite('commons', 'commons')

subs=[['%20',' '],['%28','('],['%29',')'],['%2C',','],['%3A',':']]
def pquote(s):
		s=urllib.quote(s)
		for c in range(len(subs)):
				s=re.sub(subs[c][0],subs[c][1],s)
		return s

def gettag(tag,name):
		if tag=='class':
				try:
						r=string.split(html,'class="'+name+'"')[1]
						r=string.split(r,'>')[1]
						r=string.split(r,'<')[0]
				except:
						return ''
				return r
		if tag=='td':
				try:
						r=string.split(html,'<tr><td>'+name+'</td><td>')[1]
						r=string.split(r,'</td>')[0]
				except:
						return ''
        	return r
		return ''

def p(tag, val):	#	Print nicely
		if len(val)>1:
				print Fore.CYAN+tag+" : "+Fore.YELLOW+val+Fore.WHITE
		return
def pp(tag, val):	#	Print nicely
		if len(val)>0:
				print Fore.CYAN+tag+" : "+Fore.YELLOW+val+Fore.WHITE
		else:
				print Fore.CYAN+tag+Fore.RED+"** Missing data **"+Fore.WHITE
		return

def trim(s):			#	Trim leading and trailing spaces
	return re.sub('^[\s\r\t\f\n]*|[\s\r\t\f\n]*$','',s)

def up(filename, pagetitle, desc):
    url = filename
    keepFilename=True        #set to True to skip double-checking/editing destination filename
    verifyDescription=False    #set to False to skip double-checking/editing description => change to bot-mode
    targetSite = wikipedia.getSite('commons', 'commons')
    bot = upload.UploadRobot(url, description=desc, useFilename=pagetitle, keepFilename=keepFilename, verifyDescription=verifyDescription, targetSite = targetSite)
    bot.upload_image(debug=True)
    		
def urltry(u):
	countErr=0
	x=''
	while x=='':
			try:
					x = urllib2.urlopen(u)
					time.sleep(1)
			except:
					x=''
					countErr+=1
					if countErr>20: countErr=20
					print Fore.CYAN,'** ERROR',countErr,'\n ** Failed to read from '+u+'\n ** Pause for '+str(countErr*1)+' seconds and try again'+Fore.WHITE
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
						print Fore.CYAN,'** ERROR',countErr,'\n ** Failed to read xml'
						if countErr==1:
								print Blue+'xml ='+str(x)
								print 'url ='+u+Fore.CYAN
						print ' ** Pause for '+str(p)+' seconds and try again'+Fore.WHITE
						time.sleep(p)
				else:
						r=False
		return

def xmlfind(item):
		if data.find('<metadata name="'+item)>-1:
				return data.split('<metadata name="'+item+'" value="')[1].split('"')[0]
		else:
				return ''

def gettag(h):
  #<span class="link-11"><a href="/tag/thunderstorm" rel="tag" title="">Thunderstorm</a></span>
  t=re.split('href="/tag/[^"]*" rel="tag" title="">',h)
  for i in range(len(t)):
  	  t[i]=t[i].split('<')[0]
  t[0]=re.sub('^\s*|\s$','',t[0])
  if t[0]=='': t.pop(0)
  return ", ".join(t)

def getatt(t,h):
	if h.find('>'+t+':</th>')==-1: return ''
	r=re.split('<th scope="row"[^>]*>'+t+':</th>',h)[1].split('</td>')[0]
	r=re.sub('[\n\r\t\s]',' ',r)
	r=re.sub('\s+',' ',r)
	return re.sub('^\s*|<[^>]*>|\s*$','',r)

def getcat(h):
  # <div class="item-list"><ul><li><a href="/type/natural">Natural</a></li><li><a href="/type/characteristic">Characteristic</a></li></ul></div>
  if h.find('<div class="terms">Type</div>')==-1: return '[[Category:Pdsounds.org]]'
  r=h.split('<div class="terms">Type</div>')[1]
  r=r.split('class="item-list"><ul>')[1]
  r=r.split('</a></li></ul>')[0]
  r=r.split('</a></li>')
  c=''
  for i in range(len(r)):
    r[i]=re.sub('<[^>]*?>','',r[i])
  return ", ".join(r)

def dupcheck(ff):	#	Using the SHA1 checksum, find if the file is already uploaded to Commons
		#df=urllib2.urlopen(ff)
		df=open(ff,'rb')
		notread=True	#	Try to deal with socket.timeout
		while notread:
			notread=False
			try:
				sha1 = hashlib.sha1(df.read()).hexdigest()
			except:
				notread=True
				print Fore.RED+"Trouble getting SHA1 for file, trying again in 2 seconds."
				sleep(2)
				df=urllib2.urlopen(ff)
		#print Fore.CYAN+'SHA1='+sha1
		u="http://commons.wikimedia.org/w/api.php?action=query&list=allimages&format=xml&ailimit=1&aiprop=sha1&aisha1="+sha1
		notread=True
		while notread:
				notread=False
				try:
						x=urllib2.urlopen(u)
				except:
						notread=True
						print Fore.RED+"Trouble reading",u
						time.sleep(5)
		xd=x.read()
		x.close()
		if xd.find("<img")>-1:
				t=xd.split('title="')[1].split('"')[0]
				return True,t
		return False,''

# Check if a file title is already used on commons
def nameused(name):
		u="http://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo&format=xml&titles=File:"+urllib.quote(name)
		x=urllib2.urlopen(u).read()
		if x.find('<imageinfo>')>-1:
				return True
		return False

def trimtags(s):
	return trim(re.sub('<[^>]*?>','',s))

def titlecase(s):
	s=re.sub('&#0?39;',"'",s)
	s=re.sub('&amp;','and',s)
	s=re.sub(':','-',s)
	words=s.split(" ")
	smallwords=['at','the','of','by','a','during','work','on','in','and']
	bigwords=['UK','US','USA','U\.S\.','H\.M\.S\.','HMS', 'RAF', 'R\.A\.F\.', 'YWCA', 'YMCA']
	for i in range(len(words)):
	  staybig=False
	  for j in bigwords:
				if re.search('^'+j+'[,\.;\(\)\-]?',words[i]):
						staybig=True
						continue
	  if not staybig:
				words[i]=words[i][0:1]+words[i][1:].lower()
	  else:
				continue
	  if i==0:
			continue
	  else:
			for j in smallwords:
				if words[i].lower()==j: words[i]=words[i].lower()
				continue
	return ' '.join(words)
def oddchars(s):
		s=re.sub(':',"-",s)
		s=re.sub('£',"&pound;",s)
		s=re.sub('ÂGBP',"&pound;",s)
		s=re.sub('\u00E4','&auml;',s)
		s=re.sub('\u00FC','&uuml;',s)
		s=re.sub('\u00E2','&acirc;',s)
		s=re.sub('\u2019',"'",s)
		#s=re.sub('\xA4','&euro;',s)
		s=re.sub("\xC2\xA0",'&nbsp;',s)
		s=re.sub("\xC2\xA1",'&iexcl;',s)
		s=re.sub("\xC2\xA2",'&cent;',s)
		s=re.sub("\xC2\xA3",'&pound;',s)
		s=re.sub("\xC2\xA4",'&curren;',s)
		s=re.sub("\xC2\xA5",'&yen;',s)
		s=re.sub("\xC2\xA6",'&brvbar;',s)
		s=re.sub("\xC2\xA7",'&sect;',s)
		s=re.sub("\xC2\xA8",'&uml;',s)
		s=re.sub("\xC2\xA9",'&copy;',s)
		s=re.sub("\xC2\xAA",'&ordf;',s)
		s=re.sub("\xC2\xAB",'&laquo;',s)
		s=re.sub("\xC2\xAC",'&not;',s)
		s=re.sub("\xC2\xAD",'&shy;',s)
		s=re.sub("\xC2\xAE",'&reg;',s)
		s=re.sub("\xC2\xAF",'&macr;',s)
		s=re.sub("\xC2\xB0",'&deg;',s)
		s=re.sub("\xC2\xB1",'&plusmn;',s)
		s=re.sub("\xC2\xB2",'&sup2;',s)
		s=re.sub("\xC2\xB3",'&sup3;',s)
		s=re.sub("\xC2\xB4",'&acute;',s)
		s=re.sub("\xC2\xB5",'&micro;',s)
		s=re.sub("\xC2\xB6",'&para;',s)
		s=re.sub("\xC2\xB7",'&middot;',s)
		s=re.sub("\xC2\xB8",'&cedil;',s)
		s=re.sub("\xC2\xB9",'&sup1;',s)
		s=re.sub("\xC2\xBA",'&ordm;',s)
		s=re.sub("\xC2\xBB",'&raquo;',s)
		s=re.sub("\xC2\xBC",'&frac14;',s)
		s=re.sub("\xC2\xBD",'&frac12;',s)
		s=re.sub("\xC2\xBE",'&frac34;',s)
		s=re.sub("\xC2\xBF",'&iquest;',s)
		s=re.sub("\xC3\x80",'&Agrave;',s)
		s=re.sub("\xC3\x81",'&Aacute;',s)
		s=re.sub("\xC3\x82",'&Acirc;',s)
		s=re.sub("\xC3\x83",'&Atilde;',s)
		s=re.sub("\xC3\x84",'&Auml;',s)
		s=re.sub("\xC3\x85",'&Aring;',s)
		s=re.sub("\xC3\x86",'&AElig;',s)
		s=re.sub("\xC3\x87",'&Ccedil;',s)
		s=re.sub("\xC3\x88",'&Egrave;',s)
		s=re.sub("\xC3\x89|\xc9",'&Eacute;',s)
		s=re.sub("\xC3\x8A",'&Ecirc;',s)
		s=re.sub("\xC3\x8B",'&Euml;',s)
		s=re.sub("\xC3\x8C",'&Igrave;',s)
		s=re.sub("\xC3\x8D",'&Iacute;',s)
		s=re.sub("\xC3\x8E",'&Icirc;',s)
		s=re.sub("\xC3\x8F",'&Iuml;',s)
		s=re.sub("\xC3\x90",'&ETH;',s)
		s=re.sub("\xC3\x91",'&Ntilde;',s)
		s=re.sub("\xC3\x92",'&Ograve;',s)
		s=re.sub("\xC3\x93",'&Oacute;',s)
		s=re.sub("\xC3\x94",'&Ocirc;',s)
		s=re.sub("\xC3\x95",'&Otilde;',s)
		s=re.sub("\xC3\x96",'&Ouml;',s)
		s=re.sub("\xC3\x97",'&times;',s)
		s=re.sub("\xC3\x98",'&Oslash;',s)
		s=re.sub("\xC3\x99",'&Ugrave;',s)
		s=re.sub("\xC3\x9A",'&Uacute;',s)
		s=re.sub("\xC3\x9B",'&Ucirc;',s)
		s=re.sub("\xC3\x9C",'&Uuml;',s)
		s=re.sub("\xC3\x9D",'&Yacute;',s)
		s=re.sub("\xC3\x9E",'&THORN;',s)
		s=re.sub("\xC3\x9F",'&szlig;',s)
		s=re.sub("\xC3\xA0|\xe0",'&agrave;',s)
		s=re.sub("\xC3\xA1|\xe1",'&aacute;',s)
		s=re.sub("\xC3\xA2",'&acirc;',s)
		s=re.sub("\xC3\xA3",'&atilde;',s)
		s=re.sub("\xC3\xA4",'&auml;',s)
		s=re.sub("\xC3\xA5",'&aring;',s)
		s=re.sub("\xC3\xA6",'&aelig;',s)
		s=re.sub("\xC3\xA7|\xe7",'&ccedil;',s)
		s=re.sub("\xC3\xA8",'&egrave;',s)
		s=re.sub("\xC3\xA9",'&eacute;',s)
		s=re.sub("\xC3\xAA|\xea",'&ecirc;',s)
		s=re.sub("\xC3\xAB|\xeb",'&euml;',s)
		s=re.sub("\xC3\xAC",'&igrave;',s)
		s=re.sub("\xC3\xAD|\xed",'&iacute;',s)
		s=re.sub("\xC3\xAE|\xee",'&icirc;',s)
		s=re.sub("\xC3\xAF|\xEF",'&iuml;',s)
		s=re.sub("\xC3\xB0",'&eth;',s)
		s=re.sub("\xC3\xB1",'&ntilde;',s)
		s=re.sub("\xC3\xB2",'&ograve;',s)
		s=re.sub("\xC3\xB3|\xf3",'&oacute;',s)
		s=re.sub("\xC3\xB4",'&ocirc;',s)
		s=re.sub("\xC3\xB5",'&otilde;',s)
		s=re.sub("\xC3\xB6|\xF6",'&ouml;',s)	#	http://www.fileformat.info/info/unicode/char/f6/index.htm
		s=re.sub("\xC3\xB7",'&divide;',s)
		s=re.sub("\xC3\xB8",'&oslash;',s)
		s=re.sub("\xC3\xB9",'&ugrave;',s)
		s=re.sub("\xC3\xBA|\xfa",'&uacute;',s)
		s=re.sub("\xC3\xBB",'&ucirc;',s)
		s=re.sub("\xC3\xBC|\xfc",'&uuml;',s)
		s=re.sub("\xC3\xBD",'&yacute;',s)
		s=re.sub("\xC3\xBE",'&thorn;',s)
		s=re.sub("\xC3\xBF",'&yuml;',s)
		#s=re.sub("\xc3",'',s)	#debug - a rubbish fix
		s=re.sub("\xf8",'&oslash;',s)	#debug - another unsure fix
		# Latin Extended-A
		s=re.sub("\xC5\x92",'&OElig;',s)
		s=re.sub("\xC5\x93",'&oelig;',s)
		s=re.sub("\xC5\xA0",'&Scaron;',s)
		s=re.sub("\xC5\xA1",'&scaron;',s)
		s=re.sub("\xC5\xB8",'&Yuml;',s)
		s=re.sub("\xc5\xab",'&#x16b;',s) # u macron http://www.fileformat.info/info/unicode/char/16b/index.htm
		s=re.sub("\xc5\x8c",'&#x14c;',s) # o macron
		s=re.sub("\xC5\x8d",'&#x14d;',s) # O macron
		# Spacing Modifier Letters
		s=re.sub("\xCB\x86",'&circ;',s)
		s=re.sub("\xCB\x9C",'&tilde;',s)
		# General Punctuation
		s=re.sub("\xE2\x80\x82",'&ensp;',s)
		s=re.sub("\xE2\x80\x83",'&emsp;',s)
		s=re.sub("\xE2\x80\x89",'&thinsp;',s)
		s=re.sub("\xE2\x80\x8C",'&zwnj;',s)
		s=re.sub("\xE2\x80\x8D",'&zwj;',s)
		s=re.sub("\xE2\x80\x8E",'&lrm;',s)
		s=re.sub("\xE2\x80\x8F",'&rlm;',s)
		s=re.sub("\xE2\x80\x93",'&ndash;',s)
		s=re.sub("\xE2\x80\x94",'&mdash;',s)
		s=re.sub("\xE2\x80\x98",'&lsquo;',s)
		s=re.sub("\xE2\x80\x99",'&rsquo;',s)
		s=re.sub("\xE2\x80\x9A",'&sbquo;',s)
		s=re.sub("\xE2\x80\x9C",'&ldquo;',s)
		s=re.sub("\xE2\x80\x9D",'&rdquo;',s)
		s=re.sub("\xE2\x80\x9E",'&bdquo;',s)
		s=re.sub("\xE2\x80\xA0",'&dagger;',s)
		s=re.sub("\xE2\x80\xA1",'&Dagger;',s)
		s=re.sub("\xE2\x80\xB0",'&permil;',s)
		s=re.sub("\xE2\x80\xB9",'&lsaquo;',s)
		s=re.sub("\xE2\x80\xBA",'&rsaquo;',s)
		s=re.sub("\xE2\x82\xAC",'&euro;',s)
		# Latin Extended-B
		s=re.sub("\xC6\x92",'&fnof;',s)
		# Greek
		s=re.sub("\xCE\x91",'&Alpha;',s)
		s=re.sub("\xCE\x92",'&Beta;',s)
		s=re.sub("\xCE\x93",'&Gamma;',s)
		s=re.sub("\xCE\x94",'&Delta;',s)
		s=re.sub("\xCE\x95",'&Epsilon;',s)
		s=re.sub("\xCE\x96",'&Zeta;',s)
		s=re.sub("\xCE\x97",'&Eta;',s)
		s=re.sub("\xCE\x98",'&Theta;',s)
		s=re.sub("\xCE\x99",'&Iota;',s)
		s=re.sub("\xCE\x9A",'&Kappa;',s)
		s=re.sub("\xCE\x9B",'&Lambda;',s)
		s=re.sub("\xCE\x9C",'&Mu;',s)
		s=re.sub("\xCE\x9D",'&Nu;',s)
		s=re.sub("\xCE\x9E",'&Xi;',s)
		s=re.sub("\xCE\x9F",'&Omicron;',s)
		s=re.sub("\xCE\xA0",'&Pi;',s)
		s=re.sub("\xCE\xA1",'&Rho;',s)
		s=re.sub("\xCE\xA3",'&Sigma;',s)
		s=re.sub("\xCE\xA4",'&Tau;',s)
		s=re.sub("\xCE\xA5",'&Upsilon;',s)
		s=re.sub("\xCE\xA6",'&Phi;',s)
		s=re.sub("\xCE\xA7",'&Chi;',s)
		s=re.sub("\xCE\xA8",'&Psi;',s)
		s=re.sub("\xCE\xA9",'&Omega;',s)
		s=re.sub("\xCE\xB1",'&alpha;',s)
		s=re.sub("\xCE\xB2",'&beta;',s)
		s=re.sub("\xCE\xB3",'&gamma;',s)
		s=re.sub("\xCE\xB4",'&delta;',s)
		s=re.sub("\xCE\xB5",'&epsilon;',s)
		s=re.sub("\xCE\xB6",'&zeta;',s)
		s=re.sub("\xCE\xB7",'&eta;',s)
		s=re.sub("\xCE\xB8",'&theta;',s)
		s=re.sub("\xCE\xB9",'&iota;',s)
		s=re.sub("\xCE\xBA",'&kappa;',s)
		s=re.sub("\xCE\xBB",'&lambda;',s)
		s=re.sub("\xCE\xBC",'&mu;',s)
		s=re.sub("\xCE\xBD",'&nu;',s)
		s=re.sub("\xCE\xBE",'&xi;',s)
		s=re.sub("\xCE\xBF|\U014D",'o',s)#&omacron;
		s=re.sub("\xCF\x80",'&pi;',s)
		s=re.sub("\xCF\x81",'&rho;',s)
		s=re.sub("\xCF\x82",'&sigmaf;',s)
		s=re.sub("\xCF\x83",'&sigma;',s)
		s=re.sub("\xCF\x84",'&tau;',s)
		s=re.sub("\xCF\x85",'&upsilon;',s)
		s=re.sub("\xCF\x86",'&phi;',s)
		s=re.sub("\xCF\x87",'&chi;',s)
		s=re.sub("\xCF\x88",'&psi;',s)
		s=re.sub("\xCF\x89",'&omega;',s)
		s=re.sub("\xCF\x91",'&thetasym;',s)
		s=re.sub("\xCF\x92",'&upsih;',s)
		s=re.sub("\xCF\x96",'&piv;',s)
		# General Punctuation
		s=re.sub("\xE2\x80\xA2",'&bull;',s)
		s=re.sub("\xE2\x80\xA6",'&hellip;',s)
		s=re.sub("\xE2\x80\xB2",'&prime;',s)
		s=re.sub("\xE2\x80\xB3",'&Prime;',s)
		s=re.sub("\xE2\x80\xBE",'&oline;',s)
		s=re.sub("\xE2\x81\x84",'&frasl;',s)
		# Letterlike Symbols
		s=re.sub("\xE2\x84\x98",'&weierp;',s)
		s=re.sub("\xE2\x84\x91",'&image;',s)
		s=re.sub("\xE2\x84\x9C",'&real;',s)
		s=re.sub("\xE2\x84\xA2",'&trade;',s)
		s=re.sub("\xE2\x84\xB5",'&alefsym;',s)
		# Arrows
		s=re.sub("\xE2\x86\x90",'&larr;',s)
		s=re.sub("\xE2\x86\x91",'&uarr;',s)
		s=re.sub("\xE2\x86\x92",'&rarr;',s)
		s=re.sub("\xE2\x86\x93",'&darr;',s)
		s=re.sub("\xE2\x86\x94",'&harr;',s)
		s=re.sub("\xE2\x86\xB5",'&crarr;',s)
		s=re.sub("\xE2\x87\x90",'&lArr;',s)
		s=re.sub("\xE2\x87\x91",'&uArr;',s)
		s=re.sub("\xE2\x87\x92",'&rArr;',s)
		s=re.sub("\xE2\x87\x93",'&dArr;',s)
		s=re.sub("\xE2\x87\x94",'&hArr;',s)
		# Mathematical Operators
		s=re.sub("\xE2\x88\x80",'&forall;',s)
		s=re.sub("\xE2\x88\x82",'&part;',s)
		s=re.sub("\xE2\x88\x83",'&exist;',s)
		s=re.sub("\xE2\x88\x85",'&empty;',s)
		s=re.sub("\xE2\x88\x87",'&nabla;',s)
		s=re.sub("\xE2\x88\x88",'&isin;',s)
		s=re.sub("\xE2\x88\x89",'&notin;',s)
		s=re.sub("\xE2\x88\x8B",'&ni;',s)
		s=re.sub("\xE2\x88\x8F",'&prod;',s)
		s=re.sub("\xE2\x88\x91",'&sum;',s)
		s=re.sub("\xE2\x88\x92",'&minus;',s)
		s=re.sub("\xE2\x88\x97",'&lowast;',s)
		s=re.sub("\xE2\x88\x9A",'&radic;',s)
		s=re.sub("\xE2\x88\x9D",'&prop;',s)
		s=re.sub("\xE2\x88\x9E",'&infin;',s)
		s=re.sub("\xE2\x88\xA0",'&ang;',s)
		s=re.sub("\xE2\x88\xA7",'&and;',s)
		s=re.sub("\xE2\x88\xA8",'&or;',s)
		s=re.sub("\xE2\x88\xA9",'&cap;',s)
		s=re.sub("\xE2\x88\xAA",'&cup;',s)
		s=re.sub("\xE2\x88\xAB",'&int;',s)
		s=re.sub("\xE2\x88\xB4",'&there4;',s)
		s=re.sub("\xE2\x88\xBC",'&sim;',s)
		s=re.sub("\xE2\x89\x85",'&cong;',s)
		s=re.sub("\xE2\x89\x88",'&asymp;',s)
		s=re.sub("\xE2\x89\xA0",'&ne;',s)
		s=re.sub("\xE2\x89\xA1",'&equiv;',s)
		s=re.sub("\xE2\x89\xA4",'&le;',s)
		s=re.sub("\xE2\x89\xA5",'&ge;',s)
		s=re.sub("\xE2\x8A\x82",'&sub;',s)
		s=re.sub("\xE2\x8A\x83",'&sup;',s)
		s=re.sub("\xE2\x8A\x84",'&nsub;',s)
		s=re.sub("\xE2\x8A\x86",'&sube;',s)
		s=re.sub("\xE2\x8A\x87",'&supe;',s)
		s=re.sub("\xE2\x8A\x95",'&oplus;',s)
		s=re.sub("\xE2\x8A\x97",'&otimes;',s)
		s=re.sub("\xE2\x8A\xA5",'&perp;',s)
		s=re.sub("\xE2\x8B\x85",'&sdot;',s)
		# Miscellaneous Technical
		s=re.sub("\xE2\x8C\x88",'&lceil;',s)
		s=re.sub("\xE2\x8C\x89",'&rceil;',s)
		s=re.sub("\xE2\x8C\x8A",'&lfloor;',s)
		s=re.sub("\xE2\x8C\x8B",'&rfloor;',s)
		s=re.sub("\xE2\x8C\xA9",'&lang;',s)
		s=re.sub("\xE2\x8C\xAA",'&rang;',s)
		# Geometric Shapes
		s=re.sub("\xE2\x97\x8A",'&loz;',s)
		# Miscellaneous Symbols
		s=re.sub("\xE2\x99\xA0",'&spades;',s)
		s=re.sub("\xE2\x99\xA3",'&clubs;',s)
		s=re.sub("\xE2\x99\xA5",'&hearts;',s)
		s=re.sub("\xE2\x99\xA6",'&diams;',s)
		s=re.sub("\xE8",'&egrave;',s)
		s=re.sub("\xE9",'&eacute;',s)
		return s
def asciichars(s):
		s=re.sub(r'&([A-Za-z])(uml|circ|grave|acute|macron|cedil|tilde|ring|slash);',r'\1',s)
		# -a-
		s=re.sub('Â','A',s)
		s=re.sub(u'\xC3',"A",s)
		s=re.sub("&#193;",'A',s) # Á
		s=re.sub("&#192;",'A',s) # A grave
		s=re.sub("&#198;",'Ae',s) # AE ligature
		s=re.sub(u'\u00E4','a',s)
		s=re.sub(u'\u00E2','a',s)
		s=re.sub("&#196;",'a',s) # ä
		s=re.sub("&#197;",'a',s)	# å
		s=re.sub("&#226;",'a',s) # a circ
		s=re.sub(u"\xe2",'a',s) # a circ
		s=re.sub("&#228;",'a',s)	# ä
		s=re.sub("&#229;",'a',s) # å
		s=re.sub("&#230;",'ae',s) # æ
		s=re.sub("&#225;",'a',s) # á
		s=re.sub("&#224;",'a',s) # a grave
		s=re.sub("&#228;",'a',s) # ä
		# -c-
		s=re.sub("&#231;",'c',s) # c cedila
		s=re.sub("&#199;",'C',s) # c cedila
		s=re.sub(u'\xE7',"c",s) # c cedila
		# -d-
		s=re.sub("&#240;",'d',s) # edd / eth
		# -e-
		s=re.sub(u'\xA4',"E",s)
		s=re.sub("&#202;",'E',s) # E circ
		s=re.sub("&#201;|&Eacute;",'E',s) # E acute
		s=re.sub("&#232;",'e',s) # 
		s=re.sub("&#233;|&eacute;",'e',s) # e acute
		s=re.sub("&#234;",'e',s) # e circ
		s=re.sub("&#235;",'e',s) # e diaresis
		s=re.sub("&egrave;",'e',s) # e
		# -i-
		s=re.sub("&#237;",'i',s) # í
		s=re.sub("&#238;",'i',s) # i circumflex
		s=re.sub(u"\xee",'i',s) # icirc
		s=re.sub("&#253;",'y',s) # y acute
		s=re.sub("&#222;",'Th',s) # thorn upper
		s=re.sub("&#205;",'I',s) # upper I acute
		s=re.sub("&#8211;",'-',s) # long dash
		s=re.sub("&#8221;",'"',s) # rquo
		s=re.sub("&iuml;",'i',s)
		# -n-
		s=re.sub("&#241;",'n',s) # ntilde
		s=re.sub(u'\xf1','n',s)
		# -o-
		s=re.sub("&#211;",'O',s) # Ó
		s=re.sub("&#332;",'O',s) # O macron
		s=re.sub(u'\u014c','O',s) # O macron
		s=re.sub(u'\u014D','o',s)
		s=re.sub("&#214;",'o',s) # ö
		s=re.sub("&#243;",'o',s) # ó
		s=re.sub("&#248;",'o',s) # o slash
		s=re.sub("&#242;|\xf2",'o',s) # o grave
		s=re.sub(u'\u014d','o',s) # o grave
		s=re.sub("&#216;",'Oe',s) # Ø
		s=re.sub("&#140;",'oe',s) # oe ligature
		s=re.sub("&#248;",'oe',s) # ø
		s=re.sub("&#246;",'o',s)	# ö
		s=re.sub("&#333;",'o',s) # o grave
		s=re.sub("&#244;",'o',s) # o circ
		# -s-
		s=re.sub("&#154;",'s',s) # s with caron
		s=re.sub("&#138;",'S',s) # S with caron
		s=re.sub("&#254;",'th',s) # thorn lower
		s=re.sub("\s&#191;",'.',s)
		s=re.sub("&#191;",'.',s) # upside down question mark
		# -u-
		s=re.sub(u'\u00FC','u',s)
		s=re.sub("&#249;",'u',s) # ugrave
		s=re.sub("&#251;",'u',s) # ucirc
		s=re.sub("&#252;",'u',s) # ü
		s=re.sub("&#363;",'u',s) # u bar
		s=re.sub("&#250;",'u',s) # u acute
		s=re.sub(u'\u016b','u',s) # u macron
		s=re.sub("&uuml;",'u',s)
		# -y-
		s=re.sub('&#255;','y',s) # ydiaresis
		# non-letters
		s=re.sub(u'\u2019',"'",s)
		s=re.sub(u"\u2013",'-',s) # endash
		s=re.sub(u'\ufffd','?',s) # diamond questionmark symbol
		s=re.sub("&#8216;","'",s)
		s=re.sub("&#8217;","'",s)
		s=re.sub('&#039;',"'",s)
		s=re.sub('&quot;',"'",s)
		s=re.sub(u'\u016b',"'",s)
		s=re.sub('’',"'",s)
		s=re.sub('£',"GBP",s)
		return s
		
#	*** Grab description ***
def flatten(l):
    for el in l:
        if isinstance(el, collections.Iterable) and not isinstance(el, basestring):
            for sub in flatten(el):
                yield sub
        else:
            yield el

def getdesc(html):
		soup=BeautifulSoup(html)
		try:
				image=soup.findAll("img")[-1]
		except:
				return ''
		attrib=html.split("If you are going to publish, redistribute this image on the Internet place this link:")[1].split("</td>")[0]
		title=attrib.split("title=&quot;")[1].split("&quot")[0]
		site=attrib.split("href=&quot;")[1].split("&quot")[0]
		try:
				author=re.sub("\n","",urllib.quote(attrib.split("&gt; by ")[1].split("</em")[0], " ,").encode('ascii','ignore'))
		except:
				author="Public Domain Images"
		return '{{information\n| description = {{en|1=<br/>\n:''Image title: '+image['title']+'\n:Image from Public domain images website, '+site+"}}\n| source = "+image['src']+"\n| author = "+author+'\n| date = Not given\n*Transferred by [[User:{{subst:User:Fae/Fae}}|]] on {{subst:today}}\n| permission = This file is in public domain, not copyrighted, no rights reserved, free for any use. You can use this picture for any use including commercial purposes without the prior written permission and without fee or obligation.\n}}\n=={{int:license}}==\n{{PD-author|1='+author+'}}\n[[Category:Images uploaded by {{subst:User:Fae/Fae}}]]\n[[Category:Public-domain-image.com]]'+allcat, re.sub("\s{2,}"," ",image['title'].encode('ascii','ignore'))+'.jpg', image['src']

def uptry(source,filename,desc):
		countErr=0
		r=True
		while r:
				try:
						up(source,filename,desc)
						return
				except:
						countErr+=1
						if countErr>200:
								p=300
						else:
								p=countErr*5
						print Fore.CYAN,'** ERROR Upload failed'
						print ' ** Pause for '+str(p)+' seconds and try again'+Fore.WHITE
						sleep(p)
		return

plist=[]
def numberSearch(v):
		vcount=0
		countErr=0
		loop=True
		while loop:
				try:
						vgen = pagegenerators.SearchPageGenerator(v, namespaces = "6")
						for vPage in vgen:
								plist.append(vPage.title())
								vcount+=1
						loop=False
				except:
						loop=True
						countErr+=1
						print Fore.RED+"Problem running search, sleeping for",countErr,"seconds"
						time.sleep(countErr)
				if countErr>30:
						loop=False
						vcount=-1
		return vcount

def catexists(cat):	#	Does this Commons category exist?
		urlpath="http://commons.wikimedia.org/w/api.php?action=query&prop=info&format=xml&titles=Category:"+urllib.quote(cat)
		url=urltry(urlpath)
		xml=htmltry(url,urlpath)
		if re.search('missing=""',xml):
				return False
		else:
				return True

def createcat(cat,txt,action):
		wikipedia.setAction(action)
		p=wikipedia.Page(site,"Category:"+cat)
		ptxt="Creating category "+cat
		print Fore.GREEN+"-"*len(ptxt)
		print ptxt
		print "-"*len(ptxt),Fore.WHITE
		sleep(30)
		p.put(txt)
		return

def sleepcounter(period):
		for i in range(period):
				stdout.write("\r%d " % (period-i))
				stdout.flush()
				sleep(1)
		stdout.write("\r  ")
		stdout.flush()
		stdout.write("\r")

def ns(s):
		s=re.sub("\s{2,}"," ",s)
		s=asciichars(oddchars(s))
		s=trim(s)
		return re.sub(" ","_",s)

# *********
# Main loop
# *********


baseurl="http://www.xeno-canto.org/api/recordings.php?query=lic:by-sa&page="
page=1
uri=baseurl+str(page)
print "Getting",uri
url=urltry(uri)
html=json.load(url)
print str(html)[0:100]
# error was a key, not sure what happened to it
'''
if html['error']==0:
		print Fore.GREEN,"Loaded without errors",Fore.WHITE
else:
		print Fore.RED,"Error",html['errorMessage'],Fore.WHITE
		'''
results=html
recordings=results['recordings']	#[i for i in html['results']['recordings']]
numRecordings=results['numRecordings']
numPages=results['numPages']
print Fore.YELLOW,"numRecordings",numRecordings,"\n numPages",numPages,Fore.WHITE
for p in range(int(float(numPages))):
		if p==0: continue
		uri=baseurl+str(p+1)
		print "Getting",uri
		url=urltry(uri)
		html2=json.load(url)
		#print hArr
		'''if html2['error']==0:
				print Fore.GREEN,"Loaded without errors",Fore.WHITE
		else:
				print Fore.RED,"Error",html2['errorMessage'],Fore.WHITE'''
		#for i in html2['results']['recordings']:
		recordings=html2['recordings']#.append(i)
		print Fore.CYAN+"Number of recordings identified:",len(recordings),"of",numRecordings

count=0
results=[]
for r in recordings:
		count+=1
		#pprint.PrettyPrinter(indent=2).pprint(r)
		# Quick check of uniqueness of id on Commons, for virin read filename
		plist=[]
		ref="XC"+r['id']
		title=r['en']
		numbermatch='"xeno-canto"+"'+r['gen']+'"+"'+r['sp']+'"+"'+ref+'"'
		vc=numberSearch(numbermatch)
		print Fore.YELLOW+str(count), Fore.CYAN+"http://commons.wikimedia.org/w/index.php?search="+urllib.quote(numbermatch), Fore.WHITE
		if vc==-1:
				print Fore.YELLOW+"Error generating search matches for '"+title+" "+ref+"', probably timeout error, skipping file without completing this test",Fore.WHITE
				continue
		if vc>0:	# May be a need to ignore known false positives
				#print Fore.RED+"-"*75
				print Fore.RED+"Image appears to be in use already for",asciichars(oddchars(title))+" "+ref+" ("+str(vc)+" matches)."+Fore.WHITE
				#print Fore.RED+"-"*75,Fore.WHITE
				continue
		else:
				results.append(r)

workingdir="F:/XC/"
count=0
uploadcount=0
for r in results:
		count+=1
		ref=re.sub("\D*","",r['id'])
		species=r['sp']
		genus=r['gen']
		common=r['en']
		title=genus+" "+species+" - "+common+" XC"+ref
		filename=asciichars(oddchars(title))+".ogg"	# upload filename
		# Quick check of filename in use - these should be unique
		if nameused(filename):
				print Fore.RED+'Filename found',Fore.YELLOW+"http://commons.wikimedia.org/wiki/File:"+re.sub("%20","_",urllib.quote(filename)),Fore.WHITE
				continue
		localfile=workingdir+ref+".mp3"	# source mp3 file
		localenc=workingdir+ref
		print Fore.GREEN+filename+Fore.WHITE
		source=r['file']
		artist=r['rec']
		gallery=r['url']
		url=urltry(gallery)
		html=htmltry(url,gallery)
		soup=BeautifulSoup(html)
		rd=str(soup.find('section',{'id':'recording-data'}).find('tbody'))
		date=rd.split(">Date<")[1].split('<td>')[1].split('<')[0]
		dtime=""
		if re.search(">Time<",rd):
				dtime=rd.split(">Time<")[1].split('<td>')[1].split('<')[0]
				if len(dtime)>2:
						date+=" "+dtime
		elevation=''
		if re.search('>Elevation<',rd):
				elevation=rd.split(">Elevation<")[1].split('<td>')[1].split('<')[0]
		background=''
		if re.search('>Background<',rd):
				background=rd.split(">Background")[1].split('<td')[1].split('>')[1].split('<')[0]
				if background=="none":
						background=''
		remarks=''
		if re.search('<h2>Remarks from',html):
				remarks=html.split('<h2>Remarks')[1].split('h2>')[1]
				if re.search('<.section',remarks):
						remarks=remarks.split('</section')[0]
				remarks=re.sub("<.?p>","\n",remarks)
				remarks=re.sub("<.?span[^>]*?>","\n",remarks)
				remarks=re.sub("\n*\s*<$","",remarks)
				remarks=re.sub("\n+","\n:",re.sub("\s*\n\s*","\n",remarks))
				remarks=re.sub("<a [^>]*>","",re.sub("<\/a>","",remarks))
		d="=={{int:filedesc}}==\n{{information"
		d+="\n|description={{en|"
		if remarks!='':
				d+=remarks
		if len(r['en'])>2:
				d+="\n:'''Common name:''' "+r['en']
		if len(r['type'])>2:
				d+="\n:'''Type:''' "+r['type']
		if len(r['gen'])>2:
				d+="\n:'''Genus:''' "+r['gen']
		if len(r['sp'])>2:
				d+="\n:'''Species:''' "+r['sp']
		if len(r['loc'])>2:
				d+="\n:'''Location:''' "+r['loc']
		if len(r['cnt'])>2:
				d+="\n:'''Country:''' "+r['cnt']
		if elevation!='':
				d+="\n:'''Elevation:''' "+elevation
		if background!='':
				d+="\n:Background:''' "+background
		d+="}}"
		d+="\n|date="+date
		d+="\n|author="+artist
		d+="\n|source=\n*'''Metadata:''' "+gallery+"\n*'''Audio file:''' "+source
		d+="\n}}"
		if len(r['lat'])>2:
				d+="{{object location dec|"+r['lat']+"|"+r['lng']+"}}"
		d+="{{User:{{subst:User:Fae/Fae}}/Projects/Xeno-canto/credit}}"
		d+="\n\n=={{int:license-header}}==\n{{cc-by-sa-3.0}}"
		d+="\n[[Category:Xeno-canto]]\n[[Category:Sound files uploaded by {{subst:User:Fae/Fae}}]]"
		cat=r['gen']+" "+r['sp']
		if catexists(cat):
				d+="\n[[Category:"+cat+"]]"
		d=re.sub("ocolono",":",oddchars(re.sub(":","ocolono",d)))
		print Fore.CYAN+d,Fore.WHITE
		urllib.urlretrieve(source, localfile)
		print Fore.YELLOW+str(count)+"/"+str(len(results)),Fore.GREEN,"Encoding",localfile
		print "ffmpeg -i",localfile,localenc+".wav",Fore.WHITE
		subprocess.call(["ffmpeg","-i",localfile,localenc+".wav"])
		subprocess.call(["oggenc2",localenc+".wav",
				"-q 10",	#quality
				"-a "+ns(artist),	#artist
				"-l "+ns(gallery),	#album
				"-t "+ns(title),	#title
				#"-d "+re.sub("\D*","",date.split(" ")[0]),	#date
				"-N "+ref,	#track num
				"-G "+ns(r['type']),	#genre
				"-c country="+ns(r['cnt']),
				"-c location="+ns(r['loc']),
				"-c genus="+ns(r['gen']),
				"-c species="+ns(r['sp']),
				"-c latitude="+ns(r['lat']),
				"-c longitude="+ns(r['lng']),
				"-c license="+ns(r['lic']),
				"-c URL="+ns(r['url']),
				"-c date="+date.split(" ")[0],
				"-c time="+dtime,
				"-o",localenc+".ogg"])
		remove(localenc+".wav")
		remove(localenc+".mp3")
		# Check if image is a duplicate on Commons
		media=localenc+".ogg"
		try:
				duplicate,duptitle = dupcheck(media)
		except:
				print Fore.RED+"Problem when running the duplicate check for",media,Fore.WHITE
				time.sleep(10)
				try:
						duplicate,duptitle = dupcheck(media)
				except:
						print Fore.RED+"Failed on second try, giving up and skipping"
						remove(media)
						continue
		if duplicate:
				print Fore.RED+'File is already on Commons as',duptitle,Fore.WHITE
				time.sleep(2)
				continue
		# Upload
		uptry(media,filename,d)	# Intermittently getting [Errno 54] Connection reset by peer
		remove(media)
		uploadcount+=1
		print Fore.GREEN+"Total uploads =",uploadcount,Fore.WHITE
		sleepcounter(10)
