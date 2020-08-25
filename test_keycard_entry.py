'''This module tests the KeyCard class'''
import datetime
import os
import shutil
import time

import nacl.signing

import keycard_entry as keycard
from keycard_entry import Base85Encoder
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


def test_orgentry():
	'''Tests the OrgEntry constructor'''
	card = keycard.OrgEntry()
	assert card.is_compliant().error(), "Initial OrgEntry() complies but shouldn't"

	card.set_fields({
		'Name':'Example, Inc.',
		'Contact-Admin':'admin/example.com',
		'Primary-Signing-Algorithm':'ed25519',
		'Primary-Signing-Key':'l<V_`qb)QM=K#F>u-GCs?W1+>^nl1*#!%$NRxP-6',
		'Encryption-Key-Algorithm':'curve25519',
		'Encryption-Key':'9+8r$)N}={KFhGD3H2rv<q8$72b4A$K!DN;bGrvt'
	})
	rv = card.is_compliant()
	assert rv.error(), "OrgEntry() should not comply and did"
	assert rv.info() != 'Missing field Organization-Signature', "Signature complied and shouldn't"


def test_set_fields():
	'''Tests setfields'''
	card = keycard.OrgEntry()
	card.set_fields({
		'Name':'Example, Inc.',
		'Street':'1443 Dogwood Lane',
		'City':'Nogales',
		'Province':'AZ',
		'Postal-Code':'85621',
		'Country':'United States',
		'Contact-Admin':'admin/example.com',
		'Language':'English',
		'Website':'https://www.example.com',
		'Primary-Signing-Algorithm':'ed25519',
		'Primary-Signing-Key':'l<V_`qb)QM=K#F>u-GCs?W1+>^nl1*#!%$NRxP-6',
		'Secondary-Signing-Algorithm':'ed25519',
		'Secondary-Signing-Key':'`D7QV39R926R3nf<NjU;pi)80xJxvj#1&iWD0!%6',
		'Encryption-Key-Algorithm':'curve25519',
		'Encryption-Key':'9+8r$)N}={KFhGD3H2rv<q8$72b4A$K!DN;bGrvt',
		'Web-Access':'mail.example.com:2081',
		'Mail-Access':'mail.example.com:2001',
		'Message-Size-Limit':'100MB',
		'noncompliant-field':'foobar2000'
	})
	rv = card.is_compliant()
	assert rv.error(), "Setfield() should not comply and did"
	assert rv.info() != 'Missing field Organization-Signature', "Signature complied and shouldn't"


def test_set_expiration():
	'''Tests set_expiration'''
	card = keycard.UserEntry()
	card.set_expiration(7)
	expiration = datetime.datetime.utcnow() + datetime.timedelta(7)
	assert card.fields['Expires'] == expiration.strftime("%Y%m%d"), "Expiration calculations failed"


def test_userentry():
	'''Tests the UserEntry constructor'''
	card = keycard.UserEntry()
	rv = card.is_compliant()
	assert rv.error(), "Initial UserEntry() complies but shouldn't"

	card.set_fields({
		'Workspace-ID':'00000000-1111-2222-3333-444444444444',
		'Domain':'example.com',
		'Contact-Request-Signing-Algorithm':'ed25519',
		'Contact-Request-Signing-Key':'7dfD==!Jmt4cDtQDBxYa7(dV|N$}8mYwe$=RZuW|',
		'Contact-Request-Encryption-Algorithm':'curve25519',
		'Contact-Request-Encryption-Key':'fbqsEyXT`Sq?us{OgVygsK|zBP7njBmwT+Q_a*0E',
		'Public-Encryption-Algorithm':'curve25519',
		'Public-Encryption-Key':'0IaDFoy}NDe1@fzkg9z!5`@gclY20sRINMJd_{j!',
	})
	card.signatures['User'] = 'TestBadUserSig'
	card.signatures['Organization'] = 'TestBadOrgSig'

	rv = card.is_compliant()
	assert not rv.error(), "UserEntry() compliance failed: %s" % rv.info()


