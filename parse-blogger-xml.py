#!/usr/bin/env python3

import os
import re
import html
import sys
import xml
from xml.etree import ElementTree as et
from bs4 import BeautifulSoup

NS = {
  'atom': 'http://www.w3.org/2005/Atom',
  'app': 'http://purl.org/atom/app#',
}

def XmlToMarkdown(x):
  soup = BeautifulSoup(html.unescape(x), 'html.parser')

  # Get rid of all divs.
  for d in soup.find_all('div'):
    d.unwrap()

  # Find links which only contain an image.  Replace these with just the image
  # itself, which we get from the link URL.
  #
  # <a href="http://.../IMG_5337.JPG"><img src="http://.../IMG_5337.JPG"></a>
  for a in soup.find_all('a'):
    if len(a.contents) == 1 and a.contents[0].name == 'img':
      img = a.contents[0]
      if img['src'] and a['href'] and \
         os.path.basename(img['src']) == os.path.basename(a['href']):
        a.replace_with(BeautifulSoup('<img src="%s">' % a['href'], 'html.parser'))

  # Replace <i>foo</i> with *foo*.
  for i in soup.find_all('i'):
    i.insert_before('*')
    i.insert_after('*')
    i.unwrap()

  # Replace <b>foo</b> with **foo**.
  for b in soup.find_all('b'):
    b.insert_before('**')
    b.insert_after('**')
    b.unwrap()


  x = soup.decode(formatter=None)

  x = x.replace('<br/><br/>', '\n\n')
  x = x.replace('<br/>', '\n\n')
  return x


tree = et.parse(sys.argv[1])
root = tree.getroot()
for entry in root.findall('atom:entry', NS):
  title = entry.find('atom:title', NS)
  content = entry.find('atom:content', NS)
  published = entry.find('atom:published', NS)

  tags = []
  for cat in entry.findall('atom:category', NS):
    if cat.get('scheme') == 'http://schemas.google.com/g/2005#kind':
      kind = cat.get('term')
    elif cat.get('scheme') == 'http://www.blogger.com/atom/ns#':
      tags.append(cat.get('term'))

  if kind == 'http://schemas.google.com/blogger/2008/kind#comment':
    kind = 'comment'
  elif kind == 'http://schemas.google.com/blogger/2008/kind#post':
    kind = 'post'
  elif (kind == 'http://schemas.google.com/blogger/2008/kind#template' or
        kind == 'http://schemas.google.com/blogger/2008/kind#settings' or
        kind == 'http://schemas.google.com/blogger/2008/kind#page'):
    continue
  else:
    print('Unknown kind: %s' % kind)

  isdraft = False
  control = entry.find('app:control', NS)
  if control is not None:
    draft = control.find('app:draft', NS)
    if draft is not None and draft.text == 'yes':
      isdraft = True

  #for e in entry:
  #  print(e.tag)

  with open('orig-%ss/%s' % (kind, html.unescape(title.text.replace('/', '-'))), 'w') as f:
    print('+++', file=f)
    print('date = "%s"' % published.text, file=f)
    print('title = "%s"' % title.text, file=f)
    print('tags = %s' % tags, file=f)
    if isdraft:
      print('draft = True', file=f)
    print('+++', file=f)
    print(XmlToMarkdown(content.text), file=f)
