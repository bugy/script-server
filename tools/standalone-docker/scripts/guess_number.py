#!/usr/bin/python3

import random
import sys

max_number = int(sys.argv[1])
if len(sys.argv) > 2 and sys.argv[2]:
	gueses = int(sys.argv[2])
else:
	gueses = 3

gueses_left = 3

number = random.randint(0, max_number)

print('Try to guess a number between 0 and ' + str(max_number) + ' (' + str(gueses_left) + ' tries):')
while gueses_left > 0:
	user_input = input()
	try:
		user_input = int(user_input)
	except:
		print(user_input + ' is not really a number, please try again')

	if user_input == number:
		print('Congratulations, you guessed right!')
		sys.exit(0)
	print('Oops, the wrong choice.', end='')
	gueses_left -= 1
	if gueses_left:
		print('. Try again:')

print('\nTry you luck next time!')

