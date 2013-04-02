#!/usr/bin/python
# -*- coding: utf-8 -*-
# IRCbot with few neat features
# author: Juha-Matti Santala / @hamatti

import irclib
import urllib, urllib2
import mwclient, lxml
import sys, os, signal, mimetypes, types, re
import random
from bs4 import BeautifulSoup
import ConfigParser
import sqlite3 as sql
import datetime
from bot_exceptions import *

class Nottingham(object):
	''' Bot '''
	def set_up(self):
		''' Reads config file and sets up important variables '''
		self.config = ConfigParser.RawConfigParser()
		self.config.read('config.conf')

		irclib.DEBUG = self.config.getboolean('Network', 'DEBUG')
		self.network = self.config.get('Network', 'network')
		self.port = self.config.getint('Network', 'port')
		self.channels = self.config.get('Network', 'channels').split(',')

		self.nick = self.config.get('Bot', 'nick')
		self.name = self.config.get('Bot', 'name')

		self.admins = self.config.get('Users', 'admins').split(',')
		self.todoadmin = self.config.get('Users', 'todo').split(',')

		# Luodaan irc-objekti ja serverimuuttuja irclib-kirjastosta
		self.irc = irclib.IRC()
		self.server = self.irc.server()

		self.commands = {'title': self.fetch_title, 'poem': self.fetch_poem, 'what': self.read_wikipedia, 'food': self.fetch_food, 'steam': self.steam_price, 'decide': self.decide, 'todo': self.todo, 'prio': self.change_priority, 'help': self.help, 'reload': self.reload_poems, 'no': self.no, 'badumtsh': self.badumtsh }

		self.url_match_pattern = re.compile('(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-?]*)\/?')

		self.read_poems_to_memory()

	def handle_echo(self, connection, event):
		print
		print ' '.join(event.arguments())

	def handle_no_space(self, connection, event):
		print ' '.join(event.arguments())

	def handle_priv_notice(self, connection, event):
		if event.source():
			print ':: %s -> %s' % (event.source(), event.arguments()[0])
		else:
			print event.arguments()[0]

	def handle_join(self, connection, event):
		name = event.source().split('!')[0]
		user = event.source().split('!')[1].split('@')[0]
		print '%s has joined %s' % (name, event.target())
		if user in self.admins:
			server.mode(event.target(), '+o %s' % name)

	def handle_pub_msg(self, connection, event):
		''' handles all commands (anything starting with !) '''
		name = event.source().split('!')[0]
		user = event.source().split('!')[1].split('@')[0]
		target = event.target()
		message = event.arguments()[0]
		source = event.arguments()[0]
		
		try:
			# Try to find url in the message
			url_regex_search = re.search(self.url_match_pattern, message)
			if url_regex_search:
				# If there is an url, parse its title
				url = url_regex_search.group(0).split(' ')[0]		
				result_of_command = self.commands['title'](url)
				
			elif message.startswith('!'):
				# No url so let's see if it's a command
				command = message.split(' ')[0].split('!')[1]
				arguments = message.split(' ')[1:]	
				if self.commands.has_key(command):
					result_of_command = self.commands[command](name, user, arguments, target)
				else:
					# Unknown command so do nothing
					return
			else:
				return
			self.server.privmsg(target, result_of_command)
		except (TitleException, PoemException, WikiException, RestaurantException, SteamException, DecisionException, TodoException, HelpException, Exception) as e:
			self.server.privmsg(target, e)
			raise

	def handle_priv_msg(self, connection, event):
		pass

	def handle_new_nick(self, connection, event):
		nick = '%s_' % server.get_nickname()

	def read_poems_to_memory(self):
		''' Fills self.poems with all poems listed in poems.txt '''
		self.poems = []
		for filename in open('poems.txt'):
			poemlines = []
			for line in open(filename.strip()):
				poemlines.append(line.strip())
			self.poems.append(poemlines)

	def get_soup(self, url):
		''' Given url, retrieve BeautifulSoup object '''
		if not url.startswith('http'):
			url = 'http://%s' % url
		opener = urllib2.build_opener()
		opener.addheaders = [('User-agent', 'Mozilla/5.0')]
		resource = opener.open(url)
		page_contents = resource.read()
		resource.close()
		return BeautifulSoup(page_contents, 'lxml')

	def fetch_title(self, url):
		''' Given url, parse title '''
		try:
			def timeout_handler(signum, frame):
				pass
			
			old_handler = signal.signal(signal.SIGALRM, timeout_handler)
			signal.alarm(6)

			mime = mimetypes.guess_type(url)
			if not mime[0]:
				mimetype = "None"
				file_ext = "None"
			else:
				mimetype, file_ext = mime[0].split("/")

			if mimetype.lower() == 'image':
				title = 'Image.'
				signal.alarm(0)
			elif mimetype.lower() == 'application':
				title = 'App. Doc. Something.'
				signal.alarm(0)
			else:
				soup = self.get_soup(url)
				orig_title = soup.find('title')
				title = orig_title.renderContents().replace('\n', '')
				title = ' '.join(title.split())
				signal.alarm(0)

			return title
		except:
			raise TitleException("Not found")


	def fetch_poem(self, name, user, arguments, target):
		''' Randomly select a poem and return random 3 consecutive lines from it '''
		try:
			random_poem = random.randint(0, len(self.poems) -1)
			poem = self.poems[random_poem]
			random_place = random.randint(0, len(poem)-3)
			poem_string = '%s %s %s' % (poem[random_place], poem[random_place+1], poem[random_place+2])
			if poem_string.endswith(','):
				poem_string = poem_string[:-1]
			return poem_string
		except:
			raise PoemException("Literature is dead")

	def read_wikipedia(self, name, user, arguments, target):
		''' based on query, try to retrieve first paragraph of corresponding Wikipedia page on either English or Finnish Wikipedia '''
		try:
			if len(arguments) == 0 or arguments[0] == '':
				raise WikiException('Usage: !wiki [query]')
			query = ' '.join(arguments)
			site = mwclient.Site('en.wikipedia.org')
			page = site.Pages[query]	
			
			if page.exists:
				lang = 'en'
			else:
				lang = 'fi'

			article = urllib.quote(query)
			url = 'http://%s.wikipedia.org/wiki/%s' % (lang, article)
			soup = self.get_soup(url)
			opening_paragraph = soup.find('div', id='mw-content-text').p.get_text()

			return '%s @ %s' % (opening_paragraph[:300].encode('utf-8'), url)

		except:
			raise WikiException('Page not found')

	def fetch_food(self, name, user, arguments, target):
		''' Based on query, retrieve daily menu for listed restaurants '''
		try:
			if len(arguments) == 0:
				raise RestaurantException('Usage: !food [restaurant]')
			restaurants = {'assari': 'restaurant_ag5zfm11cmtpbmF0LWhyZHIaCxISX1Jlc3RhdXJhbnRNb2RlbFYzGMG4Agw', 'delica': 'restaurant_ag5zfm11cmtpbmF0LWhyZHIaCxISX1Jlc3RhdXJhbnRNb2RlbFYzGPnPAgw', 'ict': 'restaurant_ag5zfm11cmtpbmF0LWhyZHIaCxISX1Jlc3RhdXJhbnRNb2RlbFYzGPnMAww', 'mikro': 'restaurant_ag5zfm11cmtpbmF0LWhyZHIaCxISX1Jlc3RhdXJhbnRNb2RlbFYzGOqBAgw', 'tottisalmi': 'restaurant_ag5zfm11cmtpbmF0LWhyZHIaCxISX1Jlc3RhdXJhbnRNb2RlbFYzGMK7AQw', 'tottis': 'restaurant_ag5zfm11cmtpbmF0LWhyZHIaCxISX1Jlc3RhdXJhbnRNb2RlbFYzGMK7AQw'}
			restaurant = arguments[0].lower()
			if restaurants.has_key(restaurant):
				url = 'http://murkinat.appspot.com'
				soup = self.get_soup(url)

				meal_div = soup.find(id='%s' % restaurants[restaurant])
				meal_rows = meal_div.find_all('tr', 'meal')

				meals = {}
				for meal_row in meal_rows:
					meals[meal_row.find('td', 'mealName hyphenate').string.strip()] = meal_row.find('span', 'mealPrice').string.strip()
				
				meal_string = '%s: ' % restaurant
				for meal, price in meals.iteritems():
					mealstring += '%s: %s, ' % (meal, price)
				return '%s @ %s' % (meal_string[:-2], url)
			else:
				raise RestaurantException('Tuntematon ravintola')
		except:
			raise RestaurantException('Stay hungry. Stay foolish.')

	def steam_price(self, name, user, arguments, target):
		''' Given game name, search and return description and current price '''
		try:
			if len(arguments) == 0:
				raise SteamException('Usage: !steam [game]')
			search_url = 'http://store.steampowered.com/search/?term=%s&category1=998' % ' '.join(arguments)
			soup = self.get_soup(search_url)
			searched_apps = soup.find('a', 'search_result_row')

			if not searched_apps:
				raise SteamException('Game not found')
			else:
				search_url = searched_apps['href']

			soup = self.get_soup(search_url)
			game_name = soup.find('div', 'details_block')
			game_name = str(game_name).replace('\n', '').split(':')[1].split('>')[1].split('<')[0].strip()
			description = soup.find('meta', attrs={ 'name': 'description' })
			description = str(description).split('=')[1].split("\"")[1].decode('utf-8')
			price_div = soup.find('div', 'game_purchase_price price')
			if not price_div:
				price_div = soup.find('div', 'discount_final_price')
			price = price_div.string.strip()
			game_string = '%s: %s Cost: %s' % (game_name, description[:300], price)
			return game_string.encode('utf-8')

		except:
			raise SteamException('There was an error. Probably your fault.')

	def decide(self, name, user, arguments, target):
		''' Given options (more than 1), randomly choose one '''
		try:
			if len(arguments) == 0 or arguments[0] == '':
				raise DecisionException('Usage: !decide [option1] [option2] .. [optionN]')
			decision = random.randint(1, len(arguments)-1)
			return 'Noppa ratkaisee: %s' % arguments[decision]
		except:
			raise DecisionException('Uh, couldn\'t decide')

	def todo(self, name, user, arguments, target):
		''' Given a TODO-note, save it to database '''
		try:
			if user in self.todoadmin and len(arguments) > 1:
				connection = sql.connect('todo.db')
				cursor = connection.cursor()
				dt = datetime.datetime.now()
				date = '%s-%s-%s %s:%s:%s' % (dt.year, dt.month, dt.day, int(dt.hour)+1, dt.minute, dt.second)
				cursor.execute('INSERT INTO todo (thing, date, priority) VALUES (?, ?, 4)', (" ".join(arguments).encode('utf-8'),date))
				connection.commit()
				cursor.execute('SELECT max(oid) FROM todo')
				oid = cursor.fetchone()[0]
				return 'todo #%s logged' % oid
			else:
				return 'http://hamatti.org/todo/'
		except:
			raise TodoException('Database says no. Fuck those databases')

	def change_priority(self, name, user, arguments, target):
		''' Given a priority and optional TODO-item id, change the priority in database '''
		try:
			if user in self.todoadmin:
				if len(arguments) > 0:
					connection = sql.connect('todo.db')
					cursor = connection.cursor()
					oid = 0
					if len(arguments) == 1:
						cursor.execute('SELECT max(oid) FROM todo')
						oid = cursor.fetchone()[0]
					elif len(arguments) == 2:
						oid = arguments[1]
					cursor.execute('UPDATE todo SET priority = ? WHERE oid = ?', (arguments[0], oid))
					connection.commit()
		except:
			raise TodoException('Database says no. Fuck those databases')

	def help(self, name, user, arguments, target):
		''' List all the commands in use '''
		try:
			help_string = 'Usage: '
			for command in self.commands.keys():
				if command != 'title':
					help_string += '!%s, ' % command
			return help_string[:-2]
		except:
			raise HelpException('Your parents hated you and I won\'t help you')

	def badumtsh(self, name, user, arguments, target):
		return 'http://instantrimshot.com/'

	def no(self, name, user, arguments, target):
		return 'http://nooooooooooooooo.com/'

	def reload_poems(self, name, user, arguments, target):
		''' Reload poems from the file'''
		if user == 'hamatti':
			self.read_poems_to_memory()
		return 'reloaded'

	def main(self):
		self.set_up()
		self.irc.add_global_handler ( 'privnotice', self.handle_priv_notice ) #Private notice
		self.irc.add_global_handler ( 'welcome', self.handle_echo ) # Welcome message
  		self.irc.add_global_handler ( 'yourhost', self.handle_echo ) # Host message
	  	self.irc.add_global_handler ( 'myinfo', self.handle_echo ) # "My info" message
	  	self.irc.add_global_handler ( 'featurelist', self.handle_echo ) # Server feature list
	  	self.irc.add_global_handler ( 'luserclient', self.handle_echo ) # User count
	  	self.irc.add_global_handler ( 'luserop', self.handle_echo ) # Operator count
	  	self.irc.add_global_handler ( 'luserchannels', self.handle_echo ) # Channel count
	  	self.irc.add_global_handler ( 'luserme', self.handle_echo ) # Server client count
	  	self.irc.add_global_handler ( 'n_local', self.handle_echo ) # Server client count/maximum
	  	self.irc.add_global_handler ( 'n_global', self.handle_echo ) # Network client count/maximum
	  	self.irc.add_global_handler ( 'luserconns', self.handle_echo ) # Record client count
	  	self.irc.add_global_handler ( 'luserunknown', self.handle_echo ) # Unknown connections
	  	self.irc.add_global_handler ( 'motdstart', self.handle_echo ) # Message of the day ( start )
	  	self.irc.add_global_handler ( 'motd', self.handle_no_space ) # Message of the day
	  	self.irc.add_global_handler ( 'edofmotd', self.handle_echo ) # Message of the day ( end )
	  	self.irc.add_global_handler ( 'join', self.handle_join ) # Channel join
	  	self.irc.add_global_handler ( 'namreply', self.handle_no_space ) # Channel name list
	  	self.irc.add_global_handler ( 'endofnames', self.handle_no_space ) # Channel name list ( end )
	  	self.irc.add_global_handler ( 'pubmsg', self.handle_pub_msg ) # Public messages
	  	self.irc.add_global_handler ( 'privmsg', self.handle_priv_msg ) # Private messages
	  	self.irc.add_global_handler ( 'nicknameinuse', self.handle_new_nick ) # Gives new nickname if already used
		self.server.connect(self.network, self.port, self.nick, ircname = self.name)
		for channel in self.channels:
			self.server.join(channel)
		
		self.irc.process_forever()
		

if __name__ == '__main__':
	bot = Nottingham()
	bot.main()