#!/usr/bin/env python

import argparse
import json
import os
import os.path
import sys
import tempfile
import zipfile

try:
    from urlparse import urlparse
    from urllib import urlencode
    from urllib2 import urlopen
except ModuleNotFoundError:
    from urllib.parse import urlparse
    from urllib.parse import urlencode
    from urllib.request import urlopen

arg_parser = argparse.ArgumentParser(description='Chrome extension downloader')
arg_parser.add_argument('id_or_url',
    help='ID or full URL of the extension in Chrome Web Store')
arg_parser.add_argument('-q', '--quiet',
    action='store_true',
    help='suppress all messages')

# Create a mutually exclusive group for -o and -n
output_group = arg_parser.add_mutually_exclusive_group()
output_group.add_argument('-o', '--output-file',
    required=False,
    help='where to save the .CRX file')
output_group.add_argument('-n', '--use-name',
    action='store_true',
    help='save the .CRX file using the extension name from manifest')

args = arg_parser.parse_args(sys.argv[1:])

try:
    ext_url = urlparse(args.id_or_url)
    ext_id = os.path.basename(ext_url.path)
except:
    ext_id = args.id_or_url

crx_base_url = 'https://clients2.google.com/service/update2/crx'
crx_params = urlencode({
    'response': 'redirect',
    'prodversion': '133.0',
    'acceptformat': 'crx2,crx3',
    'x': 'id=' + ext_id + '&uc'
})
crx_url = crx_base_url + '?' + crx_params

# Determine initial download path
if args.output_file:
    crx_path = args.output_file
else:
    crx_path = ext_id + '.crx'

if not args.quiet:
    print('Downloading {} to {} ...'.format(crx_url, crx_path))

with open(crx_path, 'wb') as file:
    file.write(urlopen(crx_url).read())

# If using -n option, extract extension name and rename file
if args.use_name:
    try:
        with zipfile.ZipFile(crx_path, 'r') as zip_file:
            with zip_file.open('manifest.json') as manifest_file:
                manifest = json.load(manifest_file)
                ext_name = manifest.get('name', ext_id)

                # Sanitize filename by removing/replacing invalid characters
                sanitized_name = "".join(c for c in ext_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                if not sanitized_name:
                    sanitized_name = ext_id

                final_path = sanitized_name + '.crx'

                # Rename the temporary file to the final name
                os.rename(crx_path, final_path)
                crx_path = final_path

                if not args.quiet:
                    print('Renamed to: {}'.format(final_path))
    except (zipfile.BadZipFile, KeyError, json.JSONDecodeError) as e:
        if not args.quiet:
            print('Warning: Could not extract extension name from manifest: {}. Using ID instead.'.format(str(e)))
        # Rename temp file to ID-based name
        id_path = ext_id + '.crx'
        os.rename(crx_path, id_path)
        crx_path = id_path

if not args.quiet:
    print('Success!')
