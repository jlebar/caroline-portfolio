#!/usr/bin/env python3

# TODO:
# Collapsible blog year headers
# Two columns (except on mobile)
# Google custom search box, https://support.google.com/customsearch/answer/4513897?hl=en&ref_topic=4513742
# Download images.
# If two vertical-orientation images are next to each other, flow them together.

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

SHORTLINK_TO_TITLE = {
  'biking-to-work.html': 'Biking to Work.md',
  'book-review-architectural-agents.html': 'Book Review: Architectural Agents.md',
  'book-review-collapse.html': 'Book Review: "Collapse".md',
  'c-bip-studio-part-i.html': 'C-BIP Studio Part I.md',
  'c-bip-studio-part-ii.html': 'C-BIP Studio Part II.md',
  'competition-entry-for-home-matters-design': 'Confederate Monuments, Art History, and the Public Square.md',
  'competitions-critique-and-pop-up-tents.html': 'Competitions, Critique, and Pop-up Tents.md',
  'exhibition-review-eoys-2012.html': 'Exhibition Review: "Architectural Pavilions"',
  'hello-silicon-valley.html': 'Hello Silicon Valley!.md',
  'housing-affordability-in-bay-area.html': 'Housing Affordability in the Bay Area: An Architectural Perspective.md',
  'into-wilderness.html': 'Into the Wilderness.md',
  'israelpalestine-day-3-4.html': 'Israel-Palestine: Day 3-4.md',
  'israelpalestine-day-5.html': 'Israel-Palestine: Day 5.md',
  'kinne-trip-japan.html': 'Kinne Trip: Japan!.md',
  'kinne-trip-part-2.html': 'Kinne Trip: Part 2.md',
  'kinne-trip-part-3.html': 'Kinne Trip: Part 3.md',
  'kinne-trip-part-4.html': 'Kinne Trip: Part 4.md',
  'new-year-new-resolutions.html': 'New Year, New Resolutions.md',
  'on-border-part-i.html': 'On the Border: Part I.md',
  'on-border-part-ii.html': 'On the Border: Part II.md',
  'on-border-part-iii.html': 'On the Border: Part III.md',
  'on-border-part-iv.html': 'On the Border: Part IV.md',
  'thoughts-on-studio-model.html': 'Thoughts on the Studio Model.md',
  'urban-design-studio-suburban-retrofit.html': 'Urban Design Studio: Suburban Retrofit in Denmark.md',
  'visiting-grand-canyon-part-1.html': 'Visiting the Grand Canyon: Part 1.md',
  'visiting-grand-canyon-part-2.html': 'Visiting the Grand Canyon: Part 2.md',
  'visiting-grand-canyon-part-3.html': 'Visiting the Grand Canyon: Part 3.md',
  'visiting-hawaii-part-1.html': 'Visiting Hawaii - Part 1.md',
  'visiting-hawaii-part-2.html': 'Visiting Hawaii - Part 2.md',
  'visiting-washington-dc.html': 'Visiting Washington, DC.md',
  'yes-is-more-kind-of-big-deal.html': '"YES IS MORE": Kind of a BIG Deal.md',
}

FORCE_SKIP_FILES = {
  r"""content/blog/from-blogger/Debt Slavery, the Virtual Economy, and "Ready Player One".md""",
  r"""content/blog/from-blogger/Thoughts on the Studio Model.md""",
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
  #
  # Sometimes the <a> contains whitespace and an image, which is ugh, but okay.
  for a in soup.find_all('a'):
    non_whitespace_contents = [
      c for c in a.contents
      if not (isinstance(c, bs4.element.NavigableString) and not c.strip())
    ]
    if len(non_whitespace_contents) == 1 and non_whitespace_contents[0].name == 'img':
      img = non_whitespace_contents[0]
      if img['src'] and a['href'] and \
         os.path.basename(img['src']) == os.path.basename(a['href']):
        a.replace_with(BeautifulSoup('<img src="%s">' % a['href'], 'html.parser'))

  # Find tables which contain an image + caption.
  for table in soup.find_all('table'):
    if table['class'] == ['tr-caption-container']:
      # Assume there are exactly two 'tr's in the tbody; one for the image, the
      # other for the caption.
      tbody = table.find('tbody')
      rows = tbody.find_all('tr')
      if len(rows) != 2:
        # There don't appear to be any tables left that are != 2 rows, yay.
        continue
      img_row, cap_row = rows
      img = img_row.td.img
      cap = cap_row.td.text.replace('"', '\\"')
      table.replace_with(f'\n{{{{< figure src="{img["src"]}" caption="{cap}" >}}}}\n')

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
  fix_simple_format('strike', '~~')

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
      href = a['href']
      if href.startswith('http://notbuiltinaday.blogspot.com'):
        title = SHORTLINK_TO_TITLE[href.split("/")[-1]].replace('"', r'\"')
        href = f'{{{{< ref "/blog/from-blogger/{title}" >}}}}'
      a.replace_with(f'[{a.contents[0]}]({href})')

  # Replace <ol>/<ul> with markdown.
  #
  # This doesn't work with nested lists, but thankfully we don't seem to have
  # any.
  for l in soup.find_all(['ol', 'ul']):
    # Check that all of the <li>s are plain text.
    if [li for li in l.contents if
        [c for c in li.contents if not isinstance(c, bs4.element.NavigableString)]]:
      print('ol/ul contains non-text contents:')
      print(str(l))
    for li in l.contents:
      text = ''.join(c for c in li.contents)
      sigil = '1.' if l.name == 'ol' else '* '
      li.replace_with(f'\n  {sigil} ' + text.replace('\n', '\n     '))
    l.insert(0, bs4.element.NavigableString('\n'))
    l.unwrap()

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
