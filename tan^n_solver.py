def is_nonneg_integer(s):
    """Check if string represents a non‑negative integer."""
    try:
        return int(s) >= 0
    except ValueError:
        return False

def tan_reduction_string(exponent, var):
    """Return a string representing ∫ tan^exponent(var) d(var)
       using the reduction formula.
       exponent can be an integer or a symbolic name (like 'n')."""
    if exponent == 0:
        return var
    elif exponent == 1:
        return f"∫ tan({var}) d{var}"          # Keep as unevaluated integral
    else:
        # Check if exponent is an integer for recursive expansion
        if isinstance(exponent, int) or (isinstance(exponent, str) and exponent.isdigit()):
            exp_int = int(exponent)
            if exp_int == 0:
                return var
            elif exp_int == 1:
                return f"∫ tan({var}) d{var}"
            else:
                # ∫ tan^n x dx = tan^{n-1}x/(n-1) - ∫ tan^{n-2}x dx
                term1 = f"tan({var})^{exp_int-1} / {exp_int-1}"
                term2 = tan_reduction_string(exp_int - 2, var)
                return f"{term1} - ({term2})"
        else:
            # Symbolic exponent (like 'n')
            return f"tan({var})^{{{exponent}-1}} / ({exponent}-1) - ∫ tan({var})^{{{exponent}-2}} d{var}"

def main():
    exp_input = input("Enter exponent (integer ≥ 0 or letter like 'n'): ").strip()
    var = input("Enter integration variable (default 'x'): ").strip() or 'x'

    if is_nonneg_integer(exp_input):
        exp_int = int(exp_input)
        if exp_int == 0:
            print(f"\n∫ 1 d{var} = {var} + C")
        elif exp_int == 1:
            print(f"\n∫ tan({var}) d{var} = ∫ tan({var}) d{var} + C   (cannot be expressed without logs)")
        else:
            result = tan_reduction_string(exp_int, var)
            print(f"\n∫ tan({var})^{exp_int} d{var} = {result} + C")
    else:
        # Symbolic exponent
        print(f"\nGeneral reduction formula for exponent '{exp_input}':")
        result = tan_reduction_string(exp_input, var)
        print(f"∫ tan({var})^{exp_input} d{var} = {result} + C")

if __name__ == "__main__":
    main()