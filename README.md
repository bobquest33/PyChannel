# PyChannel
## A Flask/Python implementation of 2channel

This is some text just to check

How Logging-in works:
	1. Make a thread with a special command [login|admin|idk]
	2. On this use an admin tripcode "###" (Maybe revise to just a trip "#" or a secure trip"##")
	3. The post won't actually show up, but the browser will be redirected to a special admin|mod|janitor page
	4. If the authentication fails, then you the post will go through as normal or maybe be redirected to a special ("code not recognized page")
	5. All admin feature that the user has access to will show up
	6. If the a|m wants to post as such they just put "asa" or "asadmin" into the command field, and the appropreaite capcode (if capcodes are on)
	will show up after thier name.