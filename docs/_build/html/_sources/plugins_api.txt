Plugins
=======

The plugins portion of the package contains most of the power of PyChannel as a whole. All of the files found within the plugins directory are 
imported at runtime so that they can subscribe to signals and even fire off thier own signals thus making a highly extendable interface.
The comprehensive plugin documentation can be found at :doc:`Getting Started with Plugins <plugins>`

.. py:module:: PyChannel.plugins

=================
The System plugin
=================

PyChannel has one major plugin that it comes pre-packaged with, the *system* plugin. This plugin handles everyting from saving images to enforcing bans.

.. py:module:: PyChannel.plugins.system

.. py:data:: PyChannel.plugins.system.plug

   The requisite instance of :class:`~PyChannel.helpers.plugin.PluginHandler`.

.. py:function:: PyChannel.plugins.system.check_ban(sender, meta)
   
   Checks for any bans currently in force on a particular ip address when a POST request is made. If one is found, then
   it will return a nicely formatted error with the time remaining on the ban.

   Subscribes to the 'execute_commands' signal.

.. py:function:: PyChannel.plugins.system.check_valid(sender, meta)

   Checks to see if a particular post is valid. It Checks quite a few config options and returns an error message if any of the conditions are
   not met.

   Subscribes to the 'new_post' signal.

.. py:function:: PyChannel.plugins.system.check_image(sender, meta)

   Checks to see if an image was included in the post. If images are allowed on that particular board then the image will be saved (if it does 
   not already exist) and is added to the post.

   Subscribes to the 'new_post' signal.
