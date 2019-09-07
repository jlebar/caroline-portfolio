#!/usr/bin/env python3

import os
import re
import html
import sys
import xml
from xml.etree import ElementTree as et
import bs4
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

  # <h1..h7>
  for i in range(1,7):
    for h in soup.find_all('h%d' % i):
      for br in h.find_all('br'):
        br.extract()
      if not h.contents:
        h.extract()
        continue

      h.insert_before('\n' + ('#' * i) + ' ')
      h.insert_after('\n\n')
      h.unwrap()

  # Replace <a href=...>foo</a> with markdown-style links.
  for a in soup.find_all('a'):
    if len(a.contents) == 1 and type(a.contents[0]) == bs4.element.NavigableString:
      a.replace_with('[%s](%s)' % (a.contents[0], a['href']))

  # Replace <ol>/<ul> with markdown.  By putting these in one find_all call,
  # hopefully we get top-down order, which is what we need for this to work
  # properly in the face of nested lists.
  for l in soup.find_all(['ol', 'ul']):
    pass # XXX

  x = soup.decode(formatter=None)

  x = x.replace('<br/><br/>', '\n\n')
  x = x.replace('<br/>', '\n\n')
  x = re.sub('\n\n\n*', '\n\n', x)
  x = x.strip()
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

  if kind != 'post':
    continue
  with open('content/blog/from-blogger/%s.md' % (html.unescape(title.text.replace('/', '-'))), 'w') as f:
    print('+++', file=f)
    print('date = "%s"' % published.text, file=f)
    print('title = "%s"' % title.text.replace('"', r'\"'), file=f)
    print('tags = %s' % tags, file=f)
    if isdraft:
      print('draft = true', file=f)
    print('+++', file=f)
    print(XmlToMarkdown(content.text), file=f)
