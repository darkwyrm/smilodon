# smilodon

A text-based client for the Anselus platform written in Python released under the GPLv3 license.

## Description

Smilodon started as a quickie test client to interact with server code and guide client-side spec development. As its developed, though, it has taken on a shape of its own. System administrators deserve to have good tools -- their jobs are hard as it is already. So many admins live in the Terminal, so having an Anselus client that runs there is important to good server maintenance.

It is written in Python and will be developed on top of the [urwid](http://urwid.org/) CLI toolkit. At some point, it will probably also include functionality for performing administrative tasks.

## Status

The application is in early development. It currently uses a REPL style command environment and can handle account registration and login. Features are currently limited by progress of the server code. As server development continues, it will gradually take shape into its envisioned form.

## Building

Setup is a matter of checking out the repository, setting up your virtual environment, `pip install -r requirements.txt`, and then `python smilodon.py`. Eventually it will be just a matter of installing directly from pip, but that would require day-to-day usefulness that it has not yet achieved. Hacking on Smilodon will give you a good handle on the technologies used by the Anselus platform.
