import random

chr = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0987654321"

def gen():
    sid = "".join(random.choice(chr) for i in range(random.randint(55,60)))
    return "s."+sid