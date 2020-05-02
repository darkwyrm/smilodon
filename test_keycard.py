import datetime

import keycard


def test_orgcard():
	'''Tests the OrgCard constructor'''
	card = keycard.OrgCard()
	compliant, bad_field = card.is_compliant()
	assert not compliant, "Initial OrgCard() complies but shouldn't"

	card.set_fields({
		'Name':'Example, Inc.',
		'Contact-Admin':'admin/example.com',
		'Primary-Signing-Key':'l<V_`qb)QM=K#F>u-GCs?W1+>^nl1*#!%$NRxP-6',
		'Encryption-Key':'9+8r$)N}={KFhGD3H2rv<q8$72b4A$K!DN;bGrvt'
	})
	compliant, bad_field = card.is_compliant()
	assert compliant, "OrgCard() compliance failed: %s" % bad_field

def test_set_fields():
	'''Tests setfields'''
	card = keycard.OrgCard()
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
		'Primary-Signing-Key':'l<V_`qb)QM=K#F>u-GCs?W1+>^nl1*#!%$NRxP-6',
		'Secondary-Signing-Key':'`D7QV39R926R3nf<NjU;pi)80xJxvj#1&iWD0!%6',
		'Encryption-Key':'9+8r$)N}={KFhGD3H2rv<q8$72b4A$K!DN;bGrvt',
		'Web-Access':'mail.example.com:2081',
		'Mail-Access':'mail.example.com:2001',
		'Message-Size-Limit':'100MB',
		'noncompliant-field':'foobar2000'
	})
	compliant, bad_field = card.is_compliant()
	assert compliant, "Setfield() compliance failed: %s" % bad_field


def test_usercard():
	'''Tests the UserCard constructor'''
	card = keycard.UserCard()
	compliant, bad_field = card.is_compliant()
	assert not compliant, "Initial UserCard() complies but shouldn't"

	card.set_fields({
		'Workspace-ID':'00000000-1111-2222-3333-444444444444',
		'Domain':'example.com',
		'Contact-Request-Key':'l<V_`qb)QM=K#F>u-GCs?W1+>^nl1*#!%$NRxP-6',
		'Public-Encryption-Key':'`D7QV39R926R3nf<NjU;pi)80xJxvj#1&iWD0!%6',
	})
	compliant, bad_field = card.is_compliant()
	assert compliant, "UserCard() compliance failed: %s" % bad_field


def test_set_expiration():
	'''Tests set_expiration'''
	card = keycard.UserCard()
	card.set_expiration(7)
	expiration = datetime.datetime.utcnow() + datetime.timedelta(7)
	assert card.fields['Expires'] == expiration.strftime("%Y%m%d"), "Expiration calculations failed"
