import redis, getpass, sys
from channel import Tripcode
import cPickle as cP

r = redis.Redis("localhost", db="2channel")
u_name = raw_input("Enter Username >>> ")
u_pass = getpass.getpass("Enter Password >>> ")
u_pass2 = getpass.getpass("Enter Password again >>> ")

if u_pass != u_pass2:
	print "Passwords do not match"
	sys.exit()
	
trip = Tripcode(u_name, u_pass, skip_check=True)
trip.set_permission("admin")

r.set("trip:{0}".format(trip.username), cP.dumps(trip))

print "Admin added..."
