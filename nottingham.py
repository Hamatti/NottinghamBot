import irclib
import sys, os, signal
import urllib, BeautifulSoup
import sqlite3 as sql
from datetime import date

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
  
  if 'http://' in message.lower():
    message = 'http:' + message.split('http:')[1]
    message = message.split(' ')[0] 
    new_title = fetchTitle(message)
    map_to_database(new_title, message, user)
    server.privmsg(channel, new_title)
  elif 'https://' in message.lower():
    message = 'https:' + message.split('https:')[1]
    message = message.split(' ')[0] 
    new_title = fetchTitle(message)
    map_to_database(new_title, message, user)
    server.privmsg(channel, new_title)

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
	  
  # Admins
  elif command == 'admins':
    server.privmsg(channel, 'Admins of the bot are: ' + str(admins))
  
  # Food
  elif command == 'ruoka':
    assari = fetchFood()
    server.privmsg(channel , assari + ' | http://murkinat.appspot.com')

  # Unknown command
  else:
    server.privmsg(channel, 'Unknown command or insufficient parameters')
  
  
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
  global title
  def timeout_handler(signum, frame):
    pass

  old_handler = signal.signal(signal.SIGALRM, timeout_handler)
  signal.alarm(6)

  try:
    data = BeautifulSoup.BeautifulSoup(urllib.urlopen(url)) 
    title = str(data.find('title')).split('>')[1].split('<')[0].strip()
    signal.alarm(0)
    return title    

  except:
    pass    


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
irc.process_forever()
