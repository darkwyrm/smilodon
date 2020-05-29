'''This module tests the Profile and ProfileManager classes'''
import os

from userprofile import Profile, ProfileManager

def setup_test(name):
	'''Creates a new profile folder hierarchy'''
	test_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)),'testfiles')
	if not os.path.exists(test_folder):
		os.mkdir(test_folder)

	profiletest_folder = os.path.join(test_folder, name)
	if not os.path.exists(profiletest_folder):
		os.mkdir(profiletest_folder)
	
	return profiletest_folder

def test_profile_class():
	'''Test the Profile class. It's not big or complicated, so several 
	tests are grouped together into one'''

	profile = Profile()
	profile.name = 'Primary'
	profile.id = 'ca7149eb-e533-4de6-90b1-3b0181d6fa16'
	profile.wid = 'b5a9367e-680d-46c0-bb2c-73932a6d4007'
	profile.domain = 'example.com'

	# Most of the class is so simple that it doesn't really need test
	# coverage, but set_from_dict and as_dict are a bit more than that.
	test_dict = {
		'name' : 'Primary',
		'isdefault' : False,
		'id' : 'ca7149eb-e533-4de6-90b1-3b0181d6fa16',
		'wid' : 'b5a9367e-680d-46c0-bb2c-73932a6d4007',
		'domain' : 'example.com',
		'port' : 2001
	}
	assert profile.as_dict() == test_dict, "Output did not match test data"

	profile = Profile()
	profile.set_from_dict(test_dict)
	assert 	profile.name == 'Primary' and \
			profile.isdefault is False and \
			profile.id == 'ca7149eb-e533-4de6-90b1-3b0181d6fa16' and \
			profile.wid == 'b5a9367e-680d-46c0-bb2c-73932a6d4007' and \
			profile.domain == 'example.com' and \
			profile.port == 2001, "set_dict() assignments did not match test data."

def test_pman_init():
	'''Tests initialization of ProfileManager objects. Oddly enough, this 
	tests a lot of parts of the class'''

	# Because so much is done in the constructor, this unit performs basic tests on the following:
	# save_profiles()
	# load_profiles()
	# __index_for_profile()
	# create_profile()
	# get_default_profile()
	# set_default_profile()
	# activate_profile()
	# reset_db()

	profile_test_folder = setup_test('pman_init')
	pman = ProfileManager(profile_test_folder)
	
	# Nothing has been done, so there should be 1 profile called 'primary'.
	assert not pman.error_state.error(), "ProfileManager didn't init: %s" % pman.error_state.error()
	assert len(pman.profiles) == 1, "Profile folder bootstrap didn't have a profile"
	assert pman.active_index == 0, 'Active profile index not 0'
	assert pman.default_profile == 'primary', 'Init profile not primary'
