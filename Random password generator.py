import random
import string
length = 10
characters = string.ascii_lowercase + string.digits + string.punctuation
password = ''.join(random.choice(characters) for i in range(length))
print("Generated Password:", password)