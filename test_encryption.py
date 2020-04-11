import encryption

def test_b64encode():
	'''Test b64encode()'''
	# Encoding of '1234567890'
	testdata = b'MTIzNDU2Nzg5MA'
	assert encryption.b64encode(b'1234567890') == testdata, 'b64encode test failed'

def test_b64decode():
	'''Test b64decode()'''
	# Encoding of '1234567890'
	testdata = b'MTIzNDU2Nzg5MA'
	assert encryption.b64decode(testdata) == b'1234567890', 'b64decode test failed'
