import os
import platform
import sqlite3
import time
import uuid

import items

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
				"password" TEXT,
				"type" TEXT
			);''', '''
			CREATE table "folders"(
				"id" TEXT NOT NULL UNIQUE,
				"wid" TEXT NOT NULL UNIQUE,
				"enc_key" TEXT,
				"path" TEXT
			);''', '''
			CREATE TABLE "notes" (
				"id"	TEXT NOT NULL UNIQUE,
				"title"	TEXT,
				"body"	TEXT,
				"notebook"	TEXT,
				"tags"	TEXT,
				"created"	TEXT NOT NULL,
				"updated"	TEXT,
				"attachments"	TEXT
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
	
	def connect(self):
		'''Connects to the user data storage database'''
		self.dbpath = os.path.join(self.dbfolder, self.profile_id, 'storage.db')

		if os.path.exists(self.dbpath):
			self.db = sqlite3.connect(self.dbpath)
		else:
			self.reset_db()

	def disconnect(self):
		'''Closes the connection to the user data storage database'''
		self.db.close()

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
