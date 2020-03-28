'''Houses just some different utility functions'''

import re

# This function is needed because the Anselus admin ID is purposely nonconformant -- a user can
# *never* accidentally get assigned the value, and for the purposes of the platform, version 
# information doesn't matter.
def validate_uuid(indata):
	'''Validates a UUID's basic format. Does not check version information.'''

	# With dashes, should be 36 characters or 32 without
	if (len(indata) != 36 and len(indata) != 32) or len(indata) == 0:
		return False
	
	uuid_pattern = re.compile(
			r"[\da-fA-F]{8}-?[\da-fA-F]{4}-?[\da-fA-F]{4}-?[\da-fA-F]{4}-?[\da-fA-F]{12}")
	
	if not uuid_pattern.match(indata):
		return False
	
	return True

def check_password_complexity(indata):
	'''Checks the requested string as meeting the needed security standards.
	
	Returns: (dict)
	error: string
	strength: string in [very weak', 'weak', 'medium', 'strong']
	'''
	if len(indata) < 8:
		return { 'error' : 'Passphrase must be at least 8 characters.'}
	
	strength_score = 0
	strength_strings = [ 'error', 'very weak', 'weak', 'medium', 'strong', 'very strong']

	# Anselus *absolutely* permits UTF-8-encoded passwords. This greatly increases the
	# keyspace
	try:
		indata.encode().decode('ascii')
	except UnicodeDecodeError:
		strength_score = strength_score + 1
	
	if re.search(r"\d", indata):
		strength_score = strength_score + 1
	
	if re.search(r"[A-Z]", indata):
		strength_score = strength_score + 1
	
	if re.search(r"[a-z]", indata):
		strength_score = strength_score + 1

	if re.search(r"[~`!@#$%^&*()_={}/<>,.:;|'[\]\"\\\-\+\?]", indata):
		strength_score = strength_score + 1

	if (len(indata) < 12 and strength_score < 3) or strength_score < 2:
		# If the passphrase is less than 12 characters, require complexity
		return { 'error' : 'passphrase too weak', 'strength' : strength_strings[strength_score] }
	
	return { 'error' : '', 'strength' : strength_strings[strength_score] }
