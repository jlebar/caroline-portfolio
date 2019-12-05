#!/usr/bin/env python3

import os
import glob
import subprocess
from humanize import naturalsize

# brew install jpeg-archive

def compress_image(image, target_size):
  outfile_name = (f'{os.path.dirname(os.path.abspath(image))}/'
                  f'.gen.{target_size}.{os.path.basename(image)}')

  convert_proc = subprocess.run(['convert', image, '-resize', f'{target_size}>x{target_size}>', 'ppm:-'], check=True, capture_output=True)
  with open('/dev/null', 'w') as dev_null:
    with open(outfile_name, 'w') as outfile:
      subprocess.run(['jpeg-recompress', '--method', 'smallfry', '--ppm', '-', '-'],
                     input=convert_proc.stdout, stdout=outfile, stderr=dev_null, check=True)
  orig_size = os.path.getsize(image)
  new_size = os.path.getsize(outfile_name)
  print(f'{image}@{target_size} {naturalsize(orig_size)} -> {naturalsize(new_size)} '
        f'{orig_size / new_size:.2f}x')
  if new_size >= orig_size:
    shutil.copyfile(image, outfile_name)

images = glob.glob('**/*.jpg', recursive=True)
for image in images:
  if image.startswith('resources'):
    continue
  for target_size in (1024, 512):
    compress_image(image, target_size)
