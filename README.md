# PyChannel

What is PyChannel:
---
PyChannel is a python implementation of a generic imageboard software (think 4chan) like Futaba channel geared toward ease of use, and a small code base. It is <i>Very</i> basic.

### Starting it up

First make sure that redis is running on the system before trying to start PyChannel.
To start the server, once all of the dependinces have been installed, just run `sudo python channel.py` from the home directory. It's also possible to run this through Apache via mod\_wsig or in theory any WSGI capable webserver. Just set up channel.py as the wsgi file and change the path to the config file in channel.py to an absolute path.

### Configuring PyChannel

All options can be found in `channel.ini` which is the configuration file for the app. A basic version of what `channel.ini` would look like goes something like this:

    [boards]
	g: General

the `[boards]` section defines the site's boards in the format `[SHORT]: [NAME]` where SHORT defines the url, and NAME shows up on the board's home page.

Other options specific to a certain board can also be set by making a new section `[BOARD:options]` where BOARD is the SHORT as defined in the `[boards]` section.

The `[BOARD:options]` sections has the cofiguration options for BOARD. All of these options are decribed in the channel.ini file and are implmented in the commands.py file.

The `[BOARD:commands]` sections have the config options for BOARD's commands (on|off toggles).

#### Setting up the first admin:

Once one admin is registered into the system they can create other admins and mods via the `regi` short code. However, the first admin has to be added manually. The easiest way to do this is with the create\_admin.py script in the `/scripts` folder, which will prompt for all the required information and then add a user.
***Warning:*** This does absolutely zero privlidge checking...

How Logging-in works:
---
1. Make a thread with a subject of `#!login`
2. On this thread use a capcode with the admin username and password
3. Upon login all admin feature that the user has access to will show up
