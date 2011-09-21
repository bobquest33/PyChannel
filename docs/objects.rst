Objects
=======
These objects represent different data stuctures throughought PyChannel.

.. py:module:: PyChannel.objects

=======
Signals
=======
This class acts as a namespace for signals. It, by default creates a few signals used by the PyChannel Core. 
All of the signals that are created by the plugins are also added to this class at runtime.

.. py:class:: PyChannel.objects.Signals

   When an instance of a class is created it creates a few named signals that are used by the PyChannel Core.

   .. py:attribute:: PyChannel.objects.Signals.execute_commands

      This signals is emmited when a new post is created before the new_post signal is emmited in order to ensure
	  that the commands are run before the other new_post plugins.

   .. py:attribute:: PyChannel.objects.Signals.new_post

      Emmited when a new post is made before the post is saved.

   .. py:attribute:: PyChannel.objects.Signals.save_post

      Emmited after a post has been saved, as such all changes to the post must be saved.

   .. py:attribute:: PyChannel.objects.Signals.delete_post

      Emmited after a post has been deleted.

   .. py:attribute:: PyChannel.objects.Signals.prune_thread

      Emmited when a thread is :term:`pruned <Pruning>`.

   .. py:attribute:: PyChannel.objects.Signals.new_image

      Emmited when a new image is saved.

   .. py:attribute:: PyChannel.objects.Signals.delete_image

      Emmited when an image is deleted.

   .. py:attribute:: PyChannel.objects.Signals.new_ban

      Emmited when a new ban is created.

=========
Tripcodes
=========

.. autoclass:: PyChannel.objects.Tripcode
   :members:

======
Images
======

.. autoclass:: PyChannel.objects.PostImage
   :members:

   .. py:attribute:: resolution
     
      A two item tuple in the format (length, width) in pixels.

   .. py:attribute:: format

      A the images format. ie. 'png'

   .. py:attribute:: filesize

      The image's size in bytes.

   .. py:attribute:: url

      The image's access url. (usually ``/images/[id].[format]``)

   .. attribute:: thumb_url

      The image's thumbnail url. (usually ``/images/thumb.[id].[format]``)

=====
Board
=====

.. autoclass:: PyChannel.objects.Board
   :members:

   .. attribute:: short
   	
   	  The board's short code. ie. 'g' for 'General'
	   	
   .. attribute:: title
			
	  The boards full title. ie. 'General' for /g/.

   .. attribute:: len(b)
	  
	  The number of posts on the board *b*.

============
Post Classes
============

.. autoclass:: PyChannel.objects.Post
   :members:

   .. attribute:: id

      The numeric id of this post.

   .. attribute:: created

      A :class:`datetime.datetime` object representing the time
      the post was made.

   .. attribute:: created_by

      The ip address of the creating user. (used for banning.)

.. autoclass:: PyChannel.objects.Thread
   :members:
   :show-inheritance:
   :inherited-members:

   .. attribute:: len(t)

      The number of replies to thread *t*.

.. autoclass:: PyChannel.objects.Reply
   :members:
   :show-inheritance:
   :inherited-members:
