<h1>NottinghamBot</h1>
=============

<h2> Background </h2>

When I started studying computer science at the university, me and my friends found out we need all sorts of features to our IRC channel - most important being operator management since IRCnet doesn't provide server level bots like Quakenet's Q. So it started with that and soon started to expand to fulfill our daily needs.

<h2> Main features </h2>

<ul>
<li> <b> Operation management </b> <br />
     User can list admins to configuration file and the bot will automatically give them +o when they join the channel. This way we can avoid the situation where people come and go and we end up with no one being an operator.
</li>

<li> <b> Steam search </b> <br />
     As we are all computer scientists and we love to play games, we also love Steam. Since sharing info about games can sometimes be behind too many clicks from the client to IRC, the bot handles that for you. Just type !steam [game] and it'll tell you short description of the game as well as it's price. 
</li>

<li> <b> Website titles </b><br />
     Do you know the feeling when someone pastes a link to IRC and you're not sure if it's interesting 'cause the url itself is not telling anything? NottinghamBot follows all the links sent to channel and tells other users the title of the page so you can avoid checking out non-relevant pages.
</li>

<li> <b> Wikipedia search </b><br />
     Even we don't know everything. It's convenient to just type !what [query] and check what Wikipedia tells you. Since we are Finns, the search works in both English and Finnish using the right Wikipedia language page.
</li>

<li> <b> Decide </b><br />
     Making decisions can be difficult. To have a beer or not to have. To clean up or to play games. Users can outsource their decision making to NottinghamBot by simply !decide [option1] [option2]. Bot then makes the decision for you and before it tells it to you, you propably already know what you want.
</li>

<li> <b> Student restaurant menus </b> <br />
     As students we use student restaurants daily but not always all the places offer food we like. So NottinghamBot comes to rescue. Simply typing !food [restaurant] gives the user daily menu of the wanted restaurant with prices.
</li>
</ul>

<h2> Extensibility </h2>

Expanding the feature base is made simple. Just add the command name and its function name to <i>self.commands</i> dictionary and then define a new function that accepts five arguments: <i>self, nick of the user, username of the user, arguments and channel from which the command came</i>. After that, just return wanted output and the bot will take care of rest.

<h2> Usage </h2>

The NottinghamBot is dependent on few libraries:
<ul>
<li> <a href="http://www.crummy.com/software/BeautifulSoup/"> BeautifulSoup 4</a></li>
<li> <a href="http://code.google.com/p/ircbot-collection/source/browse/trunk/irclib.py"> irclib </a></li>
</ul>

<h2> Licence </h2>

Copyright (C) 2013 Juha-Matti Santala

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

<h2> Contact </h2>

If you have ideas how to improve the bot, feel free to fork it and make a pull request or you can contact me on Twitter @hamatti.

