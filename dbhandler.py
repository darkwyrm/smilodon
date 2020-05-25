'''This module provides an abstract interface to a database. Currently only supports SQLite3'''
import time
import uuid

import encryption
import items

class Sqlite:
	'''Formerly a class to abstract database access. It has been deprecated. Remaining code will 
	be moved out into other areas at a future time. DO NOT USE.'''
	def __init__(self):
		self.db = None

	def add_workspace(self, wid, domain, pw):
		'''Adds a workspace to the storage database'''

		cursor = self.db.cursor()
		cursor.execute("SELECT wid FROM workspaces WHERE wid=?", (wid,))
		results = cursor.fetchone()
		if results:
			return False
		
		cursor.execute('''INSERT INTO workspaces(wid,domain,password,pwhashtype,type)
			VALUES(?,?,?,?,?)''', (wid, domain, pw.hashstring, pw.hashtype, "single"))
		self.db.commit()
		return True

	def remove_workspace(self, wid, domain):
		'''
		Removes ALL DATA associated with a workspace. Don't call this unless you mean to erase
		all evidence that a particular workspace ever existed.
		'''
		cursor = self.db.cursor()
		cursor.execute("SELECT wid FROM workspaces WHERE wid=? AND domain=?", (wid,domain))
		results = cursor.fetchone()
		if not results or not results[0]:
			return { 'error' : 'Workspace not found'}
		
		address = '/'.join([wid,domain])
		cursor.execute("DELETE FROM workspaces WHERE wid=? AND domain=?", (wid,domain))
		cursor.execute("DELETE FROM folders WHERE address=?", (address,))
		cursor.execute("DELETE FROM sessions WHERE address=?", (address,))
		cursor.execute("DELETE FROM keys WHERE address=?", (address,))
		cursor.execute("DELETE FROM messages WHERE address=?", (address,))
		cursor.execute("DELETE FROM notes WHERE address=?", (address,))
		self.db.commit()
		return { 'error' : '' }
	
	def remove_workspace_entry(self, wid, domain):
		'''
		Removes a workspace from the storage database.
		NOTE: this only removes the workspace entry itself. It does not remove keys, sessions,
		or other associated data.
		'''
		cursor = self.db.cursor()
		cursor.execute("SELECT wid FROM workspaces WHERE wid=? AND domain=?", (wid,domain))
		results = cursor.fetchone()
		if not results or not results[0]:
			return { 'error' : 'Workspace not found'}
		
		cursor.execute("DELETE FROM workspaces WHERE wid=? AND domain=?", (wid,domain))
		self.db.commit()
		return { 'error' : '' }
		
	def create_note(self, title='New Note', notebook='default'):
		'''
		Creates a new note and returns a note structure
		'''
		item_id = ''

		# This should never iterate, but handle edge cases anyway
		while True:
			item_id = str(uuid.uuid4())
			cursor = self.db.cursor()
			cursor.execute("SELECT id FROM notes WHERE id=?", (item_id,))
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

	def add_folder(self, folder):
		'''
		Adds a mapping of a folder ID to a specific path in the workspace.
		Parameters:
		folder : FolderMapping object
		'''
		cursor = self.db.cursor()
		cursor.execute("SELECT fid FROM folders WHERE fid=?", (folder.fid,))
		results = cursor.fetchone()
		if results:
			return { 'error' : 'Key exists'}
		
		cursor.execute('''INSERT INTO folders(fid,address,keyid,path,permissions)
			VALUES(?,?,?,?,?)''', (folder.fid, folder.address, folder.keyid, folder.path,
				folder.permissions))
		self.db.commit()

		return { 'error' : '' }

	def remove_folder(self, fid):
		'''Deletes a folder mapping.
		Parameters:
		fid : uuid

		Returns:
		error : string
		'''
		cursor = self.db.cursor()
		cursor.execute("SELECT fid FROM folders WHERE fid=?", (fid,))
		results = cursor.fetchone()
		if not results or not results[0]:
			return { 'error' : 'Folder does not exist' }

		cursor.execute("DELETE FROM folders WHERE fid=?", (fid,))
		self.db.commit()
		return { 'error' : '' }
	
	def get_folder(self, fid):
		'''Gets the specified folder.
		Parameters:
		fid : uuid

		Returns:
		'error' : string
		'folder' : FolderMapping object
		'''

		cursor = self.db.cursor()
		cursor.execute('''
			SELECT address,keyid,path,permissions FROM folders WHERE fid=?''', (fid,))
		results = cursor.fetchone()
		if not results or not results[0]:
			return { 'error' : 'Key not found' }
		
		folder = encryption.FolderMapping()
		folder.fid = fid
		folder.Set(results[0], results[1], results[2], results[3])
		
		return { 'error' : '', 'folder' : folder } 
