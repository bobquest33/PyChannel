import random, sys
import cPickle as cP
import redis
from objects import Thread, Reply
from channel import app
from datetime import datetime

WEIGHTED_LETTERS = "aaaaaaaaaaaabbbccccddddddeeeeeeeeeeeeeeeeeeeeffffggggh\
hhhhhhhhhiiiiiiiiiiiikllllllmmmmnnnnnnnnnnoooooooooooppprrrrrrrrrsssssssss\
tttttttttttttttuuuuuvvwwwyyy"


def random_word(*args):
    return "".join(random.sample(WEIGHTED_LETTERS, random.randint(*args)))

lr = 50 if len(sys.argv) < 2 else int(sys.argv[1])

ctx = app.test_request_context()
ctx.push()
app.preprocess_request()
t = Thread(
    text = "This thread is a stress test on the loading speeds of the page",
    subject = "Stress Test",
    author = "Admin",
    capcode = "## Admin ##",
    board = "g")

t.save()

for z in xrange(lr):
	xz = Reply(t.id,
		text = random_word(10, 80),
		subject = random_word(0, 15),
		author = random_word(0, 22),
		board = "g")
	
	xz.save()
	
	print "Added Reply %s (%s)"% (xz.id, z)

ctx.pop()
