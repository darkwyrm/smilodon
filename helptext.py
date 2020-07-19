'''This module merely stores the extensive help text for different commands to 
ensure the code remains easy to read.'''

login_cmd = '''Usage: login <address>
Log into a server once connected. The address used may be the numeric address
(e.g. 557207fd-0a0a-45bb-a402-c38461251f8f) or the friendly address (e.g. 
CatLover). Because multiple domains could be hosted by the same server, it is 
necessary to give the entire workspace address. Note that if the address is 
omitted, the command is assumed to log into main account for the profile.

Examples:
login f009338a-ea14-4d59-aa48-016829835cd7/example.com
login CatLover/example.com
login
'''

profile_cmd = '''Usage: profile <action> <profilename>
Manage profiles. Actions are detailed below.

create <name> - create a new profile, which is just a name for identification
by the user. The profile may be named anything other than "default", which is
reserved. Profile names are case-sensitive, so "Default" is permitted. Note
that once created, it must be made active and either logging in or
registration is needed for the profile to be useful.

delete <name> - delete a profile and any files associated with it. Because it
cannot be undone, this command requires confirmation from the user.

rename <oldname> <newname> - change the name of a profile. Neither name may be
"default".

list - prints a list of all available profiles

setdefault <name> - sets the profile to be loaded on startup. If only one
profile exists, this action has no effect.

set <name> - activates the specified profile and deactivates the current one.'''

register_cmd = '''Usage: register <serveraddress>
Register a new workspace account. This command requires a connection to a
server. Depending on the registration type set on the server, this command may
return a status other than success or failure. If a server immediately creates
a new workspace account, this command will print the new numeric address
created.'''

shell_cmd = '''Usage: shell <command>
Executes a command directly in the regular user shell. On Windows, this is 
Command Prompt. On UNIX-like platforms, this is the default shell, usually
bash.
Aliases: ` , sh'''

setinfo_cmd = '''Usage: setinfo <infotype> <value>
Sets contact information for the profile. Available information which can be 
set is listed below:
'''

setuserid_cmd = '''Usage: setuserid <userid>
Sets the user ID for the profile. This is the part before the slash in your 
Anselus address.

The user ID must be all one word -- no spaces -- but you may use any 
combination of letters, numbers, or symbols excluding the forward slash (/)
and double quote ("). You may also use non-English characters. It can be up to
128 characters, although user IDs of that length are not recommended.

Capitalization does not matter. If the user ID on your server is already
taken, you will need to choose another.

Once changed you will need to update your keycard.

Examples:

KingArthur
Аделина
Aslan_the_Lion
大和
karlweiß-52
'''
