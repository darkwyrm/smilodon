#!/usr/bin/env python3

import secrets
import sys
import uuid

from encryption import KeyPair, SigningPair
import keycard

def create_org_entry():
	'''Creates a basic org root entry'''
	out = keycard.OrgEntry()
	out.set_fields({
		"Name":"Anselus Test, Inc.",
		"Contact-Admin":"admin/anselus.test",
		"Primary-Verification-Key":"ED25519:qn#mJQz&AB<@v_PhEzGBXsCgxM8(+wd;toMSZGhM",
		"Encryption-Key":"CURVE25519:by9+6%#*!>Ba?Q;xAGYVr`L~|2>`1!FS_|7n<^w3"
	})
	rv = out.generate_hash('BLAKE2B-256')
	skey = SigningPair()
	signing_key = keycard.EncodedString()
	signing_key.prefix = 'ED25519'
	signing_key.data = skey.get_private_key85()
	rv = out.sign(signing_key, "Organization")
	if rv.error():
		print(f'Org signing failure: {str(rv)}')
		sys.exit(-1)
	return out


def create_random_user_entry():
	'''Returns a random entry'''
	first_names = [ "Leanne", "Lauryn", "Cheryl", "Addie", "Lynnette", "Meredith", "Jay", "Bernie",
					"Kenneth", "Harding", "Elissa", "Beth", "Vance", "Holden", "Careen", "Jackie",
					"Laurence", "Grover", "Megan", "Daniel", "Shelby", "Desmond", "Jason", "Patton",
					"Harvey", "Dylan", "Eleanor", "Grace", "Randall", "Carmen", "Lewis"
	]

	last_names = [ "Rennoll", "Layton", "Page", "Steffen", "Wilbur", "Clifford", "Ridge", "Norton",
					"Haden", "Smith", "Harris", "Bush", "Addison", "Warren", "Armstrong", "Radcliff",
					"Stern", "Jernigan", "Tucker", "Blackwood", "Gray", "Eaton", "Bissette", "Albert",
					"Rogers", "Tyrrell", "Randall", "Ramsey", "Parish", "Towner", "Granville"
	]

	domains = [ '/example.com', '/acme.com', '/contoso.com', '/anselus.test' ]
	rgen = secrets.SystemRandom()

	out = keycard.UserEntry()

	first_name = rgen.choice(first_names)
	last_name = rgen.choice(last_names)

	crvpair = SigningPair()
	crepair = KeyPair()
	pepair = KeyPair()

	out.set_fields({
		"Name" : ' '.join([first_name, last_name]),
		"Workspace-ID" : str(uuid.uuid4()),
		"User-ID" : first_name[0].lower() + last_name.lower(),
		"Domain" : rgen.choice(domains),
		'Contact-Request-Verification-Key':crvpair.get_public_key85(),
		'Contact-Request-Encryption-Key':crepair.get_public_key85(),
		'Public-Encryption-Key':pepair.get_public_key85()
	})

	# The validity of the signatures doesn't matter -- they just need to be different
	signing_key = keycard.EncodedString()
	signing_key.prefix = 'ED25519'
	signing_key.data = crvpair.get_private_key85()

	rv = out.sign(signing_key, "Custody")
	if rv.error():
		print(f'Custody signing failure: {str(rv)}')
		sys.exit(-1)
	rv = out.sign(signing_key, "Organization")
	if rv.error():
		print(f'Org signing failure: {str(rv)}')
		sys.exit(-1)
	rv = out.generate_hash('BLAKE2B-256')
	if rv.error():
		print(f'Hashing failure: {str(rv)}')
		sys.exit(-1)
	rv = out.sign(signing_key, "User")
	if rv.error():
		print(f'User signing failure: {str(rv)}')
		sys.exit(-1)
	return out


card = keycard.Keycard()
card.entries.append(create_org_entry())
for _ in range(10000):
	card.entries.append(create_random_user_entry())
card.save('sampledb.kc', True)
