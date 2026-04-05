def is_integer_string(s):
    """Check if string represents an integer (non-negative)."""
    try:
        val = int(s)
        return val >= 0
    except ValueError:
        return False

def sin_reduction_string(exponent, var):
    """Return a string representing ∫ sin^exponent(var) d(var)
       using the reduction formula."""
    if exponent == 0:
        return var
    elif exponent == 1:
        return f"-cos({var})"
    else:
        # Check if exponent is an integer for recursive expansion
        if isinstance(exponent, int) or (isinstance(exponent, str) and exponent.isdigit()):
            exp_int = int(exponent)
            if exp_int == 0:
                return var
            elif exp_int == 1:
                return f"-cos({var})"
            else:
                # Reduction: ∫ sin^n x dx = - (sin^{n-1}x cos x)/n + (n-1)/n ∫ sin^{n-2} x dx
                term1 = f"-(sin({var})^{exp_int-1} * cos({var}))/{exp_int}"
                term2 = sin_reduction_string(exp_int - 2, var)
                return f"{term1} + ({exp_int-1}/{exp_int}) * ({term2})"
        else:
            # Symbolic exponent (like 'n')
            return f"-(sin({var})^{{{exponent}-1}} * cos({var}))/{exponent} + ({exponent}-1)/{exponent} * ∫ sin({var})^{{{exponent}-2}} d{var}"

def main():
    exp_input = input("Enter exponent (integer or letter like 'n'): ").strip()
    var = input("Enter integration variable (default 'x'): ").strip() or 'x'

    if is_integer_string(exp_input):
        exp_int = int(exp_input)
        result = sin_reduction_string(exp_int, var)
        print(f"\n∫ sin({var})^{exp_int} d{var} = {result} + C")
    else:
        # Symbolic exponent
        print(f"\nGeneral reduction formula for exponent '{exp_input}':")
        result = sin_reduction_string(exp_input, var)
        print(f"∫ sin({var})^{exp_input} d{var} = {result} + C")

if __name__ == "__main__":
    main()