#!/usr/bin/env python3
'''Signs a keycard'''

import os
import sys

# import encryption
import keycard

def print_usage():
	'''Prints usage information'''
	print("%s: <custody|user|org> <priv_key> <keycard>\nSign a keycard." % \
			os.path.basename(__file__))

debug_app = True

if __name__ == '__main__':
	if debug_app:
		status = keycard.load_keycard('testcards/org.keycard')
		if status.error():
			print("Load failure: %s" % status.info())
		else:
			print(status['card'])
		sys.exit(0)

