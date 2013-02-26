# -*- coding: utf-8 -*- 

# irclib-kirjasto tuo perustoiminnallisuudet irc-verkkoon liittymiseksi
import irclib
# mwclient Wikipedian parsimiseen, lxml BeautifulSoupin parsimisfunktioksi
import mwclient, lxml
# Järjestelmään liittyvät kirjastot
import sys, os, signal
# mimetypes sivustojen metadatan tulkitsemiseen (kuva, dokumentti, html-sivu), types-kirjasto NoneType-tarkistusta varten
import mimetypes, types
# random satunnaislukujen luomiseen
import random
# urllib-kirjastot verkkosivujen avaamiseen
import urllib, urllib2
# BeautifulSoup4-kirjasto web-sivujen DOMin parsimiseen
from bs4 import BeautifulSoup
# konfiguraatiotiedostojen lukemiseen
import ConfigParser
# Tietokannan käyttöä varten
import sqlite3 as sql
import datetime

from HTMLParser import HTMLParser

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

## Luetaan konfiguraatiotiedosto
config = ConfigParser.RawConfigParser()
config.read('config.conf')

irclib.DEBUG = config.getboolean('Network', 'DEBUG')
network = config.get('Network', 'network')
port = config.getint('Network', 'port')
channels = config.get('Network', 'channels').split(',')

nick = config.get('Bot', 'nick')
name = config.get('Bot', 'name')

admins = config.get('Users', 'admins').split(',')
todoadmin = config.get('Users', 'todo').split(',')

# Luodaan irc-objekti ja serverimuuttuja irclib-kirjastosta
irc = irclib.IRC()
server = irc.server()

# Generic echo handler (space added)
def handleEcho(connection, event):
  print 
  print ' '.join( event.arguments() )

# Generic echo handler (no space added)
def handleNoSpace(connection, event):
  print ' '.join(event.arguments())

# Handle private notices
def handlePrivNotice(connection, event):

  if event.source():
    print ':: ' + event.source() + ' ->' + event.arguments()[0]
  else:
    print event.arguments()[0]

# Käsittelee kanavalle liittyvät - tällä hetkellä opit saavat kaikki admins-listassa olevat kanavasta riippumatta
def handleJoin(connection, event): 
  name = event.source().split('!')[0]
  user = event.source().split('!')[1].split('@')[0] 
  print name + ' has joined ' + event.target()
  if user in admins:
    server.mode(event.target(), '+o ' + name)
  
