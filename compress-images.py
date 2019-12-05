#!/usr/bin/env python3

import glob
import multiprocessing
import os
import subprocess

from PIL import Image
from concurrent.futures import ThreadPoolExecutor
from humanize import naturalsize

# brew install jpeg-archive
# pip3 install Pillow humanize

THIS_MTIME = os.path.getmtime(__file__)

def compress_image(image, target_size):
  img_mtime = os.path.getmtime(image)
  outfile_name = (f'{os.path.dirname(os.path.abspath(image))}/'
                  f'.gen.{target_size}.{os.path.basename(image)}')
  if os.path.exists(outfile_name):
    out_mtime = os.path.getmtime(outfile_name)
    if out_mtime > img_mtime and out_mtime > THIS_MTIME:
      print(f'Skipping {outfile_name}')
      return

  convert_proc = subprocess.run(['convert', image, '-resize', f'{target_size}>x{target_size}>', 'ppm:-'],
                                check=True, capture_output=True)
  with open(outfile_name, 'w') as outfile:
      subprocess.run(['jpeg-recompress', '-Q', '--quality', 'low', '--method', 'smallfry', '--ppm', '-', '-'],
                     input=convert_proc.stdout, stdout=outfile, check=True)

  orig_size = os.path.getsize(image)
  new_size = os.path.getsize(outfile_name)
  print(f'{image} @{target_size} {naturalsize(orig_size)} -> {naturalsize(new_size)} '
        f'{orig_size / new_size:.2f}x')
  if new_size >= orig_size:
    os.remove(outfile_name)

def main():
  with ThreadPoolExecutor(max_workers=2 * multiprocessing.cpu_count()) as executor:
    for image in glob.glob('**/*.jpg', recursive=True):
      imgdir = os.path.dirname(image)
      if imgdir.startswith('resources/') or imgdir.startswith('public/'):
        continue

      # Don't try to upsize an image.
      img_obj = Image.open(image)
      max_dim = max(img_obj.width, img_obj.height)
      sizes = [x for x in [2048, 1536, 1024, 768, 512] if x < max_dim] + [max_dim]

      for target_size in sizes:
        executor.submit(compress_image, image, target_size)

if __name__ == '__main__':
  main()
