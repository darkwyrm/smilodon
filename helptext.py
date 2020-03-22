'''This module merely stores the extensive help text for different commands to 
ensure the code remains easy to read.'''

login_cmd = '''Usage: login <address>
Log into a server once connected. The address used may be the numeric address
(e.g. 557207fd-0a0a-45bb-a402-c38461251f8f) or the friendly address (e.g. 
CatLover). It is not necessary to give the entire workspace address
(CatLover/example.com), but it will not cause any errors if used. If a
friendly address contains spaces, it must be enclosed in double quotes, as in
"John Q. Public/example.com" or "John Q. Public".'''

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