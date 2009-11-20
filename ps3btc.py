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
import sets
import sys
import traceback
import urllib2
import wsgiref.handlers
import calendar
import time

import nigga

from django.utils import simplejson as json
from google.appengine.ext import webapp


def html_header():
  """Prepares the HTML header for serving the home page. Returns a
  list of the HTML. The CSS has been inspired from mollio.org and is
  under the Creative Commons License."""

  return ['<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">',
          '<head><link rel="stylesheet" href="/stylesheets/main.css" type="text/css" />',
          '<title>#ps3btc ps3 tweets (ps3 better than cake)</title>',
          '<meta name="google-site-verification" content="3Y6C1jgWitOJoAcYuHQWva_lKFwMNDVD2MxlKC9TCE0" />',
          '<meta name="description" content="ps3betterthankcake - crawling twitter for latest ps3 tweets">',
          '<meta name="keywords" content="ps3 twitter, ps3 tweets, twitter mashup, twitter apps, ps3, video games, sony, playstation, playstation3, tweets">',
          '</head>',
          '<body>',
          '<div id="wrap">',
          '<div class="highlight">',
          '<h2><a href="http://twitter.com/ps3btc">#ps3btc</a> ps3 tweets (ps3 better than cake)</h2>',
          '<p><span class="ps3space">crawling twitter for the latest ps3 tweets. <a href="/">hit reload</a>',
          ]

