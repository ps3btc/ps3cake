#!/usr/bin/env python
#
# Copyright 2009 Hareesh Nagarajan.

"""Powers http://ps3btc.com ps3 is better than cake.

To test: dev_appserver.py ps3btc/
To push: appcfg.py update ps3btc/
"""

__author__ = 'hareesh.nagarajan@gmail.com (Hareesh Nagarajan)'


import StringIO
import logging
import sys
import traceback
import urllib2
import wsgiref.handlers

from django.utils import simplejson as json
from google.appengine.ext import webapp


def html_header():
  """Prepares the HTML header for serving the home page. Returns a
  list of the HTML. The CSS has been inspired from mollio.org and is
  under the Creative Commons License."""

  return ['<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">',
          '<head><link rel="stylesheet" href="/stylesheets/main.css" type="text/css" />',
          '<title>#ps3btc ps3 better than cake</title>',
          '<meta name="google-site-verification" content="3Y6C1jgWitOJoAcYuHQWva_lKFwMNDVD2MxlKC9TCE0" />',
          '<meta name="description" content="ps3betterthankcake - crawling twitter for latest ps3 tweets">',
          '<meta name="keywords" content="ps3 twitter, ps3 tweets, twitter mashup, twitter apps, ps3, video games, sony, playstation, playstation3, tweets">',
          '</head>',
          '<body>',
          '<div id="wrap">',
          '<div class="highlight">',
          '<h2><a href="http://twitter.com/ps3btc">#ps3btc</a> ps3 better than cake</h2>',
          '<p>crawling twitter for latest ps3 tweets. <a href="/">just hit refresh</a>. <a href="http://twitter.com/hnag">kthxbai</a>',
          ]

# </p></div>


def html_footer(html):
  """Prepares the HTML footer with Google Analytics, my signature"""
  
  l = [ '<center>',
        'Copyright &copy; 2009 <a href="http://twitter.com/hnag">Hareesh Nagarajan</a><p/><p/>',
        '</center>',
        '<script type="text/javascript">',
        'var gaJsHost = (("https:" == document.location.protocol) ? "https://ssl." : "http://www.");',
        'document.write(unescape("%3Cscript src=\'" + gaJsHost + "google-analytics.com/ga.js\' type=\'text/javascript\'%3E%3C/script%3E"));',
        '</script>',
        '<script type="text/javascript">',
        'try {',
        'var pageTracker = _gat._getTracker("UA-11576058-1");',
        'pageTracker._trackPageview();',
        '} catch(err) {}</script>'
        '</body>'
        '</html>'
        ]
  for i in l:
    html.append(i)


def html_one_tweet(tweet, html):
  profile_image = tweet['profile_image_url']
  text = tweet['text']
  from_user = tweet['from_user']
  from_user_url = 'http://twitter.com/%s' % (from_user)
  image_url = '<img src="%s" width="48px" height="48px" ></img>' % profile_image
  html.append('<th class="sub">'
            '<a href="%s">%s'
              '</a>&nbsp;'
              '<small>%s</small></th>' % (from_user_url, image_url, format_text(text)))


def format_text(text):
  """Takes as an argument the contents of the tweet, formats the
  links, hashtags and @ addresses"""
  
  formatted = []
  for token in text.split():
    if token.find('@') == 0:
      at = '<a href="http://twitter.com/%s">%s</a>' % (token[1:], token)
      formatted.append(at)
    elif token.find('http://') == 0:
      url = '<a href="%s">%s</a>' % (token, token)
      formatted.append(url)
    elif token.find('#') == 0 and len(token) > 1:
      hashtag = '<a href="http://search.twitter.com/search?q=%s">%s</a>' % (token, token)
      formatted.append(hashtag)
    else:
      formatted.append(token)
      
  return ' '.join(formatted)


def spam(source):
  """Takes as argument the source used to generate the tweet. Returns
  true (=spam)if the source belongs to the following sources such as
  RSS feeds, vanilla usage of the twitter API, etc. TODO(hareesh): In
  my opinion, I've seen a large percentage of of spammers and bots use
  this mechanism to tweet."""

  ignore_sources =  [ 'apiwiki.twitter.com',
                      'twitterfeed.com',
                      'rss2twitter.com',
                      'skygrid.com',
                      'assetize.com',
                      'Twitter Tools',
                      'wp-to-twitter',
                      ]

  for ign in ignore_sources:
    if source.find(ign) >= 0:
      return True

  return False  


def do_search(query, html):
  """Makes a get request fetching the JSON from twitter. If something
  is broken, we jam a 'something is broken' message into the HTML and
  return None. On success we return the dictionary of the search
  results."""
  
  url = 'http://search.twitter.com/search.json?q=%s&rpp=100&lang=en' % query

  try:
    handle = urllib2.urlopen(url)
    data = json.loads(handle.read())
    return data['results']
  except Exception, e:
    html.append('<center><h3>Oh noes! something is br0ken.'
                ' hit refresh?</h3></center>')
    s = StringIO.StringIO()
    traceback.print_exc(file=s)
    logging.error('Oops: %s', s.getvalue())
    return None


def filter_results(results):
  """Takes in a list of results that twitter search API has returned
  and filter all the spammy results out. Returns (number of results to
  display, list of results, number of filtered results)"""

  new_results = []
  for r in results:
    if not spam(r['source']):
      new_results.append(r)

  # 3 columns, so we must modulo 3.
  total_to_display = len(new_results) - (len(new_results) % 3)
  num_filtered = (len(results) - total_to_display)
  logging.info('Filtered a total of %d results' % num_filtered)
  
  return (total_to_display, new_results, num_filtered)

  
def render_home():
  """Render the all important home page, with the tweets and all that."""
  
  html = html_header()
  results = do_search('ps3', html)
  
  if results:
    (num_results, filtered_results, num_filtered) = filter_results(results)
    html.append('&nbsp;(supressed %d spammy tweets)' % num_filtered)
    html.append('</p></div>')
    html.append('<table class="table1">')
    html.append('<tbody>')
    html.append('<tr>')
    cnt = 0
    for tweet in filtered_results:
      cnt += 1
      html_one_tweet(tweet, html)
      if (cnt % 3) == 0:
        html.append('</tr><tr>')
      if cnt == num_results:
        html.append('</tbody></table>')
        break
      
  html_footer(html)
  payload = '\n'.join(html)
  return payload.encode('ascii', 'ignore')

                
class MainHandler(webapp.RequestHandler):
  """A main handler for our little webserver."""
  
  def get(self):
    self.response.out.write(render_home())

    
def main():
  application = webapp.WSGIApplication([('/', MainHandler)],
                                       debug=True)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
