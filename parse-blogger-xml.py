#!/usr/bin/env python3

# TODO:
# Collapsible blog year headers
# Two columns (except on mobile)
# Google custom search box, https://support.google.com/customsearch/answer/4513897?hl=en&ref_topic=4513742
# Blog posts should say "back to blog main page"
# About page has weird footer.
# Download images.

import functools
import html
import os
import re
import subprocess
import shlex
import sys
import xml
from xml.etree import ElementTree as et
import bs4
from bs4 import BeautifulSoup

NS = {
  'atom': 'http://www.w3.org/2005/Atom',
  'app': 'http://purl.org/atom/app#',
}

FORCE_SKIP_FILES = {
  r"""content/blog/from-blogger/Debt Slavery, the Virtual Economy, and "Ready Player One".md"""
}

@functools.lru_cache()
def FilesToSkip():
  git_out = subprocess.check_output([
    'git',
    'log',
    '--name-only',
    '--author', 'caroline',
    '--pretty=format:',
    'content/blog/from-blogger',
  ]).decode('utf-8').split('\n')

  return {shlex.split(f)[0] if f.startswith('"') else f for f in git_out if f} | FORCE_SKIP_FILES

def XmlToMarkdown(x):
  x = html.unescape(x)

  # Escape asterisks.  I have no idea why I need two semicolons; BeautifulSoup
  # must somehow be eating one.
  x = x.replace('*', '&ast;;')

  # Replace nbsp with regular space.  This may mess up formatting that relies
  # on nbsp, but it's important because you need spaces around e.g. * for
  # markdown to format it properly.
  x = x.replace('\u00A0', ' ')

  soup = BeautifulSoup(x, 'html.parser')

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

  # TODO: Handle inter-blog links, e.g.
  #  "Missed the first part?  Back to Part 1"

  # TODO: Handle something like
  # <table align="center" cellpadding="0" cellspacing="0" class="tr-caption-container" style="margin-left: auto; margin-right: auto; text-align: center;"><tbody><tr><td style="text-align: center;"><img src="https://4.bp.blogspot.com/-vQjL5Y76rr8/XCxK2pfPtqI/AAAAAAAAYrA/ZQrKZFbbOUg9gLCiuS00NoyZY-uemRu4gCKgBGAs/s1600/IMG_20180913_193214.jpg"/></td></tr><tr><td class="tr-caption" style="text-align: center;">*Boots on the ground, if you will.*</td></tr></tbody></table>

  # TODO: Bad captions in e.g. book-review-selling-jerusalem
  # TODO: Bad italics in e.g. book-review-selling-jerusalem

  # TODO: Links inside of <ul> </ol>, e.g. on-the-border-part-v

  # TODO: Download and resize giant images.

  def fix_simple_format(tag, replacement):
    for t in soup.find_all(tag):
      if t.string and t.string.endswith(' '):
        if t.string.endswith(' '):
          t.string.replace_with(t.string[:-1])
          t.insert_after(' ')

      if list(s for s in t.stripped_strings if s):
        t.insert_before(replacement)
        t.insert_after(replacement)
      t.unwrap()

  # Replace <i>foo</i> with *foo*, and same for <u>.
  fix_simple_format('i', '*')
  fix_simple_format('b', '**')

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
  title_node = entry.find('atom:title', NS)
  content = entry.find('atom:content', NS)
  published = entry.find('atom:published', NS)

  title = title_node.text.strip()

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
  filename = 'content/blog/from-blogger/%s.md' % (html.unescape(title.replace('/', '-')))
  if filename in FilesToSkip():
    print('Skipping because was modified by a human: %s' % filename)
    continue

  with open(filename, 'w') as f:
    print('+++', file=f)
    print('date = "%s"' % published.text, file=f)
    print('title = "%s"' % title.replace('"', r'\"'), file=f)
    print('tags = %s' % tags, file=f)
    if isdraft:
      print('draft = true', file=f)
    print('+++', file=f)
    print(XmlToMarkdown(content.text), file=f)
