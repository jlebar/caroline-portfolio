#!/usr/bin/env python3

import glob
import multiprocessing
import os
import subprocess
import tempfile

from PIL import Image
from concurrent.futures import ThreadPoolExecutor
from humanize import naturalsize

# brew install jpeg-archive
# pip3 install Pillow humanize

THIS_MTIME = os.path.getmtime(__file__)

SKIP_DIRS = ['public', 'resources', 'blogger-images']
OUTDIR = '_gen'

def compress_image(image, target_size):
  img_mtime = os.path.getmtime(image)
  img_noext, img_ext = os.path.splitext(os.path.basename(image))

  outdir = os.path.join(os.path.dirname(image), OUTDIR)
  try:
    os.mkdir(outdir)
  except FileExistsError:
    pass

  outfile_name = (f'{outdir}/{img_noext}.{target_size}{img_ext}')

  if os.path.exists(outfile_name):
    out_mtime = os.path.getmtime(outfile_name)
    if out_mtime > img_mtime and out_mtime > THIS_MTIME:
      print(f'Skipping {outfile_name}')
      return

  def compress(method):
    convert_proc = subprocess.run(['convert', image, '-resize', f'{target_size}>x{target_size}>', 'ppm:-'],
                                  check=True, capture_output=True)
    recompress_proc = subprocess.run(['jpeg-recompress', '-Q', '--quality', 'low', '--method', method, '--ppm', '-', '-'],
                   input=convert_proc.stdout, capture_output=True, check=True)
    return recompress_proc.stdout

  # Work around https://github.com/danielgtaylor/jpeg-archive/issues/24.
  try:
    compressed = compress('smallfry')
  except subprocess.CalledProcessError as e:
    print(f'Compressing {image} -> {outfile_name} with smallfry failed.  Trying with standard method...')
    try:
      compressed = compress('ssim')
    except subprocess.CalledProcessError as e:
      raise Exception(f'Error compressing {image} -> {outfile_name}') from e

  with open(outfile_name, 'wb') as outfile:
    outfile.write(compressed)

  subprocess.check_call(['exiftool', '-overwrite_original', '-tagsFromFile', image, outfile_name], stdout=subprocess.DEVNULL)

  orig_size = os.path.getsize(image)
  new_size = os.path.getsize(outfile_name)
  print(f'{image} @{target_size} {naturalsize(orig_size)} -> {naturalsize(new_size)} '
        f'{orig_size / new_size:.2f}x')

  # TODO: Would be nice to delete "compressed" images which are not actually
  # smaller, but ultimately it doesn't matter much, and not doing this makes
  # the script more complicated bc somehow I have to realize, when rerunning,
  # that I'd hit this case.
  #if new_size >= orig_size:
  #  os.remove(outfile_name)

def main():
  futures = []
  with ThreadPoolExecutor(max_workers=2 * multiprocessing.cpu_count()) as executor:
    for image in glob.glob('**/*.jpg', recursive=True):
      imgdir = os.path.dirname(image)
      if [x for x in SKIP_DIRS if imgdir.startswith(f'{x}/') or imgdir == x] or imgdir.endswith(f'/{OUTDIR}'):
        continue

      # Don't try to upsize an image.
      img_obj = Image.open(image)
      max_dim = max(img_obj.width, img_obj.height)
      sizes = [x for x in [2048, 1536, 1024, 768, 512] if x < max_dim] + [max_dim]

      for target_size in sizes:
        futures.append(executor.submit(compress_image, image, target_size))

  for f in futures:
    f.result()

if __name__ == '__main__':
  main()
