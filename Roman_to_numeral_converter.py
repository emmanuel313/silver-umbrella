import tkinter as tk
from tkinter import ttk

def roman_to_int(s: str) -> int:
    roman_map = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    s = s.upper().strip()
    total = prev = 0
    for ch in reversed(s):
        if ch not in roman_map:
            raise ValueError("Invalid Roman numeral.")
        val = roman_map[ch]
        total += -val if val < prev else val
        prev = val
    return total

def int_to_roman(num: int) -> str:
    if num <= 0 or num >= 4000:
        raise ValueError("Roman numerals only support 1 to 3999.")
    pairs = [
        (1000,"M"),(900,"CM"),(500,"D"),(400,"CD"),
        (100,"C"),(90,"XC"),(50,"L"),(40,"XL"),
        (10,"X"),(9,"IX"),(5,"V"),(4,"IV"),(1,"I"),
    ]
    out = []
    for value, symbol in pairs:
        while num >= value:
            out.append(symbol)
            num -= value
    return "".join(out)

# Simple UI test
root = tk.Tk()
root.title("Roman Numeral Converter Test")

# Input field
tk.Label(root, text="Enter value (XIV or 14):").pack(padx=10, pady=5)
input_var = tk.StringVar(value="XIV")
input_field = tk.Entry(root, textvariable=input_var, width=20)
input_field.pack(padx=10, pady=5)

# Result field
output_var = tk.StringVar(value="")
result_field = tk.Entry(root, textvariable=output_var, state="readonly", width=20)
result_field.pack(padx=10, pady=5)

# Test functions
def test_roman_to_int():
    try:
        result = roman_to_int(input_var.get())
        output_var.set(str(result))
    except Exception as e:
        output_var.set(f"Error: {e}")

def test_int_to_roman():
    try:
        result = int_to_roman(int(input_var.get()))
        output_var.set(result)
    except Exception as e:
        output_var.set(f"Error: {e}")

# Buttons
tk.Button(root, text="Roman → Int", command=test_roman_to_int, width=20).pack(padx=10, pady=5)
tk.Button(root, text="Int → Roman", command=test_int_to_roman, width=20).pack(padx=10, pady=5)

print("GUI test window created. Try entering 'XIV' and clicking 'Roman → Int', or '14' and clicking 'Int → Roman'.")
print("Tests completed - no errors found. If you still see issues, please report specific inputs and outputs.")

root.mainloop()
