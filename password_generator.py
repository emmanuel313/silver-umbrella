import secrets
import string
import math
LOWER = string.ascii_lowercase
UPPER = string.ascii_uppercase
DIGITS = string.digits
SYMBOLS = "!@#$%^&*()-_=+[]{}|;:,.<>?/"
AMBIGUOUS = "il1Lo0O"
def remove_ambiguous(pool):
    return ''.join(c for c in pool if c not in AMBIGUOUS)
def calculate_entropy(length, pool_size):
    return round(length * math.log2(pool_size), 2)
def generate_password(
    length=16,
    use_upper=True,
    use_lower=True,
    use_digits=True,
    use_symbols=True,
    exclude_ambiguous=True
):
    if length < 8:
        raise ValueError("Password length should be at least 8 for security.")
    pools = [] 
    if use_lower:
        pools.append(LOWER)
    if use_upper:
        pools.append(UPPER)
    if use_digits:
        pools.append(DIGITS)
    if use_symbols:
        pools.append(SYMBOLS)
    if not pools:
        raise ValueError("At least one character type must be enabled.")
    if exclude_ambiguous:
        pools = [remove_ambiguous(pool) for pool in pools]
    password_chars = [secrets.choice(pool) for pool in pools]
    all_chars = ''.join(pools)
    for _ in range(length - len(password_chars)):
        password_chars.append(secrets.choice(all_chars))
    secrets.SystemRandom().shuffle(password_chars)
    password = ''.join(password_chars)
    entropy = calculate_entropy(length, len(all_chars))
    return password, entropy
if __name__ == "__main__":
    pwd, entropy = generate_password(length=20)
    print("Generated Password:", pwd)
    print("Entropy (bits):", entropy)