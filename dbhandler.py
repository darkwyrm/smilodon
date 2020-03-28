import os
import platform
import sqlite3
import time
import uuid

import items
import utils

class sqlite:
	'''Implements the database API for SQLite3-based storage.'''
	def reset_db(self):
		'''
		Reinitializes the database to empty.
		'''
		if os.path.exists(self.dbpath):
			try:
				os.remove(self.dbpath)
			except Exception as e:
				print('Unable to delete old database %s: %s' % (self.dbpath, e))
		
		self.db = sqlite3.connect(self.dbpath)
		cursor = self.db.cursor()

		sqlcmds = [ '''
			CREATE TABLE workspaces (
				"id" TEXT NOT NULL UNIQUE,
				"wid" TEXT NOT NULL UNIQUE,
				"friendly_address" TEXT,
				"domain" TEXT,
				"password" TEXT,
				"pwhashtype" TEXT,
				"type" TEXT
			);''', '''
			CREATE table "folders"(
				"id" TEXT NOT NULL UNIQUE,
				"address" TEXT NOT NULL,
				"fid" TEXT NOT NULL,
				"enc_key" TEXT NOT NULL,
				"path" TEXT NOT NULL,
				"permissions" TEXT NOT NULL
			);''', '''
			CREATE table "sessions"(
				"id" TEXT NOT NULL UNIQUE,
				"address" TEXT NOT NULL,
				"domain" TEXT NOT NULL,
				"devid" TEXT NOT NULL,
				"devname" TEXT,
				"session_str" TEXT NOT NULL
			);''', '''
			CREATE table "messages"(
				"id" TEXT NOT NULL UNIQUE,
				"from"  TEXT NOT NULL,
				"address" TEXT NOT NULL,
				"cc"  TEXT,
				"bcc" TEXT,
				"date" TEXT NOT NULL,
				"thread_id" TEXT NOT NULL,
				"subject" TEXT,
				"body" TEXT,
				"attachments" TEXT
			);''', '''
			CREATE TABLE "contacts" (
				"id"	TEXT NOT NULL,
				"sensitivity"	TEXT NOT NULL,
				"source"	TEXT NOT NULL,
				"fieldname"	TEXT,
				"fieldvalue"	TEXT
			);''', '''
			CREATE TABLE "notes" (
				"id"	TEXT NOT NULL UNIQUE,
				"address" TEXT,
				"title"	TEXT,
				"body"	TEXT,
				"notebook"	TEXT,
				"tags"	TEXT,
				"created"	TEXT NOT NULL,
				"updated"	TEXT,
				"attachments"	TEXT
			);''', '''
			CREATE TABLE "files" (
				"id"	TEXT NOT NULL UNIQUE,
				"name"	TEXT NOT NULL,
				"type"	TEXT NOT NULL,
				"path"	TEXT NOT NULL
			);'''
		]

		for sqlcmd in sqlcmds:
			cursor = self.db.cursor()
			cursor.execute(sqlcmd)
		self.db.commit()
	
	def __init__(self):
		osname = platform.system().casefold()
		if osname == 'windows':
			self.dbfolder = os.path.join(os.getenv('LOCALAPPDATA'), 'anselus')
		else:
			self.dbfolder = os.path.join(os.getenv('HOME'), '.config','anselus')
		
		if not os.path.exists(self.dbfolder):
			os.mkdir(self.dbfolder)

		self.profile_id = ''
		self.db = None
		self.dbpath = ''
	
	def connect(self, profile_id):
		'''Connects to the user data storage database'''
		self.dbpath = os.path.join(self.dbfolder, profile_id, 'storage.db')

		if os.path.exists(self.dbpath):
			self.db = sqlite3.connect(self.dbpath)
		else:
			self.reset_db()
		self.profile_id = profile_id

	def disconnect(self):
		'''Closes the connection to the user data storage database'''
		self.db.close()

	def add_workspace(self, wid, domain, pwhash, pwhashtype):
		'''Adds a workspace to the storage database'''

		cursor = self.db.cursor()
		cursor.execute("SELECT wid FROM workspaces WHERE wid=?", (wid,))
		results = cursor.fetchone()
		if results or results[0]:
			return False
		
		cursor.execute('''INSERT INTO workspaces(wid,domain,password,pwhashtype,type)
			VALUES(?,?,?,?,?)''', wid, domain, pwhash, pwhashtype, "single")
		self.db.commit()
		return True

	def add_device_session(self, address, devid, session_str, devname=None):
		'''Adds a device to a workspace'''

		# Normally we don't validate the input, relying on the caller to ensure valid data because
		# in most cases, bad data just corrupts the database integrity, not crash the program.
		# We have to do some here to ensure there isn't a crash when the address is split.
		parts = address.split('/')
		if len(parts) != 2 or \
			not parts[0] or \
			not parts[1] or \
			utils.validate_uuid(parts[0]):
			return False

		# address has to be valid and existing already
		cursor = self.db.cursor()
		cursor.execute("SELECT wid FROM workspaces WHERE wid=?", (parts[0],))
		results = cursor.fetchone()
		if not results or not results[0]:
			return False
		
		# Can't have a session on the server already
		cursor.execute("SELECT address FROM sessions WHERE address=?", (address,))
		results = cursor.fetchone()
		if not results or not results[0]:
			return False
		
		cursor = self.db.cursor()
		if devname:
			cursor.execute('''INSERT INTO sessions(address,devid,session_str,devname) VALUES(?,?,?,?)''',
				(address, devid, session_str, devname))
		else:
			cursor.execute('''INSERT INTO sessions(address,devid,session_str) VALUES(?,?,?)''',
				(address, devid, session_str))
		self.db.commit()
		return True

	def update_device_session(self, devid, session_str):
		'''Updates the session id for a device'''

		# Device ID can't already exist
		cursor = self.db.cursor()
		cursor.execute("SELECT devid FROM sessions WHERE devid=?", (devid,))
		results = cursor.fetchone()
		if not results or not results[0]:
			return False
		
		cursor = self.db.cursor()
		cursor.execute('''UPDATE sessions SET session_str=? WHERE devid=?''', (session_str, devid))
		self.db.commit()
		return True

	def remove_device_session(self, devid):
		'''
		Removes an authorized device from the workspace. Returns a boolean success code.
		'''
		cursor = self.db.cursor()
		cursor.execute("SELECT id FROM notes WHERE id=?", (devid,))
		results = cursor.fetchone()
		if not results or not results[0]:
			return False

		cursor.execute("DELETE FROM notes WHERE id=?", (devid,))
		self.db.commit()
		return True

	def get_device_session(self, address):
		'''The device can have sessions on multiple servers, but it can only have one on each 
		server. Return the session string for the specified address or None if not found.'''
		cursor = self.db.cursor()
		cursor.execute("SELECT session_str FROM sessions WHERE address=?", (address,))
		results = cursor.fetchone()
		if not results or not results[0]:
			return None
		
		return results[0]

	def create_note(self, title='New Note', notebook='default'):
		'''
		Creates a new note and returns a note structure
		'''
		item_id = ''

		# This should never iterate, but handle edge cases anyway
		while True:
			item_id = str(uuid.uuid4())
			cursor = self.db.cursor()
			cursor.execute("SELECT id FROM notes WHERE id=?", (id,))
			if cursor.fetchone() is None:
				break
		
		timestamp = time.strftime('%Y%m%d %H%M%S', time.gmtime())
		cursor.execute("INSERT INTO	notes(id,title,created,notebook) VALUES(?,?,?,?)",
			(item_id, title, timestamp, notebook))
		self.db.commit()

		outData = items.Note()
		outData.id = item_id
		outData.title = title
		outData.notebook = notebook
		outData.created = timestamp
		
		return outData
	
	def delete_note(self, item_id):
		'''
		Deletes a note with the specified ID. Returns a boolean success code.
		'''
		cursor = self.db.cursor()
		cursor.execute("SELECT id FROM notes WHERE id=?", (item_id,))
		results = cursor.fetchone()
		if not results or not results[0]:
			return False

		cursor.execute("DELETE FROM notes WHERE id=?", (item_id,))
		self.db.commit()
		return True

	def get_note_list(self):
		'''
		Gets a list of tuples containing the title, id, and notebook of all notes in the database.
		'''
		cursor = self.db.cursor()
		cursor.execute("SELECT title,id,notebook FROM notes")
		return cursor.fetchall()
		
	def get_note(self, item_id):
		'''
		Given an ID, returns a note structure or None if not found.
		'''
		cursor = self.db.cursor()
		cursor.execute("SELECT title,body FROM notes WHERE id=?", (item_id,))
		results = cursor.fetchone()
		if not results or not results[0]:
			return None
		
		out = items.Note()
		out.title = results[0]
		out.body = results[1]
		out.id = item_id
		return out
	
	def update_note(self, n):
		'''
		Given a note structure, update a note in the database. A boolean success value is 
		returned.
		'''
		cursor = self.db.cursor()
		cursor.execute("SELECT id FROM notes WHERE id=?", (n.id,))
		results = cursor.fetchone()
		if not results or not results[0]:
			return False

		sqlcmd='''
		UPDATE notes
		SET title=?,
			body=?,
			updated=?,
			tags=?
		WHERE id=?
		'''
		timestamp = time.strftime('%Y%m%d %H%M%S', time.gmtime())
		tag_string = ','.join(n.tags)	
		cursor.execute(sqlcmd, (n.title,n.body,timestamp,tag_string,n.id))
		self.db.commit()
		return True

	def get_credentials(self, wid, domain):
		'''Returns the stored login credentials for the requested wid'''
		cursor = self.db.cursor()
		cursor.execute('''SELECT FROM workspaces(password,pwhashtype) WHERE wid=? AND domain=?''',
			(wid,domain))
		results = cursor.fetchone()
		if not results or not results[0]:
			return dict()
		return { 'password':results[0], 'pwhashtype':results[1] }

	def set_credentials(self, wid, domain, password, pwhashtype):
		'''Sets the password and hash type for the specified workspace. A boolean success 
		value is returned.'''
		cursor = self.db.cursor()
		cursor.execute("SELECT wid FROM workspaces WHERE wid=? AND domain=?", (wid,domain))
		results = cursor.fetchone()
		if not results or not results[0]:
			return False

		cursor = self.db.cursor()
		cursor.execute("UPDATE workspaces SET password=?,pwhashtype=? WHERE wid=? AND domain=?",
			(password, pwhashtype, wid, domain))
		self.db.commit()
		return True
