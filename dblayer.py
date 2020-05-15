'''DBLayer implements a simple database interaction layer for other classes to interact with using 
the Singleton pattern. Currently only SQLite3 is implemented, but internals are designed to make 
adding other engines easy.
'''

import os
import platform
import sqlite3

from retval import RetVal, BadParameterValue

class Database:
	'''The Database class provides the API to interact with the requested database type'''
	
	def connect(self, args):
		'''connect() takes a dictionary containing the necessary parameters needed to connect to 
		the particular database instance desired and returns a RetVal upon completion which 
		indicates connection state. More details can be found in the docstring for the subclass' 
		connect() method.
		'''
		return RetVal()


class SQLiteDatabase(Database):
	'''SQLiteDatabase implements the Database API using SQLite for storage'''
	def __init__(self):
		self.dbpath = ''

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
		
		# TODO: ensure absolute path,
		self.dbpath = args['path']

		# TODO: ensure db folder exists

		# osname = platform.system().casefold()
		# if osname == 'windows':
		# 	self.dbfolder = os.path.join(os.getenv('LOCALAPPDATA'), 'anselus')
		# else:
		# 	self.dbfolder = os.path.join(os.getenv('HOME'), '.config','anselus')
		
		# if not os.path.exists(self.dbfolder):
		# 	os.mkdir(self.dbfolder)

		# self.profile_id = ''
		# self.db = None
		# self.dbpath = ''


# The global interaction object.
instance = None
__DBTYPE__ = ''

def instantiate(dbtype):
	if not dbtype or dbtype not in [ 'sqlite' ]:
		raise ValueError
	
	global __DBTYPE__
	if __DBTYPE__:
		return
	
	if dbtype == 'sqlite':
		__DBTYPE__ = dbtype
		global instance
		instance = SQLiteDatabase()
