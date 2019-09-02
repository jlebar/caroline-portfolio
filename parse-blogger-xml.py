#!/usr/bin/env python3

import sys
import xml
from xml.etree import ElementTree as et

NS = {
  'atom': 'http://www.w3.org/2005/Atom'
}

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

  with open('orig-%ss/%s' % (kind, title.text.replace('/', '-')), 'w') as f:
    print('+++', file=f)
    print('date = "%s"' % published.text, file=f)
    print('title = "%s"' % title.text, file=f)
    print('tags = %s' % tags, file=f)
    print('+++', file=f)
    print(content.text, file=f)
