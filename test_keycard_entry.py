'''This module tests the KeyCard class'''
import datetime
import os
import shutil
import time

import nacl.signing

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


if __name__ == '__main__':
	test_set()
