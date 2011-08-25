# PyChannel
## A Flask/Python implementation of Futaba 2channel

### Starting it up

To start the server, once all of the dependinces have been installed, just run `sudo python channel.py` (sudo because it runs on port 80) from the home directory. It's also possible to run this through Apache or in theory any WSGI capable webserver. Just set up channel.py as the wsgi file and change the path to the config file in channel.py to an absolute path.

### Logging in

Setting up the first admin:
---
Once one admin is registered into the system they can create other admins and mods via the `regi` short code. However, the first admin has to be added manually. The easiest way to do this is with the create\_admin.py script in the `/scripts` folder, which will prompt for all the required information and then add a user.
***Warning:*** This does absolutely zero privlidge checkling...

How Logging-in works:
---
1. Make a thread with a special command [login|admin|idk]
2. On this use an admin tripcode "###" (Maybe revise to just a trip "#" or a secure trip"##")
3. The post won't actually show up, but the browser will be redirected to a special admin|mod|janitor page
4. If the authentication fails, then you the post will go through as normal or maybe be redirected to a special ("code not recognized page")
5. All admin feature that the user has access to will show up
6. If the a|m wants to post as such they just put "asa" or "asadmin" into the command field, and the appropreaite capcode (if capcodes are on) will show up after thier name.
