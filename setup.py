from distutils.core import setup
setup(
	name="PyChannel",
	version="0.7",
	description="A Python Imageboard",
	author="Josh Kunz",
	author_email="joshkunz@me.com",
	url="http://pychannel.joshkunz.com",
	requires=["flask >=0.7", "blinker >=1.1"],
	provides=["PyChannel"],
	packages=["PyChannel"],
	package_data={'PyChannel': ['templates', 'static']}
)
