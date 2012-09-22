Plugins
==========
The term *plugins* is used rather loosely in the context of PyChannel. In PyChannel a *plugin* is any file in
the *plugins* folder of the package. All of these files are imported at runtime. Each of these modules is supposed
to have some variable called *plug* which represents a class or subclass of :class:`~PyChannel.helpers.plugin.PluginHelper`
and then uses the :class:`~PyChannel.helpers.plugin.PluginHelper`'s :meth:`~PyChannel.helpers.plugin.PluginHelper.register`
decorator to subscribe to certain signals.