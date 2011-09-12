import redis, getpass, sys
from channel import app
from objects import Tripcode

u_name = raw_input("Enter Username >>> ")
u_pass = getpass.getpass("Enter Password >>> ")
u_pass2 = getpass.getpass("Enter Password again >>> ")

if u_pass != u_pass2:
	print "Passwords do not match"
	sys.exit()
	
ctx = app.test_request_context()
ctx.push()
app.preprocess_request()
	
trip = Tripcode(u_name, u_pass, skip_check=True)
trip.set_permission("admin")

trip.save()

print "Admin added..."

ctx.pop()
