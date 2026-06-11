#!/usr/bin/env python3

import configparser
import requests
import sys
import getopt

verbose = False
try:
	# parse CLI options
	opts, argvs = getopt.getopt(sys.argv[1:], "hv", ["config=", "test", "help", "verbose"])
	config_fullpath = ""
	for o, a in opts:
		if o == '--test':
			path_config = './'
			config_filename = 'config.py'
			config_fullpath = path_config+config_filename
		elif o == '--config':
			config_fullpath = a
		elif o in ("-h", "--help"):
			raise getopt.GetoptError('help')
		elif o in ("-v", "--verbose"):
			verbose = True
	if config_fullpath == "":
		raise getopt.GetoptError('help')
except getopt.GetoptError as err:
	print('Please use as: ./fb-hoarder.py --config </path/to/config/file>|--test ')
	sys.exit(2)

# reading config file at config_fullpath
config = configparser.ConfigParser()
config.read(config_fullpath)

old_fb_access_token = config['facebook']['fb_access_token']

# requesting new fb_access_token
r = requests.get('https://graph.facebook.com/oauth/access_token?client_id=1888315781392788&client_secret=c6e2148fad59db14a22b520bbe4b4ee0&grant_type=fb_exchange_token&fb_exchange_token={}'.format(old_fb_access_token))

new_fb_access_token = r.json()["access_token"]

# writing to config file at config_fullpath
config['facebook']['fb_access_token'] = new_fb_access_token
with open(config_fullpath, 'w') as configfile:
	config.write(configfile)

# if verbose, output some information on what has been done
if verbose:
	print('\n- Old FB Token {}, \n- New FB Token: {}'.format(old_fb_access_token, new_fb_access_token))
	print('- Config file {} updated'.format(config_fullpath))