# Perustoiminnallisuus kanavalle tulevien viestien (ja komentojen) käsittelyyn
def handlePubMsg(connection, event):
  user = event.source().split('!')[1].split('@')[0]
  name = event.source().split('!')[0]
  # Viesti, joka tulee kanavalle
  message = event.arguments()[0]
  source = event.target()
  try:
    # linkkien käsittely
    if 'http://' in message.lower():
      message = 'http:' + message.split('http:')[1]
      message = message.split(' ')[0] 
      if message.endswith(')'):
        message = message[:-1]
      new_title = fetchTitle(message)
      server.privmsg(event.target(), new_title)

    elif 'https://' in message.lower():
      message = 'https:' + message.split('https:')[1]
      message = message.split(' ')[0] 
      if message.endswith(')'):
        message = message[:-1]
      new_title = fetchTitle(message)
      server.privmsg(event.target(), new_title)

    # Botti lukee runoja
    elif '!poem' in message.lower():
      server.privmsg(event.target(), fetchPoemLines())

    # Wikipedia-haut
    elif message.lower().startswith("!what"):
      if len(message.split(' ')) < 2:
        server.privmsg(event.target(), "Usage: !what [query]. English and Finnish Wikipedia.")
      else:
        query = message.split(' ')[1:]
        query = " ".join(query)
        server.privmsg(event.target(), readWikipedia(query).encode('utf-8'))

    # Unican opiskelijaruokaloiden päivän tarjonta
    elif message.lower().startswith("!food"):
      if len(message.split(' ')) < 2:
        server.privmsg(event.target(), "Usage: !food [restaurant] . Restaurants at the moment are: ict, tottisalmi, assari, mikro, delica")
      else:
        restaurant = message.split(' ')[1]
        server.privmsg(event.target(), fetchFood(restaurant).encode('utf-8'))

    # Steam-pelipalvelun tietohaku
    elif message.lower().startswith('!steam'):
      if len(message.split(' ')) < 2:
        server.privmsg(event.target(), 'Usage: !steam [game]. Experimental.')
      else:
        game = message.split(' ')[1:]
        gamedesc, gameurl = steamPrice(game)
        server.privmsg(event.target(), gamedesc.encode('utf-8'))
        server.privmsg(event.target(), gameurl.encode('utf-8'))
    # Päätöstyökalu
    elif message.lower().startswith('!decide'):
      if len(message.split(' ')) < 2:
        server.privmsg(event.target(), 'Usage: !decide [option1] [option2] ... [optionN].')
      else:
        choice = decide(message.split(' '))
        server.privmsg(event.target(), '%s, noppa ratkaisee: %s' % (name, choice))
    # Oikotie NOOOOO-linkkiin
    elif message.lower().startswith('!no'):
      server.privmsg(event.target(), 'http://nooooooooooooooo.com/')
    # TODO-toiminnallisuus
    elif message.lower().startswith('!todo'):
        if user in todoadmin and len(message.split(" ")) > 1:
            con = sql.connect('todo.db')
            cur = con.cursor()
            dt = datetime.datetime.now()
            date = "%s-%s-%s %s:%s:%s" % (dt.year, dt.month, dt.day, int(dt.hour)+1, dt.minute, dt.second)
            cur.execute("INSERT INTO todo (thing, date, priority) VALUES(?, ?, 4)",(" ".join(message.split(" ")[1:]).encode('utf-8'),date ))
            con.commit()
            cur.execute("SELECT oid FROM todo WHERE oid = (select max(oid) from todo)")
            new_oid = cur.fetchone()[0]
            server.privmsg(event.target(), "todo #%s logged" % new_oid)
        else:
            server.privmsg(event.target(), "TODO-lista: http://hamatti.org/todo/")
    elif message.lower().startswith('!prio') and user in todoadmin:
        priors = message.split(" ")
        if len(priors) < 2:
            server.privmsg(event.target(), "Usage: !prior [new_priority] [oid](optional) - admins only")
        else:
            con = sql.connect('todo.db')
            cur = con.cursor()
            oid = 0
            if len(priors) == 2:
                cur.execute("select oid from todo where oid = (select max(oid) from todo)")
                oid = cur.fetchone()[0]
            elif len(priors) == 3:
                oid = priors[2]
            cur.execute("UPDATE todo SET priority = ? WHERE oid = ?", (priors[1], oid))
            con.commit()
    elif message.lower().startswith('!help'):
        helps = ['!steam', '!what', '!decide', '!food', '!todo (admin only)', '!prio (admin only)', '!poem']
        helpstring = ", ".join(sorted(helps))
        server.privmsg(event.target(), helpstring)
    elif message.lower().startswith('!badumtsh'):
        server.privmsg(event.target(), "http://instantrimshot.com/")

  except:
    server.privmsg(event.target(), "Error at level 3")

# Käsitteli yksityisviestit - ei toiminnallisuuksia tällä hetkellä
def handlePrivMsg(connection, event):
  pass

# Nickin vaihtaminen
def handleNewNick(connection, event):
  nick = server.get_nickname() + '_'

## Varsinaiset lisätoiminnallisuudet ##

# Hakee annetulle urlille otsikon (<title>-tagin sisällön) tai kertoo mitä tyyppiä se on
def fetchTitle(url):
  """
  Returns <title> of page in given url
  If url contains images, documents or applications ('image' or 'application' content-type) prints corresponding text
  """
  global title
  def timeout_handler(signum, frame):
    pass
  
  old_handler = signal.signal(signal.SIGALRM, timeout_handler)
  signal.alarm(6)

  try:

    mime = mimetypes.guess_type(url)
    if type(mime[0]) == types.NoneType:
      mimetype = "None"
      fileExt = "None"
    else:
      mimetype, fileExt = mime[0].split("/")

    if mimetype.lower() == 'image':
      title = "Image."
      signal.alarm(0)
    elif mimetype.lower() == 'application':
      title = "App. Doc. Something."
      signal.alarm(0)
    else:
      # Avataan url
      opener = urllib2.build_opener()
      opener.addheaders = [('User-agent', 'Mozilla/5.0')] 
      resource = opener.open(url)
      data = resource.read()
      resource.close()
      # Luetaan data BeutifulSoup-olioon
      soup = BeautifulSoup(data)
      # Haetaan sivun <title>-tagin sisältö
      raw_title = soup.find("title")
      # Poistetaan mahdolliset rivinvaihdot
      title = raw_title.renderContents().replace('\n','')
      title = " ".join(title.split())
      signal.alarm(0)

    return title

  except:
    title = "Not found."
    signal.alarm(0)
    return title

