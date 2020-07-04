#!/usr/bin/env python3
'''Signs a keycard'''

import os
import sys

import encryption
import keycard

def print_usage():
	'''Prints usage information'''
	print("%s: <custody|user|org> <priv_key> <keycard>\nSign a keycard." % \
			os.path.basename(__file__))

debug_app = True

if __name__ == '__main__':
	if debug_app:
		status = keycard.load_keycard('testcards/user.keycard')
		if status.error():
			print("User keycard load failure: %s" % status.info())
			sys.exit(0)
		else:
			print("User keycard:\n%s\n" % str(status['card']))
		user_card = status['card']
		
		status = encryption.load_signingpair('testcards/user_signing_keypair.jk')
		if status.error():
			print("Signing key load failure: %s" % status.info())
			sys.exit(0)
		else:
			print("User signing key:\n%s\n" % str(status['keypair']))
		user_key = status['keypair']

		status = encryption.load_signingpair('testcards/org_signing_keypair.jk')
		if status.error():
			print("Signing key load failure: %s" % status.info())
			sys.exit(0)
		else:
			print("Organization signing key:\n%s\n" % str(status['keypair']))
		org_key = status['keypair']

		user_card.sign(user_key.private, 'User')
		print("After user signature:\n%s\n" % str(user_card))
		user_card.sign(org_key.private, 'Organization')
		print("After organization signature:\n%s\n" % str(user_card))
