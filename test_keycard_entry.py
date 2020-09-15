'''This module tests the KeyCard class'''
import base64
import datetime
import os
import shutil
import time

import nacl.signing

import keycard_entry as keycard
from keycard_entry import AlgoString, Base85Encoder

# Pylint doesn't detect the use of this import:
from retval import RetVal # pylint: disable=unused-import

def setup_test(name: str) -> str:
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


def make_test_userentry() -> keycard.UserEntry:
	'''Generates a user entry for testing purposes'''

	# User signing key
	skey = nacl.signing.SigningKey(b'{Ue^0)?k`s(>pNG&Wg9f5b;VHN1^PC*c4-($G#>}', Base85Encoder)

	# Organization signing key
	oskey = nacl.signing.SigningKey(b'GS30y3fdJX0H7t&p(!m3oXqlZI1ghz+o!B7Y92Y%', Base85Encoder)

	# crskey = nacl.signing.SigningKey(b'GS30y3fdJX0H7t&p(!m3oXqlZI1ghz+o!B7Y92Y%', Base85Encoder)
	# crekey = nacl.public.PrivateKey(b'VyFX5PC~?eL5)>q|6W7ciRrOJw$etlej<tY$f+t_', Base85Encoder)
	# ekey = nacl.public.PrivateKey(b'Wsx6BC(HP~goS-C_`K=6Daqr97kapfc=vQUzi?KI', Base85Encoder)

	usercard = keycard.UserEntry()
	usercard.set_fields({
		'Name':'Corbin Simons',
		'Workspace-ID':'4418bf6c-000b-4bb3-8111-316e72030468',
		'User-ID':'csimons',
		'Domain':'example.com',
		'Contact-Request-Signing-Key':'ED25519:7dfD==!Jmt4cDtQDBxYa7(dV|N$}8mYwe$=RZuW|',
		'Contact-Request-Encryption-Key':'CURVE25519:yBZ0{1fE9{2<b~#i^R+JT-yh-y5M(Wyw_)}_SZOn',
		'Public-Encryption-Key':'CURVE25519:_`UC|vltn_%P5}~vwV^)oY){#uvQSSy(dOD_l(yE'
	})

	# User sign and verify

	keystring = AlgoString()
	keystring.set('ED25519:' + base64.b85encode(skey.encode()).decode())
	rv = usercard.sign(keystring, 'User')
	assert not rv.error(), 'Unexpected RetVal error %s / %s' % (rv.error(), rv.info())
	assert usercard.signatures['User'], 'entry failed to user sign'
	
	vkey = nacl.signing.VerifyKey(skey.verify_key.encode())
	vkeystring = AlgoString()
	vkeystring.prefix = 'ED25519'
	vkeystring.data = base64.b85encode(vkey.encode()).decode()

	rv = usercard.verify_signature(vkeystring, 'User')
	assert not rv.error(), 'entry failed to user verify'

	# Organization sign and verify

	okeystring = AlgoString()
	okeystring.set('ED25519:' + base64.b85encode(oskey.encode()).decode())
	rv = usercard.sign(okeystring, 'Organization')
	assert not rv.error(), 'Unexpected RetVal error %s' % rv.error()
	assert usercard.signatures['Organization'], 'entry failed to user sign'

	ovkey = nacl.signing.VerifyKey(oskey.verify_key.encode())
	ovkeystring = AlgoString()
	ovkeystring.prefix = 'ED25519'
	ovkeystring.data = base64.b85encode(ovkey.encode()).decode()

	rv = usercard.verify_signature(ovkeystring, 'Organization')
	assert not rv.error(), 'entry failed to org verify'

	# Entry sign and verify

	rv = usercard.sign(keystring, 'Entry')
	assert not rv.error(), 'Unexpected RetVal error %s' % rv.error()
	assert usercard.signatures['Entry'], 'entry failed to entry sign'
	
	rv = usercard.verify_signature(vkeystring, 'Entry')
	assert not rv.error(), 'entry failed to entry verify'

	status = usercard.is_compliant()
	assert not status.error(), "UserEntry wasn't compliant"

	return usercard


