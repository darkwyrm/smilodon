'''This module encapsulates authentication, credentials, and session management'''

import base64

import encryption
import utils

def get_credentials(db, wid, domain):
	'''Returns the stored login credentials for the requested wid'''
	cursor = db.cursor()
	cursor.execute('''SELECT password,pwhashtype FROM workspaces WHERE wid=? AND domain=?''',
		(wid,domain))
	results = cursor.fetchone()
	if not results or not results[0]:
		return { 'error' : 'Workspace not found' }
	
	out = encryption.Password()
	status = out.Assign(results[0])
	status['password'] = out
	return status


def set_credentials(db, wid, domain, pw):
	'''Sets the password and hash type for the specified workspace. A boolean success 
	value is returned.'''
	cursor = db.cursor()
	cursor.execute("SELECT wid FROM workspaces WHERE wid=? AND domain=?", (wid,domain))
	results = cursor.fetchone()
	if not results or not results[0]:
		return False

	cursor = db.cursor()
	cursor.execute("UPDATE workspaces SET password=?,pwhashtype=? WHERE wid=? AND domain=?",
		(pw.hashstring, pw.hashtype, wid, domain))
	db.commit()
	return True


def add_device_session(db, address, devid, session_str, devname=None):
	'''Adds a device to a workspace'''

	# Normally we don't validate the input, relying on the caller to ensure valid data because
	# in most cases, bad data just corrupts the database integrity, not crash the program.
	# We have to do some here to ensure there isn't a crash when the address is split.
	parts = utils.split_address(address)
	if parts['error']:
		return False

	# address has to be valid and existing already
	cursor = db.cursor()
	cursor.execute("SELECT wid FROM workspaces WHERE wid=?", (parts['wid'],))
	results = cursor.fetchone()
	if not results or not results[0]:
		return False

	# Can't have a session on the server already
	cursor.execute("SELECT address FROM sessions WHERE address=?", (address,))
	results = cursor.fetchone()
	if results:
		return False
	
	cursor = db.cursor()
	if devname:
		cursor.execute('''INSERT INTO sessions(address,devid,session_str,devname) VALUES(?,?,?,?)''',
			(address, devid, session_str, devname))
	else:
		cursor.execute('''INSERT INTO sessions(address,devid,session_str) VALUES(?,?,?)''',
			(address, devid, session_str))
	db.commit()
	return True


def update_device_session(db, devid, session_str):
	'''Updates the session id for a device'''

	cursor = db.cursor()
	cursor.execute("SELECT devid FROM sessions WHERE devid=?", (devid,))
	results = cursor.fetchone()
	if not results or not results[0]:
		return False
	
	cursor = db.cursor()
	cursor.execute('''UPDATE sessions SET session_str=? WHERE devid=?''', (session_str, devid))
	db.commit()
	return True


def remove_device_session(db, devid):
	'''
	Removes an authorized device from the workspace. Returns a boolean success code.
	'''
	cursor = db.cursor()
	cursor.execute("SELECT devid FROM sessions WHERE devid=?", (devid,))
	results = cursor.fetchone()
	if not results or not results[0]:
		return False

	cursor.execute("DELETE FROM sessions WHERE devid=?", (devid,))
	db.commit()
	return True


def get_session_string(db, address):
	'''The device can have sessions on multiple servers, but it can only have one on each 
	server. Return the session string for the specified address or None if not found.'''
	cursor = db.cursor()
	cursor.execute("SELECT session_str FROM sessions WHERE address=?", (address,))
	results = cursor.fetchone()
	if not results or not results[0]:
		return None
	
	return results[0]


def add_key(db, key, address):
	'''Adds an encryption key to a workspace.
	Parameters:
	key: EncryptionKey from encryption module
	address: full Anselus address, i.e. wid + domain
	
	Returns:
	error : string
	'''

	cursor = db.cursor()
	cursor.execute("SELECT keyid FROM keys WHERE keyid=?", (key.get_id(),))
	results = cursor.fetchone()
	if results:
		return { 'error' : 'Key exists'}
	
	if key.get_type() == 'symmetric':
		cursor.execute('''INSERT INTO keys(keyid,address,type,category,private,algorithm)
			VALUES(?,?,?,?,?,?)''', (key.get_id(), address, key.get_type(), key.get_category(),
				key.get_key85(), key.get_encryption_type()))
		db.commit()
		return { 'error' : '' }
	
	if key.get_type() == 'asymmetric':
		cursor.execute('''INSERT INTO keys(keyid,address,type,category,private,public,algorithm)
			VALUES(?,?,?,?,?,?,?)''', (key.get_id(), address, key.get_type(), key.get_category(),
				key.get_private_key85(), key.get_public_key85(), key.get_encryption_type()))
		db.commit()
		return { 'error' : '' }
	
	return { 'error' : "Key must be 'asymmetric' or 'symmetric'" }

def remove_key(db, keyid):
	'''Deletes an encryption key from a workspace.
	Parameters:
	keyid : uuid

	Returns:
	error : string
	'''
	cursor = db.cursor()
	cursor.execute("SELECT keyid FROM keys WHERE keyid=?", (keyid,))
	results = cursor.fetchone()
	if not results or not results[0]:
		return { 'error' : 'Key does not exist' }

	cursor.execute("DELETE FROM keys WHERE keyid=?", (keyid,))
	db.commit()
	return { 'error' : '' }

def get_key(db, keyid):
	'''Gets the specified key.
	Parameters:
	keyid : uuid

	Returns:
	'error' : string
	'key' : EncryptionKey object
	'''

	cursor = db.cursor()
	cursor.execute('''
		SELECT address,type,category,private,public,algorithm
		FROM keys WHERE keyid=?''',
		(keyid,))
	results = cursor.fetchone()
	if not results or not results[0]:
		return { 'error' : 'Key not found' }
	
	if results[1] == 'asymmetric':
		public = base64.b85decode(results[4])
		private = base64.b85decode(results[3])
		key = encryption.KeyPair(results[2],	public,	private, results[5])
		return { 'error' : '', 'key' : key }
	
	if results[1] == 'symmetric':
		private = base64.b85decode(results[3])
		key = encryption.SecretKey(results[2], private, results[5])
		return { 'error' : '', 'key' : key }
	
	return { 'error' : "Bad key type '%s'" % results[1] } 
