'''This module tests the KeyCard class'''
import datetime
import os
import shutil
import time

#import nacl.signing

import keycard_entry as keycard

# Pylint doesn't detect the use of this import:
from retval import RetVal # pylint: disable=unused-import

def setup_test(name):
	'''Creates a test folder hierarchy'''
	test_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)),'testfiles')
	if not os.path.exists(test_folder):
		os.mkdir(test_folder)

	test_folder = os.path.join(test_folder, name)
	while os.path.exists(test_folder):
		try:
			shutil.rmtree(test_folder)
		except:
			print("Waiting a second for test folder to unlock")
			time.sleep(1.0)
	os.mkdir(test_folder)
	return test_folder

def test_set_field():
	'''Tests setfield'''
	card = keycard.EntryBase()
	card.set_field('Name','Corbin Smith')
	assert card.fields['Name'] == 'Corbin Smith', "set_field() didn't work"


def test_set_fields():
	'''Tests setfields'''
	card = keycard.EntryBase()
	card.set_fields({
		'Name':'Example, Inc.',
		'Contact-Admin':'admin/example.com',
		'noncompliant-field':'foobar2000'
	})

	assert 'Name' in card.fields and 'Contact-Admin' in card.fields and \
			'noncompliant-field' in card.fields, "set_fields() didn't work right"


# TODO: Implement test_is_compliant() once subclasses are implemented
def test_is_compliant():
	'''Tests compliance testing for the base class and its subclasses'''
	
	basecard = keycard.EntryBase()
	status = basecard.is_compliant()
	assert status.error(), "EntryBase met compliance and shouldn't"


def test_set():
	'''Tests set()'''

	# Note that the Type field is not set so that set() doesn't reject the data because it doesn't
	# match the entry type
	indata = \
		b'Name:Acme, Inc.\r\n' \
		b'Contact-Admin:admin/acme.com\r\n' \
		b'Language:en\r\n' \
		b'Primary-Signing-Key:ED25519:&JEq)5Ktu@jfM+Sa@+1GU6E&Ct2*<2ZYXh#l0FxP\r\n' \
		b'Encryption-Key:CURVE25519:^fI7bdC(IEwC#(nG8Em-;nx98TcH<TnfvajjjDV@\r\n' \
		b'Time-To-Live:14\r\n' \
		b'Expires:730\r\n' \
		b'Organization-Signature:x3)dYq@S0rd1Rfbie*J7kF{fkxQ=J=A)OoO1WGx97o-utWtfbwyn-$(js'\
			b'_n^d6uTZY7p{gd60=rPZ|;m\r\n'

	basecard = keycard.EntryBase()
	status = basecard.set(indata)
	assert not status.error(), "EntryBase.set() failed"
	assert basecard.signatures['Organization'] == 'x3)dYq@S0rd1Rfbie*J7kF{fkxQ=J=A)OoO1WGx' \
			'97o-utWtfbwyn-$(js_n^d6uTZY7p{gd60=rPZ|;m', \
			"set() didn't handle the signature correctly"


def test_make_bytestring():
	'''Tests make_bytestring()'''

	basecard = keycard.EntryBase()
	basecard.type = "Test"
	basecard.field_names = [ 'Name', 'User-ID', 'Workspace-ID', 'Domain', 'Time-To-Live', 'Expires']
	basecard.set_fields({
		'Name':'Corbin Smith',
		'User-ID':'csmith',
		'Workspace-ID':'4418bf6c-000b-4bb3-8111-316e72030468',
		'Domain':'example.com',
		'Time-To-Live':'7',
		'Expires':'20201002',
		'Custody-Signature':'0000000000',
		'User-Signature':'1111111111',
		'Organization-Signature':'2222222222',
		'Entry-Signature':'3333333333'
	})

	expected_out = \
		b'Type:Test\r\n' \
		b'Name:Corbin Smith\r\n' \
		b'User-ID:csmith\r\n' \
		b'Workspace-ID:4418bf6c-000b-4bb3-8111-316e72030468\r\n' \
		b'Domain:example.com\r\n' \
		b'Time-To-Live:7\r\n' \
		b'Expires:20201002\r\n' \
		b'Custody-Signature:0000000000\r\n' \
		b'User-Signature:1111111111\r\n' \
		b'Organization-Signature:2222222222\r\n' \
		b'Entry-Signature:3333333333\r\n'
	
	actual_out = basecard.make_bytestring(4)
	assert actual_out == expected_out, "user byte string didn't match"



def test_set_expiration():
	'''Tests set_expiration()'''
	card = keycard.EntryBase()
	card.set_expiration(7)
	expiration = datetime.datetime.utcnow() + datetime.timedelta(7)
	assert card.fields['Expires'] == expiration.strftime("%Y%m%d"), "Expiration calculations failed"


if __name__ == '__main__':
	test_make_bytestring()
