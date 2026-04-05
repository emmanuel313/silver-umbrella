def is_integer_string(s):
    """Check if string represents an integer (positive or negative)."""
    try:
        int(s)
        return True
    except ValueError:
        return False

def cos_reduction_string(exponent, var):
    """Return a string representing ∫ cos^exponent(var) d(var)
       using the reduction formula.
       exponent can be an integer or a symbolic name (like 'n')."""
    if exponent == 0:
        return var
    elif exponent == 1:
        return f"sin({var})"
    else:
        # Check if exponent is an integer (for recursive reduction)
        if isinstance(exponent, int) or (isinstance(exponent, str) and exponent.isdigit()):
            exp_int = int(exponent)
            if exp_int == 0:
                return var
            elif exp_int == 1:
                return f"sin({var})"
            else:
                # Reduction formula: (cos^{n-1} var * sin var)/n + (n-1)/n ∫ cos^{n-2} var d var
                term1 = f"(cos({var})^{exp_int-1} * sin({var}))/{exp_int}"
                term2 = cos_reduction_string(exp_int - 2, var)
                return f"{term1} + ({exp_int-1}/{exp_int}) * ({term2})"
        else:
            # Symbolic exponent (like 'n')
            return f"(cos({var})^{{{exponent}-1}} * sin({var}))/{exponent} + ({exponent}-1)/{exponent} * ∫ cos({var})^{{{exponent}-2}} d{var}"

def main():
    exp_input = input("Enter exponent (integer or letter like 'n'): ").strip()
    var = input("Enter integration variable (default 'x'): ").strip() or 'x'

    if is_integer_string(exp_input):
        exp_int = int(exp_input)
        if exp_int < 0:
            print("Negative exponents are not supported in this reduction (would involve secant).")
            return
        result = cos_reduction_string(exp_int, var)
        print(f"\n∫ cos({var})^{exp_int} d{var} = {result} + C")
    else:
        # Symbolic exponent
        print(f"\nGeneral reduction formula for exponent '{exp_input}':")
        result = cos_reduction_string(exp_input, var)
        print(f"∫ cos({var})^{exp_input} d{var} = {result} + C")

if __name__ == "__main__":
    main()