import random, sys
from channel import Thread, Reply
import cPickle as cP
import redis
from time import sleep


WEIGHTED_LETTERS = "aaaaaaaaaaaabbbccccddddddeeeeeeeeeeeeeeeeeeeeffffggggh\
hhhhhhhhhiiiiiiiiiiiikllllllmmmmnnnnnnnnnnoooooooooooppprrrrrrrrrsssssssss\
tttttttttttttttuuuuuvvwwwyyy"

def random_word(*args):
    return "".join(random.sample(WEIGHTED_LETTERS, random.randint(*args)))

lr = 50 if len(sys.argv) < 2 else int(sys.argv[1])

r = redis.Redis("localhost", db="2channel")

t = Thread(
	text = "This thread is a stress test on the loading speeds of the page",
	subject = "Stress Test",
	author = "Admin",
	board = "g")

r.zadd("board:{0}:threads".format(t.board), t.id, t.id) #These are swapped in the py-redis api and not to spec
r.set("thread:{0}".format(t.id), cP.dumps(t, protocol=-1))

for z in xrange(lr):
	xz = Reply(t.id,
		text = random_word(10, 80),
		subject = random_word(0, 15),
		author = random_word(0, 22),
		board = "g")
	
	r.zadd("thread:{0}:replies".format(xz.thread), xz.id, xz.id)
	r.set("reply:{0}".format(xz.id), cP.dumps(xz, protocol=-1))
	
	print "Added Reply %s (%s)"% (xz.id, z)
	sleep(1)
