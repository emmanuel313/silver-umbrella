import sympy as sp
from sympy import Rational, sqrt
def complete_square_text(b, c):
    """Return completed square as a plain string: (x + h)^2 ± (√m / 2)^2"""
    b_r = Rational(b)
    c_r = Rational(c)
    h = b_r / 2                    
    k = c_r - h**2                 
    if h >= 0:
        base = f"(x + {sp.latex(h)})^2"
    else:
        base = f"(x - {sp.latex(-h)})^2"
    if k == 0:
        return base
    abs_k = abs(k)
    radicand = 4 * abs_k
    sqrt_part = sqrt(radicand).simplify()   
    if sqrt_part.is_Integer:
        numerator = sqrt_part
        square_term = f"({numerator}/2)^2"
    else:
        rad_str = str(sqrt_part).replace('sqrt', '√').replace('(', '').replace(')', '')
        square_term = f"({rad_str}/2)^2"

    sign = ' + ' if k > 0 else ' - '
    return base + sign + square_term

if __name__ == "__main__":
    b_input = input("Enter b: ")
    c_input = input("Enter c: ")
    try:
        b = float(b_input) if '.' in b_input else int(b_input)
        c = float(c_input) if '.' in c_input else int(c_input)
        result = complete_square_text(b, c)
        print("\nCompleted square form:")
        print(result)
    except Exception as e:
        print(f"Invalid input: {e}")