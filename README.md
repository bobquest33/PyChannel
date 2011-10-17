# PyChannel

What is PyChannel:
---
PyChannel is a python implementation of a generic imageboard software (think 4chan) like Futaba channel geared toward ease of use, and a small code base. It is <i>Very</i> basic.

### Starting it up

First make sure that redis is running on the system before trying to start PyChannel.
To start the server, once all of the dependencies have been installed, just run `pychannel-serve` from the home directory. It's also possible to run this through Apache via mod\_wsgi or in theory any WSGI capable webserver.

#### Setting up the first admin:

Once one admin is registered into the system they can create other admins and mods via the `regi` short code. However, the first admin has to be added manually. The easiest way to do this is with the `pychannel-admin`  program in the home folder,
just run `pychannel-admin create` which will prompt for all the required information and then add a user.
***Warning:*** This does absolutely zero privilege checking...

How Logging-in works:
---
1. Make a thread with a subject of `#!login`
2. On this thread use a tripcode with the admin username and password
3. Upon login all admin feature that the user has access to will show up

#### Documentation, Links, Etc.
[Latest stable version up and running](http://pychannel.joshkunz.com)
[Full documentation](http://docs.joshkunz.com/pychannel)
