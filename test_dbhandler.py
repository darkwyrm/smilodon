import os 

from dbhandler import Sqlite

def setup_db(name):
	'''Creates a new test database'''
	testdb_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)),'testfiles')
	if not os.path.exists(testdb_folder):
		os.mkdir(testdb_folder)

	testdb_path = os.path.join(testdb_folder, name)
	return Sqlite(testdb_path)


def test_connect():
	'''Tests connect()'''
	db = setup_db('connect')
	db.connect('')
	assert db.db, "connect() fail"


def test_add_workspace():
	'''Tests add_workspace()'''
	db = setup_db('add_workspace')
	db.reset_db()

	assert db.add_workspace('00000000-1111-2222-3333-444444444444','example.com',
		'$argon2id$v=19$m=65536,t=2,p=1$5PVRQQhCq+ntrG65xaU+FA'
		'$vLMKMzi4F7kE3xzK7NAXtfc2sdMERcWObSE/jfaVBZM',
		'argon2id'), "add new workspace fail"
	
	assert not db.add_workspace('00000000-1111-2222-3333-444444444444','example.com',
		'$argon2id$v=19$m=65536,t=2,p=1$5PVRQQhCq+ntrG65xaU+FA'
		'$vLMKMzi4F7kE3xzK7NAXtfc2sdMERcWObSE/jfaVBZM',
		'argon2id'), "Detect duplicate workspace fail"