def make_test_orgentry() -> keycard.OrgEntry:
	'''Generates an organizational entry for testing purposes'''

	# Primary signing key
	pskey = nacl.signing.SigningKey(b'GS30y3fdJX0H7t&p(!m3oXqlZI1ghz+o!B7Y92Y%', Base85Encoder)
	
	# Secondary signing key
	sskey = nacl.signing.SigningKey(b'GS30y3fdJX0H7t&p(!m3oXqlZI1ghz+o!B7Y92Y%', Base85Encoder)
	
	# Encryption key
	ekey = nacl.public.PrivateKey(b'Wsx6BC(HP~goS-C_`K=6Daqr97kapfc=vQUzi?KI', Base85Encoder)

	# TODO: Rework fields into org card
	orgcard = keycard.OrgEntry()
	orgcard.set_fields({
		'Name':'Corbin Simons',
		'Workspace-ID':'4418bf6c-000b-4bb3-8111-316e72030468',
		'User-ID':'csimons',
		'Domain':'example.com',
		'Contact-Request-Signing-Key':'ED25519:7dfD==!Jmt4cDtQDBxYa7(dV|N$}8mYwe$=RZuW|',
		'Contact-Request-Encryption-Key':'CURVE25519:yBZ0{1fE9{2<b~#i^R+JT-yh-y5M(Wyw_)}_SZOn',
		'Public-Encryption-Key':'CURVE25519:_`UC|vltn_%P5}~vwV^)oY){#uvQSSy(dOD_l(yE'
	})

	# Organization sign and verify

	pskeystring = AlgoString()
	pskeystring.set('ED25519:' + base64.b85encode(pskey.encode()).decode())
	rv = orgcard.sign(pskeystring, 'Organization')
	assert not rv.error(), 'Unexpected RetVal error %s' % rv.error()
	assert orgcard.signatures['Organization'], 'entry failed to user sign'

	ovkey = nacl.signing.VerifyKey(pskey.verify_key.encode())
	ovkeystring = AlgoString()
	ovkeystring.prefix = 'ED25519'
	ovkeystring.data = base64.b85encode(ovkey.encode()).decode()

	rv = orgcard.verify_signature(ovkeystring, 'Organization')
	assert not rv.error(), 'org entry failed to verify'

	return orgcard


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
	basecard.signature_info = [
		{ 'name':'Custody', 'optional':True },
		{ 'name':'User', 'optional':False },
		{ 'name':'Organization', 'optional':False },
		{ 'name':'Entry', 'optional':False }
	]

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


