# anem.py: Utility to encode and decode the Anselus Encrypted Message format
# Usage: 	anem encode <keyname> messagefile [attachment1 [attachment2...]]
#			anem decode file directory
# ©2020 Jon Yoder <jsyoder@mailfence.com>
# Released under the MIT license
import sys

def PrintUsage():
	'''Prints usage information'''
	print("Usage: anem encode <keyname> messagefile [attachment1 [attachment2...]]\n"
			"anem decode file directory")
	sys.exit(-1)

if __name__ == '__main__':
	if len(sys.argv) < 3:
		PrintUsage()
