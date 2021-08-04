#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from GEBot import GEBot
from Helper.JaroWinklerDistance import JaroWinklerDistance

# Q1
ques = u"Bạn của bạn là ai"
question, answer, score = GEBot().ask(ques)

print ("You asked: ", ques)
print ("Bot understood: ", question, "(", score, "points )")
print ("Bot answered: ")
sys.stdout.buffer.write(answer)
print("\n")

# Q2
ques = u"Ai là bạn của bạn"
question, answer, score = GEBot().ask(ques)

print ("You asked: ", ques)
print ("Bot understood: ", question, "(", score, "points )")
print ("Bot answered: ")
sys.stdout.buffer.write(answer)
print("\n")

# Q3
ques = u"you"
question, answer, score = GEBot().ask(ques)

print ("You asked: ", ques)
print ("Bot understood: ", question, "(", score, "points )")
print ("Bot answered: ")
sys.stdout.buffer.write(answer)
print("\n")

# Q4
ques = u"Bạn có độc thân không"
question, answer, score = GEBot().ask(ques)

print ("You asked: ", ques)
print ("Bot understood: ", question, "(", score, "points )")
print ("Bot answered: ")
sys.stdout.buffer.write(answer)
print("\n")

# Q5
ques = u"Nghe nói bạn vẫn một mình à"
question, answer, score = GEBot().ask(ques)

print ("You asked: ", ques)
print ("Bot understood: ", question, "(", score, "points )")
print ("Bot answered: ")
sys.stdout.buffer.write(answer)
print("\n")
