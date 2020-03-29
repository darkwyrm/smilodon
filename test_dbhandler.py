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


def test_add_device_session():
	'''Tests add_device_session()'''
	db = setup_db('add_device_session')
	db.reset_db()
	db.add_workspace('00000000-1111-2222-3333-444444444444','example.com',
		'$argon2id$v=19$m=65536,t=2,p=1$5PVRQQhCq+ntrG65xaU+FA'
		'$vLMKMzi4F7kE3xzK7NAXtfc2sdMERcWObSE/jfaVBZM',
		'argon2id'
	)
	
	assert db.add_device_session('00000000-1111-2222-3333-444444444444/example.com',
		'11111111-1111-1111-1111-111111111111',
		'----------==========++++++++++__________',
		'Test Device #1'), "Add new device session fail"
	
	assert not db.add_device_session('00000000-1111-2222-3333-555555555555/example.com',
		'11111111-1111-1111-1111-111111111111',
		'----------==========++++++++++__________',
		'Bad device'), "Failed to detect adding device to nonexistent workspace"
	
	assert not db.add_device_session('00000000-1111-2222-3333-444444444444/example.com',
		'11111111-1111-1111-1111-111111111111',
		'----------==========++++++++++__________',
		'Duplicate device'), "Failed to detect duplicate device session"
	
	db.add_workspace('00000000-1111-2222-3333-555555555555','example.com',
		'$argon2id$v=19$m=65536,t=2,p=1$5PVRQQhCq+ntrG65xaU+FA'
		'$vLMKMzi4F7kE3xzK7NAXtfc2sdMERcWObSE/jfaVBZM',
		'argon2id'
	)
	assert db.add_device_session('00000000-1111-2222-3333-555555555555/example.com',
		'22222222-2222-2222-2222-222222222222',
		'----------==========++++++++++__________'), "Failed to add unnamed second device"


def test_update_device_session():
	'''Tests update_device_session()'''
	db = setup_db('update_device_session')
	db.reset_db()
	db.add_workspace('00000000-1111-2222-3333-444444444444','example.com',
		'$argon2id$v=19$m=65536,t=2,p=1$5PVRQQhCq+ntrG65xaU+FA'
		'$vLMKMzi4F7kE3xzK7NAXtfc2sdMERcWObSE/jfaVBZM',
		'argon2id'
	)
	
	db.add_device_session('00000000-1111-2222-3333-444444444444/example.com',
		'11111111-1111-1111-1111-111111111111',
		'----------==========++++++++++__________',
		'Test Device #1')
	
	assert db.update_device_session('11111111-1111-1111-1111-111111111111',
		'||||||||||==========++++++++++__________'), "Failed to update device session string"
	
	assert not db.update_device_session('22222222-1111-1111-1111-111111111111',
		'||||||||||==========++++++++++__________'), "Failed to detect nonexistent device"


def test_remove_device_session():
	'''Tests remove_device_session()'''
	db = setup_db('remove_device_session')
	db.reset_db()
	db.add_workspace('00000000-1111-2222-3333-444444444444','example.com',
		'$argon2id$v=19$m=65536,t=2,p=1$5PVRQQhCq+ntrG65xaU+FA'
		'$vLMKMzi4F7kE3xzK7NAXtfc2sdMERcWObSE/jfaVBZM',
		'argon2id'
	)
	
	db.add_device_session('00000000-1111-2222-3333-444444444444/example.com',
		'11111111-1111-1111-1111-111111111111',
		'----------==========++++++++++__________',
		'Test Device #1')
	
	assert db.remove_device_session('11111111-1111-1111-1111-111111111111'), \
		"Failed to remove device session string"


def test_get_session_string():
	'''Tests get_session_string()'''
	db = setup_db('get_session_string')
	db.reset_db()
	db.add_workspace('00000000-1111-2222-3333-444444444444','example.com',
		'$argon2id$v=19$m=65536,t=2,p=1$5PVRQQhCq+ntrG65xaU+FA'
		'$vLMKMzi4F7kE3xzK7NAXtfc2sdMERcWObSE/jfaVBZM',
		'argon2id'
	)
	
	db.add_device_session('00000000-1111-2222-3333-444444444444/example.com',
		'11111111-1111-1111-1111-111111111111',
		'----------==========++++++++++__________',
		'Test Device #1')
	
	assert db.get_session_string('00000000-1111-2222-3333-444444444444/example.com'), \
		"Failed to get device session string"
	
	assert not db.get_session_string('00000000-1111-2222-3333-555555555555/example.com'), \
		"Failed to detect nonexistent device session"
	

def test_get_credentials():
	'''Tests get_credentials()'''
	db = setup_db('get_credentials')
	db.reset_db()
	db.add_workspace('00000000-1111-2222-3333-444444444444','example.com',
		'12345678901234567890', 'testhash')
	
	out = db.get_credentials('00000000-1111-2222-3333-444444444444','example.com')
	assert not out['error'], "Failed to get credentials"
	assert out['password'] == '12345678901234567890', \
		"Received password hash did not match input"
	assert out['pwhashtype'] == 'testhash', "Received hash type did not match input"
	assert db.get_credentials('00000000-1111-2222-3333-555555555555','example.com')['error'], \
		'Failed to detect nonexistent workspace'


def test_set_credentials():
	'''Tests set_credentials()'''
	db = setup_db('set_credentials')
	db.reset_db()
	db.add_workspace('00000000-1111-2222-3333-444444444444','example.com',
		'12345678901234567890', 'testhash')
	
	assert db.set_credentials('00000000-1111-2222-3333-444444444444','example.com',
		'09876543210987654321', 'testhash'), "Failed to set credentials"
	
	out = db.get_credentials('00000000-1111-2222-3333-444444444444','example.com')
	assert not out['error'], "Failed to get credentials"
	assert out['password'] == '09876543210987654321', \
		"Received password hash did not match input"
	assert out['pwhashtype'] == 'testhash', "Received hash type did not match input"

	assert not db.set_credentials('00000000-1111-2222-3333-555555555555','example.com',
		'09876543210987654321', 'testhash'), 'Failed to detect nonexistent workspace'