def test_userentry_bytestring():
	'''Tests the UserEntry get_bytestring() method'''
	card = keycard.UserEntry()
	card.set_fields({
		'Name':'Corbin Simons',
		'Workspace-ID':'4418bf6c-000b-4bb3-8111-316e72030468',
		'Domain':'example.com',
		'Contact-Request-Signing-Algorithm':'ed25519',
		'Contact-Request-Signing-Key':'7dfD==!Jmt4cDtQDBxYa7(dV|N$}8mYwe$=RZuW|',
		'Contact-Request-Encryption-Algorithm':'curve25519',
		'Contact-Request-Encryption-Key':'yBZ0{1fE9{2<b~#i^R+JT-yh-y5M(Wyw_)}_SZOn',
		'Public-Encryption-Algorithm':'curve25519',
		'Public-Encryption-Key':'_`UC|vltn_%P5}~vwV^)oY){#uvQSSy(dOD_l(yE',
		'Expires':'20201002'
	})

	expected_out = b'Type:User\r\n' \
		b'Name:Corbin Simons\r\n' \
		b'Workspace-ID:4418bf6c-000b-4bb3-8111-316e72030468\r\n' \
		b'Domain:example.com\r\n' \
		b'Contact-Request-Signing-Algorithm:ed25519\r\n' \
		b'Contact-Request-Signing-Key:7dfD==!Jmt4cDtQDBxYa7(dV|N$}8mYwe$=RZuW|\r\n' \
		b'Contact-Request-Encryption-Algorithm:curve25519\r\n' \
		b'Contact-Request-Encryption-Key:yBZ0{1fE9{2<b~#i^R+JT-yh-y5M(Wyw_)}_SZOn\r\n' \
		b'Public-Encryption-Algorithm:curve25519\r\n' \
		b'Public-Encryption-Key:_`UC|vltn_%P5}~vwV^)oY){#uvQSSy(dOD_l(yE\r\n' \
		b'Time-To-Live:7\r\n' \
		b'Expires:20201002\r\n'
	
	assert card.make_bytestring(True) == expected_out, "user byte string didn't match"


def test_userentry_sign():
	'''Tests the signing of a user entry'''
	skey = nacl.signing.SigningKey(b'{Ue^0)?k`s(>pNG&Wg9f5b;VHN1^PC*c4-($G#>}', Base85Encoder)
	# crskey = nacl.signing.SigningKey(b'GS30y3fdJX0H7t&p(!m3oXqlZI1ghz+o!B7Y92Y%', Base85Encoder)
	# crekey = nacl.public.PrivateKey(b'VyFX5PC~?eL5)>q|6W7ciRrOJw$etlej<tY$f+t_', Base85Encoder)
	# ekey = nacl.public.PrivateKey(b'Wsx6BC(HP~goS-C_`K=6Daqr97kapfc=vQUzi?KI', Base85Encoder)

	card = keycard.UserEntry()
	card.set_fields({
		'Name':'Corbin Simons',
		'Workspace-ID':'4418bf6c-000b-4bb3-8111-316e72030468',
		'Domain':'example.com',
		'Contact-Request-Signing-Algorithm':'ed25519',
		'Contact-Request-Signing-Key':'7dfD==!Jmt4cDtQDBxYa7(dV|N$}8mYwe$=RZuW|',
		'Contact-Request-Encryption-Algorithm':'curve25519',
		'Contact-Request-Encryption-Key':'yBZ0{1fE9{2<b~#i^R+JT-yh-y5M(Wyw_)}_SZOn',
		'Public-Encryption-Algorithm':'curve25519',
		'Public-Encryption-Key':'_`UC|vltn_%P5}~vwV^)oY){#uvQSSy(dOD_l(yE',
		'Expires':'20201002'
	})
	expected_sig = '#sl4;saPEf*w~PxituHuiXrgP^tko9uO8kib;Wt$>*r(ECw8K;>Uq7zlAWx9%D9HU)`HV87@6Ht5elCJ'
	
	rv = card.sign(skey.encode(), 'User')
	assert not rv.error(), 'Unexpected RetVal error %s' % rv.error()
	assert card.signatures['User'], 'keycard failed to user sign'
	assert card.signatures['User'] == expected_sig, "card did not yield the expected signature"


def test_keycard_save():
	'''Tests the Keycard class' save() method'''
	# TODO: Implement


def test_keycard_load():
	'''Tests the Keycard class' load() method'''
	# TODO: Implement

