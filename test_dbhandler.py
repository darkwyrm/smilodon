import os 

from dbhandler import Sqlite
import encryption

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


def test_remove_workspace():
	'''Tests remove_workspace()'''
	db = setup_db('remove_workspace')
	db.reset_db()

	# A lot of setup to test this method because it's supposed to erase ALL remnants of the 
	# specified Anselus address
	assert db.add_workspace('00000000-1111-2222-3333-444444444444','example.com',
		'$argon2id$v=19$m=65536,t=2,p=1$5PVRQQhCq+ntrG65xaU+FA'
		'$vLMKMzi4F7kE3xzK7NAXtfc2sdMERcWObSE/jfaVBZM',
		'argon2id'), "add new workspace fail"
	
	assert db.add_workspace('00000000-1111-2222-3333-555555555555','example.com',
		'$argon2id$v=19$m=65536,t=2,p=1$7YxSIvohj/+L4Zqx7ywl+g'
		'$B3sEts3Zs4+t2/J6fBX7LQEwRebtvDd+Ypl9K6y+Eoc',
		'argon2id'), 'add new workspace fail'
	
	# Folder mappings
	testpath = encryption.FolderMapping()
	testpath.MakeID()
	testpath.Set('00000000-1111-2222-3333-444444444444/example.com',
		'22222222-2222-2222-2222-222222222222', 'folder1', 'admin')
	out = db.add_folder(testpath)
	assert not out['error'], "Failed to add folder mapping 1"

	testpath.MakeID()
	testpath.Set('00000000-1111-2222-3333-444444444444/example.com',
		'22222222-2222-2222-2222-222222222222', 'folder2', 'admin')
	out = db.add_folder(testpath)
	assert not out['error'], "Failed to add folder mapping 2"

	# Device sessions
	assert db.add_device_session('00000000-1111-2222-3333-444444444444/example.com',
		'11111111-1111-1111-1111-111111111111',
		'----------==========++++++++++__________',
		'Test Device #1'), "Add new device session fail"

	assert db.add_device_session('00000000-1111-2222-3333-444444444444/example2.com',
		'22222222-2222-2222-2222-222222222222',
		'..........==========++++++++++__________',
		'Test Device #2'), "Add second new device session fail"

	# Encryption keys
	key = encryption.SecretKey('folder')
	out = db.add_key(key, '11111111-1111-1111-1111-111111111111')
	assert not out['error'], "Failed to add folder key"

	key = encryption.SecretKey('broadcast')
	out = db.add_key(key, '22222222-2222-2222-2222-222222222222')
	assert not out['error'], "Failed to add broadcast key"

	# Notes
	db.create_note('Note #1', 'default')
	db.create_note('Note #2', 'default')

	# Clean up EVERYTHING
	out = db.remove_workspace('00000000-1111-2222-3333-444444444444', 'example.com')
	assert not out['error'], 'remove workspace fail'


def test_remove_workspace_entry():
	'''Tests remove_workspace_entry()'''
	db = setup_db('remove_workspace_entry')
	db.reset_db()

	assert db.add_workspace('00000000-1111-2222-3333-444444444444','example.com',
		'$argon2id$v=19$m=65536,t=2,p=1$5PVRQQhCq+ntrG65xaU+FA'
		'$vLMKMzi4F7kE3xzK7NAXtfc2sdMERcWObSE/jfaVBZM',
		'argon2id'), "add new workspace fail"
	
	out = db.remove_workspace_entry('00000000-1111-2222-3333-444444444444', 'example.com')
	assert not out['error'], 'remove workspace fail'


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


def test_add_key():
	'''Tests add_key'''
	db = setup_db('add_key')
	db.reset_db()
	db.add_workspace('00000000-1111-2222-3333-444444444444','example.com',
		'12345678901234567890', 'testhash')
	
	key = encryption.KeyPair('identity')
	out = db.add_key(key,'00000000-1111-2222-3333-444444444444/example.com')
	assert not out['error'], "Failed to add asymmetric key"

	key = encryption.SecretKey('broadcast')
	out = db.add_key(key, '22222222-2222-2222-2222-222222222222')
	assert not out['error'], "Failed to add symmetric key"


def test_remove_key():
	'''Tests remove_key()'''
	db = setup_db('remove_key')
	db.reset_db()
	db.add_workspace('00000000-1111-2222-3333-444444444444','example.com',
		'12345678901234567890', 'testhash')
	
	key = encryption.SecretKey('broadcast')
	out = db.add_key(key, '22222222-2222-2222-2222-222222222222')
	assert not out['error'], "Failed to add symmetric key"
	
	out = db.remove_key(key.get_id())
	assert not out['error'], "Failed to remove key"


def test_get_key():
	'''Tests get_key()'''
	db = setup_db('get_key')
	db.reset_db()
	db.add_workspace('00000000-1111-2222-3333-444444444444','example.com',
		'12345678901234567890', 'testhash')
	
	key = encryption.KeyPair('identity')
	out = db.add_key(key,'00000000-1111-2222-3333-444444444444/example.com')
	assert not out['error'], "Failed to add asymmetric key"

	key2 = encryption.SecretKey('broadcast')
	out = db.add_key(key2, '22222222-2222-2222-2222-222222222222')
	assert not out['error'], "Failed to add symmetric key"

	out = db.get_key(key.get_id())
	assert not out['error'], "Failed to get asymmetric key"
	
	out = db.get_key(key2.get_id())
	assert not out['error'], "Failed to get symmetric key"


def test_add_folder():
	'''Tests add_folder()'''
	db = setup_db('add_folder')
	db.reset_db()

	testpath = encryption.FolderMapping()
	testpath.MakeID()
	testpath.Set('00000000-1111-2222-3333-444444444444/example.com',
		'22222222-2222-2222-2222-222222222222', 'foo bar baz', 'admin')
	out = db.add_folder(testpath)
	assert not out['error'], "Failed to add folder mapping"


def test_remove_folder():
	'''Tests remove_folder()'''
	db = setup_db('remove_folder')
	db.reset_db()

	testpath = encryption.FolderMapping()
	testpath.MakeID()
	testpath.Set('00000000-1111-2222-3333-444444444444/example.com',
		'22222222-2222-2222-2222-222222222222', 'foo bar baz', 'admin')
	out = db.add_folder(testpath)
	assert not out['error'], "Failed to add folder mapping"
	
	out = db.remove_folder(testpath.fid)
	assert not out['error'], "Failed to remove folder"


def test_get_folder():
	'''Tests get_folder()'''
	db = setup_db('get_folder')
	db.reset_db()

	testpath = encryption.FolderMapping()
	testpath.MakeID()
	testpath.Set('00000000-1111-2222-3333-444444444444/example.com',
		'22222222-2222-2222-2222-222222222222', 'foo bar baz', 'admin')
	out = db.add_folder(testpath)
	assert not out['error'], "Failed to add folder mapping"
	
	out = db.remove_folder(testpath.fid)
	assert not out['error'], "Failed to remove folder"
