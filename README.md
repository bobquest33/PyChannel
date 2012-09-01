# PyChannel

What is PyChannel:
---
PyChannel is a python implementation of a generic imageboard software based on Futaba Channel (think 4chan) geared toward ease of use, extendability, and a small code base.

### Starting it up

First make sure that redis is running on the system before trying to start PyChannel.
To start the server, once all of the dependencies have been installed, just run 
`pychannel-serve` from the home directory. It's also possible to run this through 
Apache via mod\_wsgi or in theory any WSGI capable webserver. (tornado, gunicorn, etc.)

#### Setting up the first admin:

Once one admin is registered into the system they can create other admins and mods via the `regi`
short code. However, the first admin has to be added manually. The easiest way to do this is 
with the `pychannel-admin`  program in the home folder, just run `pychannel-admin create` 
which will prompt for all the required information and then add a user.
***Warning:*** This does absolutely zero privilege checking...

### Read More, Documentation, Example
[Latest stable version up and running](http://pychannel.joshkunz.com)
[Full documentation](http://www.joshkunz.com/PyChannel)