def test_sign():
	'''Tests signing of a keycard entry'''
	skey = nacl.signing.SigningKey(b'{Ue^0)?k`s(>pNG&Wg9f5b;VHN1^PC*c4-($G#>}', Base85Encoder)
	# crskey = nacl.signing.SigningKey(b'GS30y3fdJX0H7t&p(!m3oXqlZI1ghz+o!B7Y92Y%', Base85Encoder)
	# crekey = nacl.public.PrivateKey(b'VyFX5PC~?eL5)>q|6W7ciRrOJw$etlej<tY$f+t_', Base85Encoder)
	# ekey = nacl.public.PrivateKey(b'Wsx6BC(HP~goS-C_`K=6Daqr97kapfc=vQUzi?KI', Base85Encoder)

	basecard = keycard.EntryBase()
	basecard.type = "Test"
	basecard.field_names = [ 'Name', 'Workspace-ID', 'Domain', 'Contact-Request-Signing-Key',
			'Contact-Request-Encryption-Key', 'Public-Encryption-Key', 'Expires']
	basecard.set_fields({
		'Name':'Corbin Simons',
		'Workspace-ID':'4418bf6c-000b-4bb3-8111-316e72030468',
		'Domain':'example.com',
		'Contact-Request-Signing-Key':'ED25519:7dfD==!Jmt4cDtQDBxYa7(dV|N$}8mYwe$=RZuW|',
		'Contact-Request-Encryption-Key':'CURVE25519:yBZ0{1fE9{2<b~#i^R+JT-yh-y5M(Wyw_)}_SZOn',
		'Public-Encryption-Key':'CURVE25519:_`UC|vltn_%P5}~vwV^)oY){#uvQSSy(dOD_l(yE',
		'Expires':'20201002',

		# These junk signatures will end up being cleared when sign('User') is called
		'User-Signature':'1111111111',
		'Organization-Signature':'2222222222',
		'Entry-Signature':'3333333333'
	})
	basecard.signature_info = [
		{ 'name':'Custody', 'optional':True },
		{ 'name':'User', 'optional':False },
		{ 'name':'Organization', 'optional':False },
		{ 'name':'Entry', 'optional':False }
	]

	keystring = AlgoString()
	keystring.set('ED25519:' + base64.b85encode(skey.encode()).decode())
	rv = basecard.sign(keystring, 'User')
	assert not rv.error(), 'Unexpected RetVal error %s' % rv.error()
	assert basecard.signatures['User'], 'entry failed to user sign'
	
	expected_sig = \
		'ED25519:&7=iP?(=08IB44fog$pB7C*4(s9+7DRe=p(+1Mnoh{|avuYNAFDHG-H%0dFmYmyQL3DtPhup-*n?doI+'
	assert basecard.signatures['User'] == expected_sig, "entry did not yield the expected signature"


