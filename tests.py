#!/usr/bin/python
# -*- coding: utf-8 -*-

import unittest
import bot_exceptions 
from nottingham_v2 import *

class nottinghamTest(unittest.TestCase):

	def setUp(self):
		self.bot = Nottingham()
		self.bot.set_up()

	def test_setup_network(self):
		self.assertEqual(self.bot.network, 'irc.in.tum.de')

	def test_setup_port(self):
		self.assertEqual(self.bot.port, 6667)    	

	def test_setup_channels(self):
		self.assertEqual(self.bot.channels, ['#nottingham', '#nottingham-test'])

	def test_setup_nick(self):
		self.assertEqual(self.bot.nick, 'RobinHoodie')

	def test_setup_name(self):
		self.assertEqual(self.bot.name, 'New Sheriff of Nottingham')

	def test_setup_admins(self):
		self.assertEqual(self.bot.admins, 			'vianah,alpeha,jumasan,jmaoja,jopemi,pesape,aatkin,anttlai,toalla,smau,hamatti'.split(','))

    # def test_google_title_returns_correct_title(self):
    #     google_title = self.bot.fetch_title('http://www.google.com')
    #     self.assertEqual('App. Doc. Something.', google_title)
        
    # def test_iltalehti_title_returns_correct_title(self):
    # 	iltalehti_title = self.bot.fetch_title('www.iltalehti.fi')
    #     self.assertEqual('Iltalehti.fi | IL - Suomen suurin uutispalvelu', iltalehti_title)

    # # def test_hamatti_org_raises_title_exception(self):
    # # 	self.assertRaises(bot_exceptions.TitleException, self.bot.fetch_title, 'www.hamatti.org')

    # def test_help(self):
    # 	help = self.bot.help('a', 'b', 'c', 'd')
    # 	self.assertEqual(help, 'Usage: !wiki, !help, !prio, !food, !decide, !todo, !poem, !title, !no, !reload, !badumtsh, !steam')

    # def test_wikipedia(self):
    # 	wikiquery = u'Bob Dylan (pron.: /ˈdɪlən/; born Robert Allen Zimmerman; May 24, 1941) is an American musician, singer-songwriter, record producer, artist, poet, and writer. He has been an influential figure in popular music and culture for more than five decades.[2][3] Much of his most celebrated work dates from t @ http://en.wikipedia.org/wiki/Bob%20Dylan'
    # 	self.assertEqual(self.bot.read_wikipedia('Hamatti', 'hamatti', ['Bob', 'Dylan'], '#nottingham'), wikiquery)

    # def test_food_on_nonfood_day_to_get_exception(self):
    # 	self.assertRaises(bot_exceptions.RestaurantException, self.bot.fetch_food, 'Hamatti', 'hamatti', ['assari'], '#nottingham')

    # def test_no(self):
    # 	self.assertEqual(self.bot.no('hamatti', 'hamatti', [], 'nottingham'), 'http://nooooooooooooooo.com/')

    # def test_badumtsh(self):
    # 	self.assertEqual(self.bot.badumtsh('hamatti', 'hamatti', [], 'nottingham'), 'http://instantrimshot.com/')

    # def test_arxiv(self):
    # 	self.assertEqual(self.bot.fetch_title('http://arxiv.org/abs/1303.5768'), '[1303.5768] Live music programming in Haskell')