def fetchTitleBITLY(url):
    import bitly_api
    
    apikey = "ef1e5e332dff2e7649d4c7f4902040db7d51c387"
    
    c = bitly_api.Connection(login="hamatti", access_token=apikey)
    shorturl = c.shorten(url)
    try:
        ml = MLStripper()
        ml.feed(c.link_content(shorturl['url']))
        return ml.get_data().encode('utf-8')
    except:
        return "No title"
    
# Hakee satunnaisesta runosta satunnaisen kohdan ja palauttaa 3 riviä pilkuilla erotettuna
def fetchPoemLines():
  """
  Reads random poem from global poems variable and then returns 3 lines from that poem
  """
  randPoem = random.randint(0,len(poems)-1)
  poem = poems[randPoem]
  rand = random.randint(0,len(poem)-3)
  poemstring = "%s %s %s" % (poem[rand], poem[rand+1], poem[rand+2])
  if poemstring.endswith(","):
    poemstring = poemstring[:-1]
  return poemstring

# Lukee poems.txt-tiedostossa olevien tiedostonimien vastaavat tiedostot globaaliin poems-muuttujaan
def readPoems():
  """
  Read poems present in poems.txt
  """
  global poems
  poems = []
  for filename in open('poems.txt'):
    poemlines = []
    for line in open(filename.strip()):
      poemlines.append(line.strip())
    poems.append(poemlines)

# Wikipedia-haku
def readWikipedia(query):
  """
  Based on query, tries to find corresponding article from english or finnish wikipedia and then returns first paragraph and url to article.
  Works fine on most articles but sometimes not since only takes account the first <p>-tag in page
  """
  try:
    
    site = mwclient.Site("en.wikipedia.org")
    page = site.Pages[query]
    if page.exists:
      article = urllib.quote(query)
      opener = urllib2.build_opener()
      opener.addheaders = [('User-agent', 'Mozilla/5.0')] #wikipedia needs this                                                                                                                          
      
      resource = opener.open("http://en.wikipedia.org/wiki/" + article)
      url = "http://en.wikipedia.org/wiki/%s" % article
      data = resource.read()
      resource.close()
      soup = BeautifulSoup(data)
      paragraph = soup.find('div',id="mw-content-text").p.get_text()
    
      return  "%s @ %s" % (paragraph[:300], url)
    else:
      site = mwclient.Site("fi.wikipedia.org")
      page = site.Pages[query]
      if page.exists:
        article = urllib.quote(query)
        opener = urllib2.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')] #wikipedia needs this                                                                                                                      
        
        resource = opener.open("http://fi.wikipedia.org/wiki/" + article)
        url = "http://fi.wikipedia.org/wiki/%s" % article
        data = resource.read()
        resource.close()
        soup = BeautifulSoup(data)
        paragraph = soup.find('div',id="mw-content-text").p.get_text()
        return  "%s @ %s" % (paragraph[:300], url)
            
      else:
        return "Page not found."

  except:
    return "Error at level 4 (Wikipedia)"

def fetchFood(restaurant):
  """
  Shows menu for student restaurants in Turku
  """
  # Murkinat.appspot.comin käyttämät ravintolakohtaiset id-tunnukset
  restaurants = {'assari': 'restaurant_ag5zfm11cmtpbmF0LWhyZHIaCxISX1Jlc3RhdXJhbnRNb2RlbFYzGMG4Agw', 'delica': 'restaurant_ag5zfm11cmtpbmF0LWhyZHIaCxISX1Jlc3RhdXJhbnRNb2RlbFYzGPnPAgw', 'ict': 'restaurant_ag5zfm11cmtpbmF0LWhyZHIaCxISX1Jlc3RhdXJhbnRNb2RlbFYzGPnMAww', 'mikro': 'restaurant_ag5zfm11cmtpbmF0LWhyZHIaCxISX1Jlc3RhdXJhbnRNb2RlbFYzGOqBAgw', 'tottisalmi': 'restaurant_ag5zfm11cmtpbmF0LWhyZHIaCxISX1Jlc3RhdXJhbnRNb2RlbFYzGMK7AQw', 'tottis': 'restaurant_ag5zfm11cmtpbmF0LWhyZHIaCxISX1Jlc3RhdXJhbnRNb2RlbFYzGMK7AQw'}

  if restaurants.has_key(restaurant.lower()):
    opener = urllib2.build_opener()    
    resource = opener.open("http://murkinat.appspot.com")
    data = resource.read()
    resource.close()
    soup = BeautifulSoup(data, "lxml")
    meal_div = soup.find(id="%s"%restaurants[restaurant.lower()])        
    meal_trs = meal_div.find_all("tr", "meal")

    meals = {}
    for meal_tr in meal_trs:
      meals[meal_tr.find('td', 'mealName hyphenate').string.strip()] = meal_tr.find('span', 'mealPrice').string.strip()

    mealstring = "%s: " % restaurant
    for meal in meals.keys():
        mealstring += "%s: %s, " % (meal, meals[meal])
    return "%s @ %s" % (mealstring[:-2], "http://murkinat.appspot.com")


  else:
    return "Tuntematon ravintola"

