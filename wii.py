#!/usr/bin/env python
#
# Copyright 2009 Hareesh Nagarajan.

def html_header():
  """Prepares the HTML header for serving the home page. Returns a
  list of the HTML. The CSS has been inspired from mollio.org and is
  under the Creative Commons License."""
  
  return ['<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">',
          '<head><link rel="stylesheet" href="/stylesheets/main.css" type="text/css" />',
          '<title>#wii tweets</title>',
          '<meta name="description" content="wii what - crawling twitter for latest tweets with the word wii">',
          '<meta name="keywords" content="wii tweets, wii twitter, twitter mashup">',
          '</head>',
          '<body>',
          '<div id="wrap">',
          '<div class="highlight">',
          '<h2><a href="/n">#wii</a> tweets</h2>',
          '<p><span class="ps3space">crawling twitter for latest tweets with word <b>wii</b> in them. <a href="/n">hit reload</a>',
          ]
