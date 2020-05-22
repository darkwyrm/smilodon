'''DBLayer implements a simple database interaction layer for other classes to interact with using 
the Singleton pattern. Currently only SQLite3 is implemented, but internals are designed to make 
adding other engines easy.
'''

# pylint: disable=unused-argument,no-self-use

import pathlib
import sqlite3

from retval import RetVal, BadParameterValue, FilesystemError

DBConnectionFailed = 'DBConnectionFailed'

class Database:
	'''The Database class provides the API to interact with the requested database type'''
	
	def connect(self, args):
		'''connect() takes a dictionary containing the necessary parameters needed to connect to 
		the particular database instance desired and returns a RetVal upon completion which 
		indicates connection state. More details can be found in the docstring for the subclass' 
		connect() method.
		'''
		return RetVal()

	def disconnect(self):
		'''disconnect() closes the connection to the user data storage database.'''
		return RetVal()
	
	def create_table(self, name, fields):
		'''create_table() creates a database table. 'name' is the name of the table and 'fields' 
		is a list of 2-element tuples containing the field name and the field parameters, like 
		type and any qualifiers, e.g. [ ('wid','TEXT NOT NULL'), ('fid', 'TEXT NOT NULL UNIQUE')]. 
		'''
		return RetVal()

	def delete_table(self, name):
		'''delete_table() deletes the named table.'''
		return RetVal()
	
	def empty_table(self, name):
		'''empty_table() deletes all records from the named table.'''
		return RetVal()
	
	def insert_row(self, name, fields):
		'''insert_row() adds a record to the named table. 'name' is the name of the table and 
		'fields' is a list of 2-element tuples containing the field name and its value.
		'''
		return RetVal()
	
	def update_rows(self, name, fields, condition):	
		'''update_rows() updates records in the named table. 'name' is the name of the table,  
		'fields' is a list list of 2-element tuples containing the field name and its value, and 
		'condition' is an expression. 
		'''
		return RetVal()
	
	def delete_rows(self, name, fields, condition):	
		'''delete_rows() deletes records in the named table. 'name' is the name of the table,  
		'fields' is a list of containing the field name(s), and 'condition' is an expression. 
		'''
		return RetVal()

	def select_rows(self, name, fields, condition):	
		'''select_rows() returns records from the named table. 'name' is the name of the table,  
		'fields' is a list of containing the field name(s), and 'condition' is an expression. 
		'''
		return RetVal()


class SQLiteDatabase(Database):
	'''SQLiteDatabase implements the Database API using SQLite for storage'''
	def __init__(self):
		self.dbpath = ''
		self.db = None

	def connect(self, args):
		'''Connects to a SQLite database.

		Parameters:
		'path': string, full path to the desired database location, e.g. /home/foo/bar/baz.db. The 
			path format is OS-dependent.
		
		Returns:
		error(): success/failure of the connection
		'''

		if 'path' not in args or not args['path']:
			return RetVal(BadParameterValue)
		
		p = pathlib.Path(args['path']).absolute()
		self.dbpath = str(p)
		if not p.parent().exists():
			try:
				p.parent().mkdir(parents=True, exist_ok=True)
			except Exception as e:
				error = RetVal(FilesystemError)
				error.set_value("message", str(e))
				return error
		try:
			self.db = sqlite3.connect(self.dbpath)
		except Exception as e:
			error = RetVal(DBConnectionFailed)
			error.set_value("message", str(e))
			return error
		
		return RetVal()

	def disconnect(self):
		'''Closes the connection to the SQLite database instance'''
		self.db.close()
		return RetVal()


# The global interaction object.
instance = None
__DBTYPE__ = ''

def instantiate(dbtype):
	'''Returns an instance of the database connection requested. Currently only 'sqlite' is 
	supported.
	'''
	if not dbtype or dbtype not in [ 'sqlite' ]:
		raise ValueError
	
	global __DBTYPE__	# pylint: disable=global-statement
	if __DBTYPE__:
		return
	
	if dbtype == 'sqlite':
		__DBTYPE__ = dbtype
		global instance	# pylint: disable=global-statement
		instance = SQLiteDatabase()