# Hakee Steam-palvelusta pelin käyttäen järjestelmän sisäistä hakukonetta ja palauttaa pelin nimen, kuvauksen sekä hinnan
def steamPrice(game):
  try:
    search_url = 'http://store.steampowered.com/search/?term=%s&category1=998' % game
    search_soup = BeautifulSoup(urllib.urlopen(search_url))
    searched_apps = search_soup.find('a', 'search_result_row')

    if isinstance(searched_apps, types.NoneType):
        return "Game not found", "http://store.steampowered.com"
    else:
        search_url = searched_apps['href']

    soup = BeautifulSoup(urllib.urlopen(search_url))
    game_name = soup.find('div', 'details_block')
    game_name = str(game_name).replace('\n', '').split(':')[1].split('>')[1].split('<')[0].strip()
    desc = soup.find('meta', attrs={'name': 'description'})
    price_div = soup.find('div', 'game_purchase_price price')
    if isinstance(price_div, types.NoneType):
        price_div = soup.find('div', 'discount_final_price')
    price = price_div.string
    gamedesc = "%s: %s Cost: %s" % (game_name, str(desc).split('=')[1].split("\"")[1].decode('utf-8'), price.strip())

    return gamedesc, search_url

  except:
    return "Error, game not found", "http://store.steampowered.com"

# Valitsee annetuista vaihtoehdoista satunnaisesti yhden ja palauttaa sen
def decide(options):
    decision = random.randint(0,len(options)-1)
    if (decision > 0) :
        return options[decision]
    else:
        return decide(options)

def main():
  # Lisätään irc-objektiin käsittelytoiminnot eri tapahtumille
  irc.add_global_handler ( 'privnotice', handlePrivNotice ) #Private notice
  irc.add_global_handler ( 'welcome', handleEcho ) # Welcome message
  irc.add_global_handler ( 'yourhost', handleEcho ) # Host message
  irc.add_global_handler ( 'created', handleEcho ) # Server creation message
  irc.add_global_handler ( 'myinfo', handleEcho ) # "My info" message
  irc.add_global_handler ( 'featurelist', handleEcho ) # Server feature list
  irc.add_global_handler ( 'luserclient', handleEcho ) # User count
  irc.add_global_handler ( 'luserop', handleEcho ) # Operator count
  irc.add_global_handler ( 'luserchannels', handleEcho ) # Channel count
  irc.add_global_handler ( 'luserme', handleEcho ) # Server client count
  irc.add_global_handler ( 'n_local', handleEcho ) # Server client count/maximum
  irc.add_global_handler ( 'n_global', handleEcho ) # Network client count/maximum
  irc.add_global_handler ( 'luserconns', handleEcho ) # Record client count
  irc.add_global_handler ( 'luserunknown', handleEcho ) # Unknown connections
  irc.add_global_handler ( 'motdstart', handleEcho ) # Message of the day ( start )
  irc.add_global_handler ( 'motd', handleNoSpace ) # Message of the day
  irc.add_global_handler ( 'edofmotd', handleEcho ) # Message of the day ( end )
  irc.add_global_handler ( 'join', handleJoin ) # Channel join
  irc.add_global_handler ( 'namreply', handleNoSpace ) # Channel name list
  irc.add_global_handler ( 'endofnames', handleNoSpace ) # Channel name list ( end )
  irc.add_global_handler ( 'pubmsg', handlePubMsg ) # Public messages
  irc.add_global_handler ( 'privmsg', handlePrivMsg ) # Private messages
  irc.add_global_handler ( 'nicknameinuse', handleNewNick ) # Gives new nickname if already used

  # Yhdistää botin haluttuun verkkoon ja porttiin annetuilla konfiguraatioparametreilla
  server.connect(network, port, nick, ircname = name)
  # Liittää botin kanaville
  for channel in channels:
    server.join(channel)

  # Lukee runot muistiin
  readPoems()

  # Käynnistää irclibin ikuisen loopin, jossa botti ottaa vastaan kanavalta tulevan syötteen  
  irc.process_forever()

if __name__ == '__main__':
  main()