def test_verify_signature():
	'''Tests the signing of a test keycard entry'''
	# This is an extensive test because while it doesn't utilize all the fields that a standard
	# entry would normally have, it tests signing and verification of user, org, and entry
	# signatures. This test is also only intended to confirm success states of the method.

	# User signing key
	skey = nacl.signing.SigningKey(b'{Ue^0)?k`s(>pNG&Wg9f5b;VHN1^PC*c4-($G#>}', Base85Encoder)

	# Organization signing key
	oskey = nacl.signing.SigningKey(b'GS30y3fdJX0H7t&p(!m3oXqlZI1ghz+o!B7Y92Y%', Base85Encoder)

	# crekey = nacl.public.PrivateKey(b'VyFX5PC~?eL5)>q|6W7ciRrOJw$etlej<tY$f+t_', Base85Encoder)
	# ekey = nacl.public.PrivateKey(b'Wsx6BC(HP~goS-C_`K=6Daqr97kapfc=vQUzi?KI', Base85Encoder)

	basecard = keycard.EntryBase()
	basecard.type = "Test"
	basecard.field_names = [ 'Name', 'Workspace-ID', 'Domain', 'Contact-Request-Signing-Key',
			'Contact-Request-Encryption-Key', 'Public-Encryption-Key', 'Expires']
	basecard.set_fields({
		'Name':'Corbin Simons',
		'Workspace-ID':'4418bf6c-000b-4bb3-8111-316e72030468',
		'Domain':'example.com',
		'Contact-Request-Signing-Key':'ED25519:7dfD==!Jmt4cDtQDBxYa7(dV|N$}8mYwe$=RZuW|',
		'Contact-Request-Encryption-Key':'CURVE25519:yBZ0{1fE9{2<b~#i^R+JT-yh-y5M(Wyw_)}_SZOn',
		'Public-Encryption-Key':'CURVE25519:_`UC|vltn_%P5}~vwV^)oY){#uvQSSy(dOD_l(yE',
		'Expires':'20201002',

		# These junk signatures will end up being cleared when sign('User') is called
		'User-Signature':'1111111111',
		'Organization-Signature':'2222222222',
		'Entry-Signature':'3333333333'
	})
	basecard.signature_info = [
		{ 'name':'Custody', 'optional':True },
		{ 'name':'User', 'optional':False },
		{ 'name':'Organization', 'optional':False },
		{ 'name':'Entry', 'optional':False }
	]

	# User sign and verify

	keystring = AlgoString()
	keystring.set('ED25519:' + base64.b85encode(skey.encode()).decode())
	rv = basecard.sign(keystring, 'User')
	assert not rv.error(), 'Unexpected RetVal error %s' % rv.error()
	assert basecard.signatures['User'], 'entry failed to user sign'
	
	expected_sig = \
		'ED25519:&7=iP?(=08IB44fog$pB7C*4(s9+7DRe=p(+1Mnoh{|avuYNAFDHG-H%0dFmYmyQL3DtPhup-*n?doI+'
	assert basecard.signatures['User'] == expected_sig, \
			"entry did not yield the expected user signature"

	vkey = nacl.signing.VerifyKey(skey.verify_key.encode())
	vkeystring = AlgoString()
	vkeystring.prefix = 'ED25519'
	vkeystring.data = base64.b85encode(vkey.encode()).decode()

	rv = basecard.verify_signature(vkeystring, 'User')
	assert not rv.error(), 'entry failed to user verify'

	# Organization sign and verify

	okeystring = AlgoString()
	okeystring.set('ED25519:' + base64.b85encode(oskey.encode()).decode())
	rv = basecard.sign(okeystring, 'Organization')
	assert not rv.error(), 'Unexpected RetVal error %s' % rv.error()
	assert basecard.signatures['Organization'], 'entry failed to user sign'

	expected_sig = \
		'ED25519:1k*c9Ij~7~!LTKVi%03t>lNWyu;z&HstS*_w{vLuWY`b=)wxQDqQqryUoR#=u<GKg+8pGgH7e!#0>%IX'
	assert basecard.signatures['Organization'] == expected_sig, \
			"entry did not yield the expected org signature"
	

	ovkey = nacl.signing.VerifyKey(oskey.verify_key.encode())
	ovkeystring = AlgoString()
	ovkeystring.prefix = 'ED25519'
	ovkeystring.data = base64.b85encode(ovkey.encode()).decode()

	rv = basecard.verify_signature(ovkeystring, 'Organization')
	assert not rv.error(), 'entry failed to org verify'

	# Entry sign and verify

	rv = basecard.sign(keystring, 'Entry')
	assert not rv.error(), 'Unexpected RetVal error %s' % rv.error()
	assert basecard.signatures['Entry'], 'entry failed to entry sign'
	
	expected_sig = \
		'ED25519:oXQvALV4gf2pn|IQhf2^KKBoL`8w7n{Q(Du{W2X05>WY{hVEeMoM|9NGUpKkjIutFlp$y8(E(EdzTx)<'
	assert basecard.signatures['Entry'] == expected_sig, \
			"entry did not yield the expected entry signature"

	rv = basecard.verify_signature(vkeystring, 'Entry')
	assert not rv.error(), 'entry failed to entry verify'


def test_base_is_compliant():
	'''Tests compliance testing for the base class'''
	basecard = keycard.EntryBase()
	status = basecard.is_compliant()
	assert status.error(), "EntryBase met compliance and shouldn't"


def test_is_compliant_user():
	'''Tests compliance testing for the UserEntry class'''

	# The original code for this test made a great setup for other UserEntry-based tests
	make_test_userentry()


