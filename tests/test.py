import random, sys
import channel as c
import cPickle as cP
import redis
from datetime import datetime

WEIGHTED_LETTERS = "aaaaaaaaaaaabbbccccddddddeeeeeeeeeeeeeeeeeeeeffffggggh\
hhhhhhhhhiiiiiiiiiiiikllllllmmmmnnnnnnnnnnoooooooooooppprrrrrrrrrsssssssss\
tttttttttttttttuuuuuvvwwwyyy"


def random_word(*args):
    return "".join(random.sample(WEIGHTED_LETTERS, random.randint(*args)))

lr = 50 if len(sys.argv) < 2 else int(sys.argv[1])

ctx = c.app.test_request_context()
ctx.push()
c.app.preprocess_request()
t = c.Thread(
    text = "This thread is a stress test on the loading speeds of the page",
    subject = "Stress Test",
    author = "Admin",
    board = "g")

t.save()

for z in xrange(lr):
	xz = c.Reply(t.id,
		text = random_word(10, 80),
		subject = random_word(0, 15),
		author = random_word(0, 22),
		board = "g")
	
	xz.save()
	
	print "Added Reply %s (%s)"% (xz.id, z)

ctx.pop()
