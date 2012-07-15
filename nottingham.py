# -*- coding: utf-8 -*- 

import irclib, mwclient, lxml, pywapi
import sys, os, signal, mimetypes, types, random
import urllib, urllib2
import string
from bs4 import BeautifulSoup
import sqlite3 as sql
from datetime import date
from mechanize import Browser

# For debugging and learning. Comment out if not needed
irclib.DEBUG = True

# Connection information
network = 'irc.cc.tut.fi'
port = 6667
channel = '#nottingham'
nick = 'RobinHoodi'
name = 'New Sheriff of Nottingham'

# The owner and the admins
owner = 'Hamatti'
admins = ['vianah', 'alpeha', 'jumasan', 'jmaoja', 'jopemi', 'pesape', 'aatkin', 'anttlai']

# Create an IRC object from irclib
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

# Handle channel joins
def handleJoin(connection, event): 
  name = event.source().split('!')[0]
  user = event.source().split('!')[1].split('@')[0] 
  print name + ' has joined ' + event.target()
  if user in admins:
    server.mode(channel, '+o ' + name)

#Handle public messages
def handlePubMsg(connection, event):
  user = event.source().split('!')[1].split('@')[0]
  name = event.source().split('!')[0]
  message = event.arguments()[0]
  source = event.target()
  try:
    if 'http://' in message.lower():
      message = 'http:' + message.split('http:')[1]
      message = message.split(' ')[0] 
      new_title = fetchTitle(message)
    #map_to_database(new_title, message, user)
      server.privmsg(channel, new_title)
    elif 'https://' in message.lower():
      message = 'https:' + message.split('https:')[1]
      message = message.split(' ')[0] 
      new_title = fetchTitle(message)
    #map_to_database(new_title, message, user)
      server.privmsg(channel, new_title)
    elif '!poem' in message.lower():
      server.privmsg(channel, fetchPoemLines())
    elif message.lower().startswith("!what"):
      query = message.split(' ')[1:]
      query = " ".join(query)
      server.privmsg(channel, readWikipedia(query).encode('utf-8'))
    elif message.lower().startswith("!food"):
      if len(message.split(' ')) < 2:
        server.privmsg(channel, "Usage: !food [restaurant] . Restaurants at the moment are: ict, tottisalmi, assari, mikro, delica")
      else:
        restaurant = message.split(' ')[1]
        server.privmsg(channel, fetchFood(restaurant).encode('utf-8'))
    elif message.lower().startswith("!weather"):
      if len(message.split(' ')) < 2:
        server.privmsg(channel, "Usage: !weather [city]. Only Finnish cities.")
      else:
        city = message.split(' ')[1]
        server.privmsg(channel, weather(city))
                      
  except:
    server.privmsg(channel, "Error at level 3")

def map_to_database(title, url, user):
  conn = sql.connect('urls.db')
  c = conn.cursor()
  day = date.today()
  t = (title, url, user, day)
  c.execute("INSERT INTO urls VALUES ?, ?, ?, ?", t)
  conn.commit()
  c.close()

def handleCommands(event, message):
  message = message[1:len(message)]
  channel = event.target()
  command = message.split(' ')[0]
  
  # op or deop
  if command == 'op' or command == 'deop':
    param1 = message.split(' ')[1]	  
    if len(message.split(' ')) < 2:
      server.privmsg(channel, 'Not enough parameters')
    else:
      if command == 'op':
        server.mode(channel, '+o ' + param1)
      else:
	if param1 != 'Hamatti' and param1 != nick:
          server.mode(channel, '-o ' + param1)
	else:
	  server.privmsg(channel, 'You cannot deop bot or Hamatti')
  
  
def handlePrivMsg(connection, event):
  name = event.source().split('!')[0] 
  message = event.arguments()[0]
  if name == owner and message == 'quit':
    quit()
  if name == owner and message == 'boot':
    restart()

def handleNewNick(connection, event):
  nick = server.get_nickname() + '_'

def quit():
  server.disconnect('I love you, but I got to go <3')
  sys.exit()

def restart():
  python = sys.executable
  os.execl(python, python, *sys.argv)   

# Fetch titles from url
def fetchTitle(url):
  br = Browser()
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
      res = br.open(url)
      data = res.get_data()
      soup = BeautifulSoup(data)
    
      raw_title = soup.find("title")
      title = raw_title.renderContents().replace('\n','')
      title = " ".join(title.split())
      signal.alarm(0)

    return title

  except:
    title = "Not found."
    signal.alarm(0)
    return title

def fetchPoemLines():
    randPoem = random.randint(0,len(poems)-1)
    poem = poems[randPoem]
    rand = random.randint(0,len(poem)-3)
    poemstring = "%s %s %s" % (poem[rand], poem[rand+1], poem[rand+2])
    if poemstring.endswith(","):
      poemstring = poemstring[:-1]
    return poemstring

def readPoems():
  global poems
  poems = []
  for filename in open('poems.txt'):
    poemlines = []
    for line in open(filename.strip()):
      poemlines.append(line.strip())
    poems.append(poemlines)

def readWikipedia(query):
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
            paragraph = soup.find('div',id="bodyContent").p.get_text().replace('\n', '')
            return  "%s @ %s" % (paragraph, url)

        else:
            return "Page not found."

    except:
        return "Error at level 4: %s" % sys.exc_info()[0]

def fetchFood(restaurant):
  
  restaurants = {'assari': 'restaurant_aghtdXJraW5hdHIaCxISX1Jlc3RhdXJhbnRNb2RlbFYzGMG4Agw', 'delica': 'restaurant_aghtdXJraW5hdHIaCxISX1Jlc3RhdXJhbnRNb2RlbFYzGPnPAgw', 'ict': 'restaurant_aghtdXJraW5hdHIaCxISX1Jlc3RhdXJhbnRNb2RlbFYzGPnMAww', 'mikro': 'restaurant_aghtdXJraW5hdHIaCxISX1Jlc3RhdXJhbnRNb2RlbFYzGOqBAgw', 'tottisalmi': 'restaurant_aghtdXJraW5hdHIaCxISX1Jlc3RhdXJhbnRNb2RlbFYzGMK7AQw'}
  if restaurants.has_key(restaurant.lower()):
    opener = urllib2.build_opener()    
    resource = opener.open("http://murkinat.appspot.com")
    data = resource.read()
    resource.close()
    soup = BeautifulSoup(data, "lxml")
    meal_div = soup.find(id="%s"%restaurants[restaurant.lower()])        
    meal_div = meal_div.find_all("td", "mealName hyphenate")
    mealstring = "%s: " % restaurant
    for meal in meal_div:
      mealstring += "%s / " % meal.string.strip()
    mealstring = "%s @ %s" % (mealstring[:-3], "http://murkinat.appspot.com")
    return mealstring

  else:
    return "Tuntematon ravintola"

def weather(city):
  try:
    weather = pywapi.get_weather_from_google("%s finland" % city)
    return "%s: %s and %s C now" % (city, string.lower(weather['current_conditions']['condition']), weather['current_conditions']['temp_c'])
  except:
    return "Unknown city"


# Register handlers
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

# Create server object, connect and join
server.connect(network, port, nick, ircname = name)
server.join(channel)



# Infinite loop
readPoems()
irc.process_forever()