def html_footer(html):
  """Prepares the HTML footer with Google Analytics, my signature"""
  
  l = [ '<center><div id="footer">',
        '<a href="/">#ps3btc</a>&nbsp;&nbsp;'
        '<a href="/n">#what?</a><p/>'
        'Copyright &copy; 2009 <a href="http://linkybinky.appspot.com">linkybinky</a> effective twitter targetting<p/>'
        #'Copyright &copy; 2009 <a href="http://twitter.com/hnag">Hareesh Nagarajan</a>',
        '</div></center>',
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


def get_time_ago(reference_epoch, created_at):
  tww=time.strptime(created_at, '%a, %d %b %Y %H:%M:%S +0000')
  seconds_ago = int(reference_epoch - calendar.timegm(tww))
  ret = '%d secs ago' % seconds_ago
  if seconds_ago > 60 and seconds_ago <= 3600:
    ret = '%d mins ago' % (seconds_ago / 60)
  elif seconds_ago > 3600 and seconds_ago <= 86400:
    ret = '%d hrs ago' % (seconds_ago / 3600)
  elif seconds_ago > 86400:
    ret = '%d days ago' % (seconds_ago / 86400)

  return '<span class="date">(%s)</span>' % ret
    

def html_one_tweet(tweet, html, reference_epoch):
  profile_image = tweet['profile_image_url']
  text = tweet['text']
  from_user = tweet['from_user']
  from_user_url = 'http://twitter.com/%s' % (from_user)
  created_at = tweet['created_at']
  image_url = '<img src="%s" width="32px" height="32px" ></img>' % profile_image
  url = '<a href="%s">%s</a>' % (from_user_url, image_url)
  time_ago = get_time_ago(reference_epoch, created_at)
  tweet = format_text(text)
  to_display = '%s <small>%s</small>' % (time_ago, tweet)
  
  html.append('<th class="sub"><td>%s</td><td>%s</td></th>' %
              (url, to_display))


def format_text(text):
  """Takes as an argument the contents of the tweet, formats the
  links, hashtags and @ addresses"""
  
  formatted = []
  for token_ in text.split():
    for token in token_.split('.'):
      if token.find('@') == 0:
        at = '<span class="ps3emph">@<a class="user" href="http://twitter.com/%s">%s</a></span>' % (token[1:], token[1:])
        formatted.append(at)
      elif token.find('http://') == 0:
        url = token
        if len(token) > 21:
          url = '%s...' % token[:17]
          url = '<span class="ps3emph"><a class="http" href="%s">%s</a></span>' % (token, url)
          formatted.append(url)
      elif token.find('#') == 0 and len(token) > 1:
        hashtag = '<span class="ps3emph"><a class="hashtag" href="http://search.twitter.com/search?q=%s">%s</a></span>' % (token, '%s' % token)
        formatted.append(hashtag)
      else:
        formatted.append('%s' % token[:17])
      
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
                      'bit.ly',
                      'allyourtweet.com'
                      'wordpress',
                      'alexking.org',
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

  # TODO(hareesh): &lang=en restricts seems to be broken.
  url = 'http://search.twitter.com/search.json?q=%s&rpp=100' % query

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
  non_english = 0
  
  # By doing the language restricts here and not in the search, we are
  # overcounting the non-english queries, so we fix it with the
  # non_english counter.
  for r in results:
    if not spam(r['source']):
      if r.has_key('iso_language_code'):
        if r['iso_language_code'] == 'en':
          new_results.append(r)
        else:
          non_english += 1

  # 3 columns, so we must modulo 3.
  total_to_display = len(new_results) - (len(new_results) % 3)
  num_filtered = (len(results) - total_to_display - non_english)
  logging.info('Filtered a total of %d results' % num_filtered)
  return (total_to_display, new_results, num_filtered)

def just_show_image(tweet):
  profile_image = tweet['profile_image_url']
  from_user = tweet['from_user']
  from_user_url = 'http://twitter.com/%s' % (from_user)
  return ('<a title="%s" href="%s"><img alt="%s" border=0 width=48px height=48px src="%s"></a>'
          % (from_user, from_user_url, from_user,  profile_image))

def get_images(results):
  image_list = []
  for tweet in results:
    profile_image = tweet['profile_image_url']
    # Do not show the image, if the user does not have a profile
    # picture.
    if profile_image.find('default_profile_') == -1:
      from_user = tweet['from_user']
      from_user_url = 'http://twitter.com/%s' % (from_user)
      image_list.append('<a title="%s" href="%s"><img alt="%s" border=0 width=48px height=48px src="%s"></a>'
                        % (from_user, from_user_url, from_user,  profile_image))
    
  # Do this to remove dupe images
  return list(sets.Set(image_list))

def get_hot_hashtags(results):
  hashtags = {}
  for tweet in results:
    text = tweet['text'].lower()
    for token_ in text.split():
      for token in token_.split('.'):
        if token.find('#') == 0 and len(token) > 1:
          if hashtags.has_key(token):
            hashtags[token] += 1
          else:
            hashtags[token] = 1

  inv = {}
  for k, v in hashtags.iteritems():
    inv[v] = inv.get(v, [])
    inv[v].append(k)

  counts = inv.keys()
  counts.sort()
  counts.reverse()
  
  html = []
  html.append('<span class="hashtagspace">')
  for count in counts:
    for hashtag in inv[count]:
      just_tag = hashtag[1:]
      if just_tag.isalnum():
        css_tag='hashtag3'
        if count >= 10:
          css_tag='hashtag1'
        elif count >=5 and count < 10:
          css_tag='hashtag2'
        html.append('<span class="%s"><a class="%s" href="http://search.twitter.com/search?q=%s">%s (%d)</a></span>&nbsp;' %
                    (css_tag, css_tag, hashtag, hashtag, hashtags[hashtag]))
  html.append('</span>')
  return html
  
def render_home(html, query):
  """Render the all important home page, with the tweets and all that."""

  header = html
  
  try:
    results = do_search(query, html)
    reference_epoch = time.time()
    if results:
      (num_results, filtered_results, num_filtered) = filter_results(results)
      html.append('&nbsp;(supressed %d spammy tweets)</p>' % num_filtered)
      html.append('</span></div>')

      # Generate block of photos
      html.append('<table class="table1">')
      for image in get_images(filtered_results):
        html.append(image)
      html.append('</table>')

      # Generate hot tags
      html.append('<table class="table1">')
      for tag in get_hot_hashtags(filtered_results):
        html.append(tag)
      html.append('</table>')

      html.append('<table class="table1">')
      html.append('<tbody>')
      html.append('<tr>')
      cnt = 0
      for tweet in filtered_results:
        cnt += 1
        html_one_tweet(tweet, html, reference_epoch)
        if (cnt % 3) == 0:
          html.append('</tr><tr>')
          if cnt == num_results:
            html.append('</tbody></table>')
            break
      html_footer(html)
      payload = '\n'.join(html)
      return payload.encode('ascii', 'ignore')
  except Exception, e:
    s = StringIO.StringIO()
    traceback.print_exc(file=s)
    logging.error('Oops: %s', s.getvalue())
    html = header
    html.append('<center><h3>Oh noes! something is br0ken.'
                ' hit refresh?</h3></center>')
    html_footer(html)
    payload = '\n'.join(html)
    return payload.encode('ascii', 'ignore')

                
class Ps3Handler(webapp.RequestHandler):
  """A / (ps3) handler for our little webserver."""
  
  def get(self):
    html = html_header()
    self.response.out.write(render_home(html, 'ps3'))


class NiggaHandler(webapp.RequestHandler):
  """A /nigga handler for our little webserver."""
  
  def get(self):
    html = nigga.html_header()
    self.response.out.write(render_home(html, 'nigga'))

    
def main():
  application = webapp.WSGIApplication([
      ('/', Ps3Handler),
      ('/n', NiggaHandler),
      ], debug=True)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