def test_is_compliant_org():
	'''Tests compliance testing for the OrgEntry class'''

	# Organization signing key
	oskey = nacl.signing.SigningKey(b'GS30y3fdJX0H7t&p(!m3oXqlZI1ghz+o!B7Y92Y%', Base85Encoder)

	orgcard = keycard.OrgEntry()
	orgcard.set_fields({
		'Name':'Acme Widgets, Inc',
		'Contact-Admin':'admin/example.com',
		'Contact-Abuse':'abuse/example.com',
		'Language':'en',
		'Primary-Signing-Key':'ED25519:7dfD==!Jmt4cDtQDBxYa7(dV|N$}8mYwe$=RZuW|',
		'Encryption-Key':'CURVE25519:_`UC|vltn_%P5}~vwV^)oY){#uvQSSy(dOD_l(yE'
	})

	# sign and verify

	okeystring = AlgoString()
	okeystring.set('ED25519:' + base64.b85encode(oskey.encode()).decode())
	rv = orgcard.sign(okeystring, 'Organization')
	assert not rv.error(), 'Unexpected RetVal error %s' % rv.error()
	assert orgcard.signatures['Organization'], 'entry failed to user sign'

	ovkey = nacl.signing.VerifyKey(oskey.verify_key.encode())
	ovkeystring = AlgoString()
	ovkeystring.prefix = 'ED25519'
	ovkeystring.data = base64.b85encode(ovkey.encode()).decode()

	rv = orgcard.verify_signature(ovkeystring, 'Organization')
	assert not rv.error(), 'entry failed to org verify'

	status = orgcard.is_compliant()
	assert not status.error(), "OrgEntry wasn't compliant"


def test_user_chaining():
	'''Tests chaining of user entries and verification thereof'''
	userentry = make_test_userentry()

	# User signing key
	skeystring = AlgoString('ED25519:{Ue^0)?k`s(>pNG&Wg9f5b;VHN1^PC*c4-($G#>}')

	# Organization signing key
	oskeystring = AlgoString('ED25519:GS30y3fdJX0H7t&p(!m3oXqlZI1ghz+o!B7Y92Y%')
	
	chaindata = userentry.chain(skeystring, True)
	assert not chaindata.error(), f'userentry.chain returned an error: {chaindata.error()}'

	new_entry = chaindata['entry']

	# Now that we have a new entry, it only has a valid custody signature. Add all the other 
	# signatures needed to be compliant and then verify the whole thing.

	# The signing key is replaced during chain()
	status = skeystring.set(chaindata['sign.private'])
	assert not status.error(), 'test_user_chain: new signing key has bad format'
	
	status = new_entry.sign(skeystring, 'User')
	assert not status.error(), f'new entry failed to user sign: {status}'

	status = new_entry.sign(oskeystring, 'Organization')
	assert not status.error(), f'new entry failed to org sign: {status}'

	status = new_entry.sign(skeystring, 'Entry')
	assert not status.error(), f'new entry failed to entry sign: {status}'

	status = new_entry.is_compliant()
	assert not status.error(), f'new entry failed compliance check: {status}'

	# Testing of chain() is complete. Now test verify_chain()
	status = new_entry.verify_chain(userentry)
	assert not status.error(), f'chain of custody verification failed: {status}'


def test_keycard_chain_verify():
	'''Tests entry rotation of a keycard'''
	userentry = make_test_userentry()

	card = keycard.Keycard()
	card.entries.append(userentry)

	chaindata = card.chain(True)
	assert not chaindata.error(), f'keycard chain failed: {chaindata}'

	new_entry = chaindata['entry']
	oskeystring = AlgoString('ED25519:GS30y3fdJX0H7t&p(!m3oXqlZI1ghz+o!B7Y92Y%')

	skeystring = AlgoString(chaindata['sign.private'])
	status = new_entry.sign(skeystring, 'User')
	assert not status.error(), f'chained entry failed to user sign: {status}'

	status = new_entry.sign(oskeystring, 'Organization')
	assert not status.error(), f'chained entry failed to org sign: {status}'

	status = new_entry.sign(skeystring, 'Entry')
	assert not status.error(), f'chained entry failed to entry sign: {status}'

	card.entries[-1] = new_entry
	status = card.verify()
	# assert not status.error(), f'keycard failed to verify: {status}'


if __name__ == '__main__':
	test_user_chaining()
