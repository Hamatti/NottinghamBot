import nottingham
import re

ham = nottingham.Nottingham()
ham.set_up()

url = 'http://www.youtube.com/watch?v=mIyNduHMsEc'.decode('utf-8')
print re.search(ham.url_match_pattern, url).group()

print ham.fetch_title(url)
