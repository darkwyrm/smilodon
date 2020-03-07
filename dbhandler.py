import os
import platform
import sqlite3
import time
import uuid

import note

class DBHandler:
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
		sqlcmd = '''
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
		cursor = self.db.cursor()
		cursor.execute(sqlcmd)
		self.db.commit()
	
	def __init__(self):
		osname = platform.system().casefold()
		if osname == 'windows':
			self.dbfolder = os.path.join(os.getenv('LOCALAPPDATA'), 'anselus')
		else:
			self.dbfolder = os.path.join(os.getenv('HOME'), '.config','anselus')
		self.dbpath = os.path.join(self.dbfolder, 'storage.db')

		if not os.path.exists(self.dbfolder):
			os.mkdir(self.dbfolder)

		if os.path.exists(self.dbpath):
			self.db = sqlite3.connect(self.dbpath)
		else:
			self.reset_db()
	
	def create_note(self, title='New Note', notebook'default'):
		'''
		Creates a new note and returns a note structure
		'''
		id = ''

		# This should never iterate, but handle edge cases anyway
		while True:
			id = str(uuid.uuid4())
			cursor = self.db.cursor()
			cursor.execute("SELECT id FROM notes WHERE id=?", (id,))
			if cursor.fetchone() == None:
				break
		
		timestamp = time.strftime('%Y%m%d %H%M%S', time.gmtime())
		cursor.execute("INSERT INTO	notes(id,title,created,notebook) VALUES(?,?,?,?)",
			(id, title, timestamp, notebook))
		self.db.commit()

		outData = note.Note()
		outData.id = id
		outData.title = title
		outData.notebook = notebook
		outData.created = timestamp
		
		return outData
	
	def delete_note(self, id):
		'''
		Deletes a note with the specified ID. Returns a boolean success code.
		'''
		cursor = self.db.cursor()
		cursor.execute("SELECT id FROM notes WHERE id=?", (id,))
		results = cursor.fetchone()
		if not results or not results[0]:
			return False

		cursor.execute("DELETE FROM notes WHERE id=?", (id,))
		self.db.commit()
		return True

	def get_note_list(self):
		'''
		Gets a list of tuples containing the title, id, and notebook of all notes in the database.
		'''
		cursor = self.db.cursor()
		cursor.execute("SELECT title,id,notebook FROM notes")
		return cursor.fetchall()
		
	def get_note(self, id):
		'''
		Given an ID, returns a note structure or None if not found.
		'''
		cursor = self.db.cursor()
		cursor.execute("SELECT title,body FROM notes WHERE id=?", (id,))
		results = cursor.fetchone()
		if not results or not results[0]:
			return None
		
		out = note.Note()
		out.title = results[0]
		out.body = results[1]
		out.id = id
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