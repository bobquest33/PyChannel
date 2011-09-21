Helpers
========

.. py:module:: PyChannel.helpers

==============
Plugin Helpers
==============
.. py:module:: PyChannel.helpers.plugin

.. py:exception:: PyChannel.helpers.plugin.ImmediateRedirect(redirect_object)

   When this error is raised anywhere within the request context it will immediately redirect the request to the
   supplied url. Useful for plugins that don't want a post to be saved after completing some action.

   :param redirect_object: A :func:`flask.redirect` object.

.. py:class:: PyChannel.helpers.plugin.PluginHandler

   A Helpful class that allows various plugins and commands to access the signaling interface.
   
   .. py:method:: register(self, signal_name)

	  A decorator to subscribe the decorated function to the signal *signal_name*
	  Example::

	      @plug.register("new_post")
	      def run_on_new_post(sender, **kwargs):
	          print "New post!"

	  :param signal_name: Name of the signal to subscribe to.
	  :type signal_name: string
	  :rtype: Function

   .. py:method:: signal(self, signal_name)
      
	  Add a new signal named *signal_name*\ . These signals are global and can be recived in any plugin. These signals are also garenteed to exist
	  before any plugins try to emit them see :meth:`~PyChannel.helpers.plugin.PluginHandler.fire`

   .. py:method:: fire(self, signal_name, \**kwargs)
	  
      Emit the signal *signal_name* from within a plugin. Fire takes any number of keyword arguments which are passed to the signal's subscribers.

===============
Channel Helpers
===============

.. py:module:: PyChannel.helpers.channel

.. py:function:: PyChannel.helpers.channel.get_opt(section, option[, default=None[, type='str']])

   A helper function used for parsing out options from the configuration file.

   :param section: The name of the section to search
   :param option: The name of the option to retrive
   :param default: The default return value. Will be returned if A) The section does not exist B) The option does not exist
   :param type: The type of coercion to preform on the value returned default is none ('str')
   :type type: 'str', 'bool', 'int', 'float'

.. py:function:: PyChannel.helpers.channel.get_post_opts(subject_line, author_line)
	
   Preforms the string parsing on the *command* line and *author* line of the post form. This is almost never used by anything except internal
   PyChannel functions.

   :returns: A meta object (a specific dictionary) that is used extensively throughoght PyChannel

===============
Command Helpers
===============

.. py:module:: PyChannel.helpers.command

.. py:function:: PyChannel.helpers.command.require(*args)

   A function used to check if the meta object passed to certain commands has particular keys, and to fail gracefully if those keys do not exist.
   It also checks to see if the command being decorated has even been called.
   Example::

       @plug.register("execute_commands")
       @require("post", trip)
       def requires_post_and_trip(sender, meta):
           print "This meta definitly has a trip and post"

