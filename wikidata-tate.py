#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Bot to import paintings from the Nationalmuseum (Sweden) to Wikidata.
Based on https://git.wikimedia.org/blob/labs%2Ftools%2Fmultichill.git/e6a873ea1d397e22965b2a69d08a2cd7b410d562/bot%2Fwikidata%2Frijksmuseum_import.py
    by Multichill

"""
import json, os
import pywikibot
from pywikibot import pagegenerators
import urllib
import re
import pywikibot.data.wikidataquery as wdquery
import datetime
from pywikibot import config
from colorama import Fore, Back, Style
from colorama import init
init()

class PaintingsBot:
    """
    A bot to enrich and create monuments on Wikidata
    """
    def __init__(self, paintingArray, paintingIdProperty):
        """
        Arguments:
            * chosen array of json records

        """
        self.generator = paintingArray
        self.repo = pywikibot.Site().data_repository()

        self.paintingIdProperty = paintingIdProperty
        self.paintingIds = self.fillCache(self.paintingIdProperty)

    def fillCache(self, propertyId, queryoverride=u'', cacheMaxAge=0):
        '''
        Query Wikidata to fill the cache of paintings we already have an object for
        https://tools.wmflabs.org/autolist/autolist1.html?q=CLAIM[195%3A430682]%20AND%20NOCLAIM[217]
        '''
        result = {}
        if queryoverride:
            query = queryoverride
        else:
            query = u'CLAIM[195:430682] AND CLAIM[%s]' % (propertyId,)  # collection
        wd_queryset = wdquery.QuerySet(query)

        wd_query = wdquery.WikidataQuery(cacheMaxAge=cacheMaxAge)
        data = wd_query.query(wd_queryset, props=[str(propertyId),])

        if data.get('status').get('error')=='OK':
            expectedItems = data.get('status').get('items')
            props = data.get('props').get(str(propertyId))
            for prop in props:
                # FIXME: This will overwrite id's that are used more than once.
                # Use with care and clean up your dataset first
                result[prop[2]] = prop[0]

            if expectedItems==len(result):
                pywikibot.output('I now have %s items in cache' % expectedItems)

        return result

    def run(self):
        """
        Starts the robot.
        """
        nationalmuseum = pywikibot.ItemPage(self.repo, u'Q430682') #Q430682 is the Tate gallery
        for painting in self.generator:
            # Buh, for this one I know for sure it's in there

            # paintingId = painting['object']['proxies'][0]['about'].replace(u'/proxy/provider/90402/', u'').replace(u'_', u'-')
            paintingId = painting['acno']
            #paintingId = ids[0].replace('Inv. Nr.:','').strip('( )')
            #objId = ids[1]
            uri = painting['url'] #u'http://emp-web-22.zetcom.ch/eMuseumPlus?service=ExternalInterface&module=collection&objectId=%s&viewType=detailView' % objId
            #europeanaUrl = u'http://europeana.eu/portal/record/%s.html' % (painting['object']['about'],)
            
            #dcYear=painting['

            print Fore.GREEN+paintingId,Fore.WHITE
            print Fore.CYAN+uri,Fore.WHITE

            try:
                dcCreatorName = painting['all_artists']
                print dcCreatorName
            except KeyError:
                print 'skipped'
                continue



            paintingItem = None
            newclaims = []
            if paintingId in self.paintingIds:
                paintingItemTitle = u'Q%s' % (self.paintingIds.get(paintingId),)
                print paintingItemTitle
                paintingItem = pywikibot.ItemPage(self.repo, title=paintingItemTitle)

            else:
                # creating a new one
                data = {'labels': {},
                        'descriptions': {},
                        }
                
                dcTitleLang='en'
                dcTitle=painting['title']
                data['labels'][dcTitleLang] = {'language': dcTitleLang,
                                            'value': dcTitle}


                if dcCreatorName:
                    if False:#dcCreatorName == u'Okänd':
                        '''data['descriptions']['en'] = {'language': u'en', 'value' : u'painting by unknown painter'}
                        data['descriptions']['nl'] = {'language': u'nl', 'value' : u'schilderij van onbekende schilder'}
                        data['descriptions']['sv'] = {'language': u'sv', 'value' : u'målning av okänd konstnär'}'''
                    else:
                        data['descriptions']['en'] = {'language': u'en', 'value' : u'painting by %s' % (dcCreatorName,)}
                        data['descriptions']['nl'] = {'language': u'nl', 'value' : u'schilderij van %s' % (dcCreatorName,)}
                        data['descriptions']['sv'] = {'language': u'sv', 'value' : u'målning av %s' % (dcCreatorName,)}


                # print data
                # create new empty item and request Q-number
                identification = {}
                summary = u'Creating new item with data from %s ' % (uri,)
                pywikibot.output(summary)
                #monumentItem.editEntity(data, summary=summary)
                try:
                		result = self.repo.editEntity(identification, data, summary=summary)
                		#print result
                		paintingItemTitle = result.get(u'entity').get('id')
                		paintingItem = pywikibot.ItemPage(self.repo, title=paintingItemTitle)
										# add identifier
                		newclaim = pywikibot.Claim(self.repo, u'P%s' % (self.paintingIdProperty,))
                		newclaim.setTarget(paintingId)
                		pywikibot.output('Adding new id claim to %s' % paintingItem)
                		paintingItem.addClaim(newclaim)
                		self.addReference(paintingItem, newclaim, uri)
                		
                		newqualifier = pywikibot.Claim(self.repo, u'P195') #Add collection, isQualifier=True
                		newqualifier.setTarget(nationalmuseum)
                		pywikibot.output('Adding new qualifier claim to %s' % paintingItem)
                		newclaim.addQualifier(newqualifier)
                		
                		# add collection
                		newclaim = pywikibot.Claim(self.repo, u'P195')
                		newclaim.setTarget(nationalmuseum)
                		pywikibot.output('Adding collection claim to %s' % paintingItem)
                		paintingItem.addClaim(newclaim)
                		self.addReference(paintingItem, newclaim, uri)
                		# end of new item creation
                except Exception, e:
                		try:
                				print Fore.RED+str(e).encode('latin-1','ignore'),Fore.WHITE
                		except:
                				pass


            if paintingItem and paintingItem.exists():

                data = paintingItem.get()
                claims = data.get('claims')
                #print claims

                # located in
                if u'P276' not in claims:
                    newclaim = pywikibot.Claim(self.repo, u'P276')
                    newclaim.setTarget(nationalmuseum)
                    pywikibot.output('Adding located in claim to %s' % paintingItem)
                    paintingItem.addClaim(newclaim)
                    self.addReference(paintingItem, newclaim, uri)


                # instance of always painting while working on the painting collection
                if u'P31' not in claims:
                    dcformatItem = pywikibot.ItemPage(self.repo, title='Q3305213')  # painting

                    newclaim = pywikibot.Claim(self.repo, u'P31')
                    newclaim.setTarget(dcformatItem)
                    pywikibot.output('Adding instance claim to %s' % paintingItem)
                    paintingItem.addClaim(newclaim)
                    self.addReference(paintingItem, newclaim, uri)

                # Europeana ID
                '''if u'P727' not in claims:
                		
                    europeanaID = painting['object']['about'].lstrip('/')

                    newclaim = pywikibot.Claim(self.repo, u'P727')
                    newclaim.setTarget(europeanaID)
                    pywikibot.output('Adding Europeana ID claim to %s' % paintingItem)
                    paintingItem.addClaim(newclaim)
                    self.addReference(paintingItem, newclaim, europeanaUrl)'''

    def addReference(self, paintingItem, newclaim, uri):
        """
        Add a reference with a retrieval url and todays date
        """
        pywikibot.output('Adding new reference claim to %s' % paintingItem)
        refurl = pywikibot.Claim(self.repo, u'P854') #Add url, isReference=True
        refurl.setTarget(uri)
        refdate = pywikibot.Claim(self.repo, u'P813')
        today = datetime.datetime.today()
        date = pywikibot.WbTime(year=today.year, month=today.month, day=today.day)
        refdate.setTarget(date)
        newclaim.addSources([refurl, refdate])


def main(directoryReq):
		sourceDir = '/' + os.path.join('Users','Fae', 'git', 'collection','artworks')	
		print "Reading directory:", sourceDir
		from os import walk
		currentFiles = []
		mypath = sourceDir
		count = 0
		oldcount = 0
		for (dirpath, dirnames, filenames) in walk(mypath):
				if not (re.search(directoryReq, dirpath.split('\\')[-1]) or re.search(directoryReq, dirpath.split('\\')[-2]) ): continue
				print Fore.CYAN,dirpath,Fore.YELLOW
				filenames = [f for f in filenames if re.match('json', f[-4:])]
				if len(filenames)>0:
						currentFiles.extend([[filenames, dirpath]])
						count+=len(filenames)
				if len(currentFiles) % 10 == 1:
						print currentFiles[-1][1].split('/')[-1], Fore.WHITE, count

		count=0
		toUpload=[]
		for d in currentFiles:
				directory=d[1]
				for f in d[0]:
						count+=1
						ddfile=file(os.path.join(directory,f))
						data = json.load(ddfile)
						if data['medium'] is None: continue
						if not re.search('[Oo]il|[Ww]atercolour', data['medium']): continue
						if re.search(r'known', data['title']): continue
						record={'artist':data['all_artists'],
										'date':data['dateText'],
										'medium':data['medium'],
										'title':data['title'],
										'acno':data['acno'],
										'url':data['url']}
						for i in ['acno', 'artist','date','title','url']:
								print i,Fore.YELLOW, record[i].encode('latin-1','replace'), Fore.WHITE
						toUpload.append(data)
		paintingsBot = PaintingsBot(toUpload, 217)  # inv nr.
		paintingsBot.run()


if __name__ == "__main__":
    usage = u'Usage:\tpython nationalmuseumSE.py rows start\n' \
            u'where rows and start are optional integers'
    import sys
    from sys import argv
    if len(argv) == 1:
        main()
    elif len(argv) == 2:
    		main(re.compile(argv[1]))
    else:
        print usage
