
"""
All-in-One Super Calculator
===========================

How to run
----------
1) Save this file as `super_calculator.py`
2) Install dependencies:
   pip install -r requirements.txt
3) Launch:
   python super_calculator.py

README
------
This is a single-file, extensible Tkinter application that bundles:
- Basic calculator
- Scientific calculator
- Advanced numerical calculus tools
- Unit and currency conversion
- Graphing
- Financial calculator
- Programming/base conversion and bitwise tools
- Statistics and utility tools
- History save/load/export

Notes
-----
- Numerical calculus features are implemented with robust numerical methods.
- Currency conversion includes a placeholder API hook and offline sample rates.
- The expression engine is sandboxed via AST and only allows safe operations.
"""

from __future__ import annotations

import ast
import csv
import json
import math
import operator as op
import random
import re
import statistics as stats
import tkinter as tk
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

try:
    from scipy import integrate, optimize, stats as scipy_stats
except Exception:  # pragma: no cover
    integrate = None
    optimize = None
    scipy_stats = None


APP_TITLE = "All-in-One Super Calculator"
DEFAULT_MATH_NAMESPACE = {}
HISTORY_FILE = Path.home() / ".super_calculator_history.json"


def cbrt(x):
    return np.sign(x) * np.abs(x) ** (1 / 3)


def factorial(x):
    x = float(x)
    if x < 0 or int(x) != x:
        raise ValueError("Factorial is defined for non-negative integers only.")
    return math.factorial(int(x))


def safe_div(a, b):
    if np.any(np.asarray(b) == 0):
        raise ZeroDivisionError("Division by zero is not allowed.")
    return a / b


def to_rad(x, degrees_mode: bool):
    return np.deg2rad(x) if degrees_mode else x


def from_rad(x, degrees_mode: bool):
    return np.rad2deg(x) if degrees_mode else x


def build_math_namespace(degrees_mode: bool = False):
    sin = lambda x: np.sin(to_rad(x, degrees_mode))
    cos = lambda x: np.cos(to_rad(x, degrees_mode))
    tan = lambda x: np.tan(to_rad(x, degrees_mode))
    asin = lambda x: from_rad(np.arcsin(x), degrees_mode)
    acos = lambda x: from_rad(np.arccos(x), degrees_mode)
    atan = lambda x: from_rad(np.arctan(x), degrees_mode)
    sinh = np.sinh
    cosh = np.cosh
    tanh = np.tanh
    exp = np.exp
    ln = np.log
    log10 = np.log10
    sqrt = np.sqrt
    pi = math.pi
    e = math.e
    tau = math.tau
    inf = math.inf

    return {
        "sin": sin,
        "cos": cos,
        "tan": tan,
        "asin": asin,
        "acos": acos,
        "atan": atan,
        "sinh": sinh,
        "cosh": cosh,
        "tanh": tanh,
        "log10": log10,
        "ln": ln,
        "log": ln,
        "exp": exp,
        "sqrt": sqrt,
        "cbrt": cbrt,
        "abs": np.abs,
        "floor": np.floor,
        "ceil": np.ceil,
        "round": np.round,
        "pow": np.power,
        "factorial": factorial,
        "fact": factorial,
        "pi": pi,
        "e": e,
        "tau": tau,
        "inf": inf,
        "radians": np.deg2rad,
        "degrees": np.rad2deg,
        "min": np.minimum,
        "max": np.maximum,
        "sum": np.sum,
        "prod": np.prod,
        "mean": np.mean,
        "median": np.median,
    }


SAFE_OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: safe_div,
    ast.Pow: op.pow,
    ast.Mod: op.mod,
    ast.FloorDiv: op.floordiv,
    ast.UAdd: op.pos,
    ast.USub: op.neg,
}


class SafeEvaluator(ast.NodeVisitor):
    def __init__(self, namespace: dict[str, object]):
        self.namespace = namespace

    def visit(self, node):  # type: ignore[override]
        if isinstance(node, ast.Expression):
            return self.visit(node.body)
        return super().visit(node)

    def generic_visit(self, node):
        raise ValueError(f"Unsupported expression element: {type(node).__name__}")

    def visit_Constant(self, node):  # noqa: N802
        if isinstance(node.value, (int, float, complex)):
            return node.value
        raise ValueError("Only numeric constants are allowed.")

    def visit_Name(self, node):  # noqa: N802
        if node.id in self.namespace:
            return self.namespace[node.id]
        raise ValueError(f"Unknown name: {node.id}")

    def visit_BinOp(self, node):  # noqa: N802
        left = self.visit(node.left)
        right = self.visit(node.right)
        op_type = type(node.op)
        if op_type in SAFE_OPERATORS:
            return SAFE_OPERATORS[op_type](left, right)
        raise ValueError(f"Unsupported operator: {op_type.__name__}")

    def visit_UnaryOp(self, node):  # noqa: N802
        operand = self.visit(node.operand)
        op_type = type(node.op)
        if op_type in SAFE_OPERATORS:
            return SAFE_OPERATORS[op_type](operand)
        raise ValueError(f"Unsupported unary operator: {op_type.__name__}")

    def visit_Call(self, node):  # noqa: N802
        func = self.visit(node.func)
        args = [self.visit(arg) for arg in node.args]
        kwargs = {kw.arg: self.visit(kw.value) for kw in node.keywords}
        if callable(func):
            return func(*args, **kwargs)
        raise ValueError("Attempted to call a non-callable object.")


def safe_eval(expression: str, namespace: dict[str, object]) -> object:
    expression = expression.strip()
    if not expression:
        raise ValueError("Enter an expression first.")
    tree = ast.parse(expression, mode="eval")
    return SafeEvaluator(namespace).visit(tree)


def parse_number(value: str) -> float:
    return float(value.strip())


def format_number(value: object) -> str:
    if isinstance(value, np.ndarray):
        if value.size == 1:
            return format_number(value.item())
        return np.array2string(value, precision=10, separator=", ")
    if isinstance(value, (np.floating, float)):
        if np.isnan(value):
            return "NaN"
        if np.isinf(value):
            return "Infinity" if value > 0 else "-Infinity"
        if abs(value - round(value)) < 1e-12:
            return str(int(round(value)))
        return f"{value:.12g}"
    if isinstance(value, (np.integer, int)):
        return str(int(value))
    return str(value)


def roman_to_int(s: str) -> int:
    roman_map = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    s = s.upper().strip()
    total = 0
    prev = 0
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
        (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
        (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
        (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")
    ]
    out = []
    for value, symbol in pairs:
        while num >= value:
            out.append(symbol)
            num -= value
    return "".join(out)


def convert_base(value: str, from_base: int, to_base: int) -> str:
    n = int(value.strip(), from_base)
    if to_base == 10:
        return str(n)
    digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if n == 0:
        return "0"
    sign = "-" if n < 0 else ""
    n = abs(n)
    result = ""
    while n:
        n, rem = divmod(n, to_base)
        result = digits[rem] + result
    return sign + result


def twos_complement(value: int, bits: int) -> str:
    if bits <= 0:
        raise ValueError("Bit width must be positive.")
    mask = (1 << bits) - 1
    return format(value & mask, f"0{bits}b")


def bit_not(value: int, bits: int) -> int:
    return (~value) & ((1 << bits) - 1)


def gcd_lcm(a: int, b: int) -> tuple[int, int]:
    return math.gcd(a, b), abs(a * b) // math.gcd(a, b) if a and b else 0


def prime_check(n: int) -> bool:
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def derivative(expr: str, x0: float, degrees_mode: bool = False, h: float = 1e-6) -> float:
    ns = build_math_namespace(degrees_mode)
    func = lambda x: safe_eval(expr, {**ns, "x": x})
    return float((func(x0 + h) - func(x0 - h)) / (2 * h))


def integral(expr: str, a: float, b: float, degrees_mode: bool = False) -> float:
    ns = build_math_namespace(degrees_mode)
    func = lambda x: safe_eval(expr, {**ns, "x": x})
    if integrate is not None:
        return float(integrate.quad(lambda t: float(func(t)), a, b, limit=200)[0])
    xs = np.linspace(a, b, 10001)
    ys = np.array([func(x) for x in xs], dtype=float)
    return float(np.trapz(ys, xs))


def indefinite_integral(expr: str, x0: float, degrees_mode: bool = False) -> float:
    return integral(expr, 0.0, x0, degrees_mode)


def limit(expr: str, x0: float, direction: str = "both", degrees_mode: bool = False, h: float = 1e-6) -> float:
    ns = build_math_namespace(degrees_mode)
    func = lambda x: safe_eval(expr, {**ns, "x": x})
    if direction == "left":
        return float(func(x0 - h))
    if direction == "right":
        return float(func(x0 + h))
    return float((func(x0 - h) + func(x0 + h)) / 2)


def summation(expr: str, var: str, start: int, end: int, degrees_mode: bool = False) -> float:
    ns = build_math_namespace(degrees_mode)
    total = 0.0
    for i in range(start, end + 1):
        total += float(safe_eval(expr, {**ns, var: i}))
    return total


def product(expr: str, var: str, start: int, end: int, degrees_mode: bool = False) -> float:
    ns = build_math_namespace(degrees_mode)
    total = 1.0
    for i in range(start, end + 1):
        total *= float(safe_eval(expr, {**ns, var: i}))
    return total


def mean(data): return float(np.mean(data))
def median(data): return float(np.median(data))
def mode(data): return stats.mode(data)
def stdev(data): return float(np.std(data, ddof=1))
def variance(data): return float(np.var(data, ddof=1))


def percent_change(old, new):
    return ((new - old) / old) * 100.0


def compound_interest(principal, rate, times_per_year, years):
    return principal * ((1 + rate / times_per_year) ** (times_per_year * years))


def emi(principal, annual_rate, months):
    r = annual_rate / 12 / 100
    if r == 0:
        return principal / months
    return principal * r * (1 + r) ** months / ((1 + r) ** months - 1)


def pv(fv, rate, periods):
    return fv / ((1 + rate) ** periods)


def fv(pv_, rate, periods):
    return pv_ * ((1 + rate) ** periods)


def annuity(payment, rate, periods):
    if rate == 0:
        return payment * periods
    return payment * ((1 - (1 + rate) ** (-periods)) / rate)


def npv(rate, cashflows):
    return sum(cf / ((1 + rate) ** i) for i, cf in enumerate(cashflows))


def irr(cashflows):
    if optimize is not None:
        fn = lambda r: npv(r, cashflows)
        return float(optimize.newton(fn, 0.1))
    guess = 0.1
    for _ in range(100):
        val = npv(guess, cashflows)
        d = sum(-i * cf / ((1 + guess) ** (i + 1)) for i, cf in enumerate(cashflows) if i > 0)
        if abs(d) < 1e-12:
            break
        new_guess = guess - val / d
        if abs(new_guess - guess) < 1e-10:
            return float(new_guess)
        guess = new_guess
    return float(guess)


def bmi(weight_kg, height_m):
    return weight_kg / (height_m ** 2)


def tip_bill(subtotal, tip_percent, split=1):
    total = subtotal * (1 + tip_percent / 100)
    return total, total / split


def random_number(start, end):
    return random.randint(start, end)


def days_between(date1: str, date2: str, fmt: str = "%Y-%m-%d") -> int:
    d1 = datetime.strptime(date1, fmt)
    d2 = datetime.strptime(date2, fmt)
    return abs((d2 - d1).days)


UNIT_CONVERSIONS = {
    "length": {
        "m": 1.0, "km": 1000.0, "cm": 0.01, "mm": 0.001, "mile": 1609.344, "yard": 0.9144, "ft": 0.3048, "in": 0.0254
    },
    "mass": {"kg": 1.0, "g": 0.001, "mg": 1e-6, "lb": 0.45359237, "oz": 0.028349523125},
    "volume": {"l": 1.0, "ml": 0.001, "m3": 1000.0, "gal": 3.785411784, "cup": 0.24},
    "area": {"m2": 1.0, "km2": 1e6, "cm2": 1e-4, "ft2": 0.09290304, "acre": 4046.8564224},
    "speed": {"m/s": 1.0, "km/h": 1/3.6, "mph": 0.44704, "kn": 0.514444},
    "time": {"s": 1.0, "min": 60.0, "h": 3600.0, "day": 86400.0},
    "energy": {"j": 1.0, "kj": 1000.0, "cal": 4.184, "kwh": 3_600_000.0},
    "power": {"w": 1.0, "kw": 1000.0, "hp": 745.699872},
    "pressure": {"pa": 1.0, "kpa": 1000.0, "bar": 100000.0, "atm": 101325.0, "psi": 6894.757293168},
    "data": {"b": 1.0, "kb": 1000.0, "mb": 1_000_000.0, "gb": 1_000_000_000.0, "tb": 1_000_000_000_000.0,
             "kib": 1024.0, "mib": 1024.0**2, "gib": 1024.0**3},
    "angle": {"rad": 1.0, "deg": math.pi / 180.0},
}

TEMP_UNITS = ("c", "f", "k")
SAMPLE_CURRENCY_RATES = {"USD": 1.0, "INR": 83.0, "EUR": 0.92, "GBP": 0.79, "JPY": 155.0}


def convert_units(category: str, value: float, from_unit: str, to_unit: str) -> float:
    category = category.lower()
    from_unit = from_unit.lower()
    to_unit = to_unit.lower()
    if category == "temperature":
        if from_unit == to_unit:
            return value
        c = value if from_unit == "c" else (value - 32) * 5 / 9 if from_unit == "f" else value - 273.15
        if to_unit == "c":
            return c
        if to_unit == "f":
            return c * 9 / 5 + 32
        if to_unit == "k":
            return c + 273.15
        raise ValueError("Unsupported temperature unit.")
    if category == "currency":
        # Placeholder for API-based rates:
        # Replace SAMPLE_CURRENCY_RATES with live data from your chosen FX provider.
        rates = SAMPLE_CURRENCY_RATES
        if from_unit not in rates or to_unit not in rates:
            raise ValueError("Unknown currency code.")
        usd = value / rates[from_unit]
        return usd * rates[to_unit]
    if category not in UNIT_CONVERSIONS:
        raise ValueError("Unknown category.")
    table = UNIT_CONVERSIONS[category]
    if from_unit not in table or to_unit not in table:
        raise ValueError("Unknown unit.")
    base_value = value * table[from_unit]
    return base_value / table[to_unit]


def binomial_pmf(k, n, p):
    return math.comb(n, k) * (p ** k) * ((1 - p) ** (n - k))


def binomial_cdf(k, n, p):
    return sum(binomial_pmf(i, n, p) for i in range(0, k + 1))


def normal_pdf(x, mu, sigma):
    return (1 / (sigma * math.sqrt(2 * math.pi))) * math.exp(-0.5 * ((x - mu) / sigma) ** 2)


def normal_cdf(x, mu, sigma):
    return 0.5 * (1 + math.erf((x - mu) / (sigma * math.sqrt(2))))


@dataclass
class HistoryItem:
    timestamp: str
    category: str
    expression: str
    result: str


class SuperCalculatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1400x900")
        self.minsize(1180, 760)

        self.style = ttk.Style(self)
        self.degrees_mode = tk.BooleanVar(value=False)
        self.dark_mode = tk.BooleanVar(value=True)
        self.memory = 0.0
        self.history: list[HistoryItem] = []

        self._configure_theme()
        self._build_ui()
        self._bind_keys()
        self._load_history_file()
        self._refresh_history_view()
        self._set_status("Ready")

    def _configure_theme(self):
        self._apply_theme()

    def _apply_theme(self):
        bg = "#1e1e1e" if self.dark_mode.get() else "#f4f4f4"
        fg = "#f0f0f0" if self.dark_mode.get() else "#111111"
        self.configure(bg=bg)
        self.style.theme_use("clam")
        self.style.configure(".", background=bg, foreground=fg, fieldbackground="#2b2b2b" if self.dark_mode.get() else "#ffffff")
        self.style.configure("TNotebook", background=bg)
        self.style.configure("TNotebook.Tab", padding=(12, 6))
        self.style.configure("TFrame", background=bg)
        self.style.configure("TLabel", background=bg, foreground=fg)
        self.style.configure("TButton", padding=6)
        self.style.configure("Treeview", rowheight=24)
        self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

    def _build_ui(self):
        topbar = ttk.Frame(self)
        topbar.pack(fill="x", padx=10, pady=(10, 0))

        ttk.Label(topbar, text=APP_TITLE, font=("Segoe UI", 18, "bold")).pack(side="left")
        ttk.Checkbutton(topbar, text="Dark mode", variable=self.dark_mode, command=self._toggle_theme).pack(side="right", padx=8)
        ttk.Checkbutton(topbar, text="Degrees mode", variable=self.degrees_mode, command=self._relabel_angle_hint).pack(side="right", padx=8)

        self.status_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.status_var, anchor="w").pack(fill="x", padx=10, pady=(4, 6))

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.basic_tab = ttk.Frame(self.notebook)
        self.scientific_tab = ttk.Frame(self.notebook)
        self.converter_tab = ttk.Frame(self.notebook)
        self.graph_tab = ttk.Frame(self.notebook)
        self.financial_tab = ttk.Frame(self.notebook)
        self.programming_tab = ttk.Frame(self.notebook)
        self.utilities_tab = ttk.Frame(self.notebook)
        self.history_tab = ttk.Frame(self.notebook)

        for tab, name in [
            (self.basic_tab, "Basic"),
            (self.scientific_tab, "Scientific"),
            (self.converter_tab, "Converter"),
            (self.graph_tab, "Graph"),
            (self.financial_tab, "Financial"),
            (self.programming_tab, "Programming"),
            (self.utilities_tab, "Utilities"),
            (self.history_tab, "History"),
        ]:
            self.notebook.add(tab, text=name)

        self._build_basic_tab()
        self._build_scientific_tab()
        self._build_converter_tab()
        self._build_graph_tab()
        self._build_financial_tab()
        self._build_programming_tab()
        self._build_utilities_tab()
        self._build_history_tab()

    def _bind_keys(self):
        self.bind("<Return>", lambda e: self._evaluate_basic())
        self.bind("<Escape>", lambda e: self._clear_basic())
        self.bind("<Control-l>", lambda e: self._clear_basic())
        self.bind("<Control-z>", lambda e: self._undo_active())
        self.bind("<Control-y>", lambda e: self._redo_active())
        self.bind("<Control-c>", lambda e: self.focus_get().event_generate("<<Copy>>") if self.focus_get() else None)
        self.bind("<Control-v>", lambda e: self.focus_get().event_generate("<<Paste>>") if self.focus_get() else None)

    def _toggle_theme(self):
        self._apply_theme()
        self._set_status(f"Theme switched to {'dark' if self.dark_mode.get() else 'light'} mode.")

    def _set_status(self, text: str):
        self.status_var.set(text)

    def _active_entry(self):
        widget = self.focus_get()
        return widget if isinstance(widget, (tk.Entry, tk.Text)) else None

    def _undo_active(self):
        w = self._active_entry()
        if w and hasattr(w, "edit_undo"):
            try:
                w.edit_undo()
            except tk.TclError:
                pass

    def _redo_active(self):
        w = self._active_entry()
        if w and hasattr(w, "edit_redo"):
            try:
                w.edit_redo()
            except tk.TclError:
                pass

    def _log_history(self, category: str, expression: str, result: str):
        self.history.append(HistoryItem(datetime.now().isoformat(timespec="seconds"), category, expression, result))
        self._refresh_history_view()
        self._save_history_file()

    def _load_history_file(self):
        if HISTORY_FILE.exists():
            try:
                payload = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
                self.history = [HistoryItem(**item) for item in payload]
            except Exception:
                self.history = []

    def _save_history_file(self):
        try:
            HISTORY_FILE.write_text(json.dumps([item.__dict__ for item in self.history], indent=2), encoding="utf-8")
        except Exception:
            pass

    def _refresh_history_view(self):
        if hasattr(self, "history_tree"):
            for row in self.history_tree.get_children():
                self.history_tree.delete(row)
            for item in self.history[-500:]:
                self.history_tree.insert("", "end", values=(item.timestamp, item.category, item.expression, item.result))

    def _insert_basic(self, text: str):
        self.basic_entry.insert(tk.INSERT, text)

    def _clear_basic(self):
        self.basic_entry.delete(0, tk.END)
        self.basic_result_var.set("")
        self._set_status("Cleared.")

    def _evaluate_basic(self):
        expr = self.basic_entry.get().strip()
        try:
            result = safe_eval(expr.replace("^", "**"), build_math_namespace(self.degrees_mode.get()) | {"M": self.memory})
            result_text = format_number(result)
            self.basic_result_var.set(result_text)
            self._set_status("Calculated successfully.")
            self._log_history("Basic", expr, result_text)
        except Exception as exc:
            self.basic_result_var.set("Error")
            self._set_status(f"Error: {exc}")

    def _memory_add(self):
        try:
            val = float(self.basic_result_var.get() or self.basic_entry.get())
            self.memory += val
            self._set_status(f"Memory updated: {self.memory}")
        except Exception as exc:
            messagebox.showerror("Memory", str(exc))

    def _memory_subtract(self):
        try:
            val = float(self.basic_result_var.get() or self.basic_entry.get())
            self.memory -= val
            self._set_status(f"Memory updated: {self.memory}")
        except Exception as exc:
            messagebox.showerror("Memory", str(exc))

    def _memory_recall(self):
        self.basic_entry.insert(tk.INSERT, format_number(self.memory))
        self._set_status("Memory recalled.")

    def _memory_clear(self):
        self.memory = 0.0
        self._set_status("Memory cleared.")

    def _build_basic_tab(self):
        left = ttk.Frame(self.basic_tab)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        right = ttk.Frame(self.basic_tab)
        right.pack(side="right", fill="y")

        ttk.Label(left, text="Expression").pack(anchor="w")
        self.basic_entry = ttk.Entry(left, font=("Consolas", 18))
        self.basic_entry.pack(fill="x", pady=5)
        self.basic_entry.focus_set()

        btnrow = ttk.Frame(left)
        btnrow.pack(fill="x", pady=5)
        for label, cmd in [
            ("MC", self._memory_clear), ("MR", self._memory_recall), ("M+", self._memory_add), ("M-", self._memory_subtract),
            ("C", self._clear_basic), ("=", self._evaluate_basic)
        ]:
            ttk.Button(btnrow, text=label, command=cmd).pack(side="left", padx=3)

        keypad = ttk.Frame(left)
        keypad.pack(fill="both", expand=True, pady=8)

        buttons = [
            ("7", "7"), ("8", "8"), ("9", "9"), ("/", "/"),
            ("4", "4"), ("5", "5"), ("6", "6"), ("*", "*"),
            ("1", "1"), ("2", "2"), ("3", "3"), ("-", "-"),
            ("0", "0"), (".", "."), ("(", "("), (")", ")"),
            ("+", "+"), ("%", "/100"), ("π", "pi"), ("e", "e"),
        ]
        for i, (label, text) in enumerate(buttons):
            r, c = divmod(i, 4)
            ttk.Button(keypad, text=label, command=lambda t=text: self._insert_basic(t)).grid(row=r, column=c, sticky="nsew", padx=4, pady=4)
        for i in range(4):
            keypad.columnconfigure(i, weight=1)
        for i in range(5):
            keypad.rowconfigure(i, weight=1)

        scirow = ttk.Frame(right)
        scirow.pack(fill="y")
        for label, text in [
            ("sin", "sin("), ("cos", "cos("), ("tan", "tan("),
            ("asin", "asin("), ("acos", "acos("), ("atan", "atan("),
            ("sqrt", "sqrt("), ("cbrt", "cbrt("), ("x²", "**2"),
            ("x³", "**3"), ("xʸ", "**"), ("!", "factorial("),
            ("ln", "ln("), ("log10", "log10("), ("exp", "exp("),
        ]:
            ttk.Button(scirow, text=label, width=10, command=lambda t=text: self._insert_basic(t)).pack(fill="x", pady=2)

        self.basic_result_var = tk.StringVar(value="")
        ttk.Label(left, text="Result").pack(anchor="w", pady=(10, 0))
        ttk.Entry(left, textvariable=self.basic_result_var, font=("Consolas", 16), state="readonly").pack(fill="x", pady=5)
        ttk.Label(right, text="Hint: use sqrt(16), sin(30), 5! via factorial(5), and power with **.").pack(fill="x", pady=10)

    def _build_scientific_tab(self):
        frame = ttk.Frame(self.scientific_tab)
        frame.pack(fill="both", expand=True)

        calc = ttk.LabelFrame(frame, text="Advanced calculus")
        calc.pack(side="left", fill="both", expand=True, padx=(0, 8), pady=4)

        row1 = ttk.Frame(calc); row1.pack(fill="x", pady=4)
        ttk.Label(row1, text="f(x)").pack(side="left")
        self.calc_expr = ttk.Entry(row1)
        self.calc_expr.pack(side="left", fill="x", expand=True, padx=5)
        self.calc_expr.insert(0, "sin(x) + x**2")

        row2 = ttk.Frame(calc); row2.pack(fill="x", pady=4)
        ttk.Label(row2, text="x0").pack(side="left")
        self.calc_x0 = ttk.Entry(row2, width=10); self.calc_x0.pack(side="left", padx=5); self.calc_x0.insert(0, "1")
        ttk.Label(row2, text="a").pack(side="left")
        self.calc_a = ttk.Entry(row2, width=10); self.calc_a.pack(side="left", padx=5); self.calc_a.insert(0, "0")
        ttk.Label(row2, text="b").pack(side="left")
        self.calc_b = ttk.Entry(row2, width=10); self.calc_b.pack(side="left", padx=5); self.calc_b.insert(0, "2")

        row3 = ttk.Frame(calc); row3.pack(fill="x", pady=4)
        ttk.Label(row3, text="Variable").pack(side="left")
        self.sum_var = ttk.Entry(row3, width=8); self.sum_var.pack(side="left", padx=5); self.sum_var.insert(0, "n")
        ttk.Label(row3, text="Start").pack(side="left")
        self.sum_start = ttk.Entry(row3, width=8); self.sum_start.pack(side="left", padx=5); self.sum_start.insert(0, "1")
        ttk.Label(row3, text="End").pack(side="left")
        self.sum_end = ttk.Entry(row3, width=8); self.sum_end.pack(side="left", padx=5); self.sum_end.insert(0, "10")

        actions = ttk.Frame(calc); actions.pack(fill="x", pady=8)
        for label, cmd in [
            ("Derivative", self._calc_derivative),
            ("Integral", self._calc_integral),
            ("Indefinite", self._calc_indefinite),
            ("Limit", self._calc_limit),
            ("Summation", self._calc_summation),
            ("Product", self._calc_product),
        ]:
            ttk.Button(actions, text=label, command=cmd).pack(side="left", padx=4)

        self.calc_output = tk.Text(calc, height=16, wrap="word", undo=True)
        self.calc_output.pack(fill="both", expand=True, pady=5)

        stats_frame = ttk.LabelFrame(frame, text="Statistics")
        stats_frame.pack(side="right", fill="y", padx=(8, 0), pady=4)

        self.stats_data = ttk.Entry(stats_frame, width=38)
        self.stats_data.pack(fill="x", padx=5, pady=5)
        self.stats_data.insert(0, "1, 2, 3, 4, 5, 5, 7")

        for label, cmd in [
            ("Mean", self._stat_mean),
            ("Median", self._stat_median),
            ("Mode", self._stat_mode),
            ("Std dev", self._stat_stdev),
            ("Variance", self._stat_var),
            ("Permutations nPr", self._stat_npr),
            ("Combinations nCr", self._stat_ncr),
            ("Binomial PMF", self._stat_binomial_pmf),
            ("Binomial CDF", self._stat_binomial_cdf),
            ("Normal PDF", self._stat_normal_pdf),
            ("Normal CDF", self._stat_normal_cdf),
        ]:
            ttk.Button(stats_frame, text=label, command=cmd).pack(fill="x", padx=5, pady=2)

        ttk.Separator(stats_frame).pack(fill="x", pady=6)
        self.stats_out = tk.Text(stats_frame, height=10, width=38, undo=True)
        self.stats_out.pack(fill="both", expand=True, padx=5, pady=5)

    def _append_calc_output(self, text: str):
        self.calc_output.insert("end", text + "\n")
        self.calc_output.see("end")

    def _calc_derivative(self):
        try:
            val = derivative(self.calc_expr.get(), parse_number(self.calc_x0.get()), self.degrees_mode.get())
            self._append_calc_output(f"Derivative at x0 = {format_number(val)}")
            self._log_history("Scientific", f"d/dx {self.calc_expr.get()} at {self.calc_x0.get()}", format_number(val))
        except Exception as exc:
            self._append_calc_output(f"Error: {exc}")

    def _calc_integral(self):
        try:
            val = integral(self.calc_expr.get(), parse_number(self.calc_a.get()), parse_number(self.calc_b.get()), self.degrees_mode.get())
            self._append_calc_output(f"Definite integral [{self.calc_a.get()}, {self.calc_b.get()}] = {format_number(val)}")
            self._log_history("Scientific", f"∫ {self.calc_expr.get()} dx [{self.calc_a.get()}, {self.calc_b.get()}]", format_number(val))
        except Exception as exc:
            self._append_calc_output(f"Error: {exc}")

    def _calc_indefinite(self):
        try:
            val = indefinite_integral(self.calc_expr.get(), parse_number(self.calc_x0.get()), self.degrees_mode.get())
            self._append_calc_output(f"Numerical antiderivative from 0 to x0 = {format_number(val)}")
        except Exception as exc:
            self._append_calc_output(f"Error: {exc}")

    def _calc_limit(self):
        try:
            val = limit(self.calc_expr.get(), parse_number(self.calc_x0.get()), "both", self.degrees_mode.get())
            self._append_calc_output(f"Limit near x0 = {format_number(val)}")
        except Exception as exc:
            self._append_calc_output(f"Error: {exc}")

    def _calc_summation(self):
        try:
            val = summation(self.calc_expr.get(), self.sum_var.get().strip() or "n", int(self.sum_start.get()), int(self.sum_end.get()), self.degrees_mode.get())
            self._append_calc_output(f"Summation = {format_number(val)}")
        except Exception as exc:
            self._append_calc_output(f"Error: {exc}")

    def _calc_product(self):
        try:
            val = product(self.calc_expr.get(), self.sum_var.get().strip() or "n", int(self.sum_start.get()), int(self.sum_end.get()), self.degrees_mode.get())
            self._append_calc_output(f"Product = {format_number(val)}")
        except Exception as exc:
            self._append_calc_output(f"Error: {exc}")

    def _parse_stats_data(self):
        raw = re.split(r"[,\s]+", self.stats_data.get().strip())
        values = [float(x) for x in raw if x]
        if not values:
            raise ValueError("Enter at least one value.")
        return values

    def _stats_write(self, text: str):
        self.stats_out.insert("end", text + "\n")
        self.stats_out.see("end")

    def _stat_mean(self):
        try:
            self._stats_write(f"Mean: {format_number(mean(self._parse_stats_data()))}")
        except Exception as exc:
            self._stats_write(f"Error: {exc}")

    def _stat_median(self):
        try:
            self._stats_write(f"Median: {format_number(median(self._parse_stats_data()))}")
        except Exception as exc:
            self._stats_write(f"Error: {exc}")

    def _stat_mode(self):
        try:
            vals = self._parse_stats_data()
            self._stats_write(f"Mode: {stats.multimode(vals)}")
        except Exception as exc:
            self._stats_write(f"Error: {exc}")

    def _stat_stdev(self):
        try:
            self._stats_write(f"Std dev: {format_number(stdev(self._parse_stats_data()))}")
        except Exception as exc:
            self._stats_write(f"Error: {exc}")

    def _stat_var(self):
        try:
            self._stats_write(f"Variance: {format_number(variance(self._parse_stats_data()))}")
        except Exception as exc:
            self._stats_write(f"Error: {exc}")

    def _stat_npr(self):
        try:
            n = int(self.n_value.get())
            r = int(self.r_value.get())
            self._stats_write(f"nPr: {math.perm(n, r)}")
        except Exception as exc:
            self._stats_write(f"Error: {exc}")

    def _stat_ncr(self):
        try:
            n = int(self.n_value.get())
            r = int(self.r_value.get())
            self._stats_write(f"nCr: {math.comb(n, r)}")
        except Exception as exc:
            self._stats_write(f"Error: {exc}")

    def _stat_binomial_pmf(self):
        try:
            k = int(self.bin_k.get()); n = int(self.bin_n.get()); p = float(self.bin_p.get())
            self._stats_write(f"Binomial PMF: {format_number(binomial_pmf(k, n, p))}")
        except Exception as exc:
            self._stats_write(f"Error: {exc}")

    def _stat_binomial_cdf(self):
        try:
            k = int(self.bin_k.get()); n = int(self.bin_n.get()); p = float(self.bin_p.get())
            self._stats_write(f"Binomial CDF: {format_number(binomial_cdf(k, n, p))}")
        except Exception as exc:
            self._stats_write(f"Error: {exc}")

    def _stat_normal_pdf(self):
        try:
            x = float(self.norm_x.get()); mu = float(self.norm_mu.get()); sigma = float(self.norm_sigma.get())
            self._stats_write(f"Normal PDF: {format_number(normal_pdf(x, mu, sigma))}")
        except Exception as exc:
            self._stats_write(f"Error: {exc}")

    def _stat_normal_cdf(self):
        try:
            x = float(self.norm_x.get()); mu = float(self.norm_mu.get()); sigma = float(self.norm_sigma.get())
            self._stats_write(f"Normal CDF: {format_number(normal_cdf(x, mu, sigma))}")
        except Exception as exc:
            self._stats_write(f"Error: {exc}")

    def _build_converter_tab(self):
        outer = ttk.Frame(self.converter_tab)
        outer.pack(fill="both", expand=True)

        left = ttk.LabelFrame(outer, text="Unit converter")
        left.pack(side="left", fill="both", expand=True, padx=(0, 8), pady=4)
        right = ttk.LabelFrame(outer, text="Temperature, currency, bases")
        right.pack(side="right", fill="y", padx=(8, 0), pady=4)

        self.unit_category = ttk.Combobox(left, values=list(UNIT_CONVERSIONS.keys()) + ["temperature", "currency"], state="readonly")
        self.unit_category.set("length")
        self.unit_category.pack(fill="x", padx=5, pady=4)
        self.unit_value = ttk.Entry(left)
        self.unit_value.pack(fill="x", padx=5, pady=4)
        self.unit_value.insert(0, "1")
        self.unit_from = ttk.Entry(left)
        self.unit_from.pack(fill="x", padx=5, pady=4)
        self.unit_from.insert(0, "m")
        self.unit_to = ttk.Entry(left)
        self.unit_to.pack(fill="x", padx=5, pady=4)
        self.unit_to.insert(0, "km")
        ttk.Button(left, text="Convert", command=self._convert_units).pack(pady=4)
        self.unit_result = tk.StringVar(value="")
        ttk.Entry(left, textvariable=self.unit_result, state="readonly").pack(fill="x", padx=5, pady=4)
        ttk.Label(left, text="Examples: length m→km, mass kg→lb, speed m/s→km/h, angle deg→rad").pack(anchor="w", padx=5)

        self.currency_from = ttk.Entry(right); self.currency_from.pack(fill="x", padx=5, pady=4); self.currency_from.insert(0, "USD")
        self.currency_to = ttk.Entry(right); self.currency_to.pack(fill="x", padx=5, pady=4); self.currency_to.insert(0, "INR")
        self.currency_amount = ttk.Entry(right); self.currency_amount.pack(fill="x", padx=5, pady=4); self.currency_amount.insert(0, "100")
        ttk.Button(right, text="Convert currency", command=self._convert_currency).pack(fill="x", padx=5, pady=4)
        self.currency_result = tk.StringVar(value="Placeholder offline rates loaded.")
        ttk.Entry(right, textvariable=self.currency_result, state="readonly").pack(fill="x", padx=5, pady=4)

        sep = ttk.Separator(right); sep.pack(fill="x", pady=8)
        ttk.Label(right, text="Base conversions").pack(anchor="w", padx=5)
        self.base_value = ttk.Entry(right); self.base_value.pack(fill="x", padx=5, pady=4); self.base_value.insert(0, "255")
        self.base_from = ttk.Entry(right); self.base_from.pack(fill="x", padx=5, pady=4); self.base_from.insert(0, "10")
        self.base_to = ttk.Entry(right); self.base_to.pack(fill="x", padx=5, pady=4); self.base_to.insert(0, "16")
        ttk.Button(right, text="Convert base", command=self._convert_base_ui).pack(fill="x", padx=5, pady=4)
        self.base_result = tk.StringVar()
        ttk.Entry(right, textvariable=self.base_result, state="readonly").pack(fill="x", padx=5, pady=4)

        ttk.Separator(right).pack(fill="x", pady=8)
        self.roman_value = ttk.Entry(right); self.roman_value.pack(fill="x", padx=5, pady=4); self.roman_value.insert(0, "XIV")
        ttk.Button(right, text="Roman → Int", command=self._roman_to_int_ui).pack(fill="x", padx=5, pady=2)
        ttk.Button(right, text="Int → Roman", command=self._int_to_roman_ui).pack(fill="x", padx=5, pady=2)
        self.roman_result = tk.StringVar()
        ttk.Entry(right, textvariable=self.roman_result, state="readonly").pack(fill="x", padx=5, pady=4)

    def _convert_units(self):
        try:
            cat = self.unit_category.get()
            val = float(self.unit_value.get())
            result = convert_units(cat, val, self.unit_from.get(), self.unit_to.get())
            self.unit_result.set(format_number(result))
        except Exception as exc:
            self.unit_result.set(f"Error: {exc}")

    def _convert_currency(self):
        try:
            result = convert_units("currency", float(self.currency_amount.get()), self.currency_from.get().upper(), self.currency_to.get().upper())
            self.currency_result.set(format_number(result))
        except Exception as exc:
            self.currency_result.set(f"Error: {exc}")

    def _convert_base_ui(self):
        try:
            self.base_result.set(convert_base(self.base_value.get(), int(self.base_from.get()), int(self.base_to.get())))
        except Exception as exc:
            self.base_result.set(f"Error: {exc}")

    def _roman_to_int_ui(self):
        try:
            self.roman_result.set(str(roman_to_int(self.roman_value.get())))
        except Exception as exc:
            self.roman_result.set(f"Error: {exc}")

    def _int_to_roman_ui(self):
        try:
            self.roman_result.set(int_to_roman(int(self.roman_value.get())))
        except Exception as exc:
            self.roman_result.set(f"Error: {exc}")

    def _build_graph_tab(self):
        top = ttk.Frame(self.graph_tab)
        top.pack(fill="x", pady=4)
        ttk.Label(top, text="f(x)").pack(side="left")
        self.graph_expr = ttk.Entry(top)
        self.graph_expr.pack(side="left", fill="x", expand=True, padx=5)
        self.graph_expr.insert(0, "sin(x)")
        ttk.Label(top, text="x min").pack(side="left")
        self.graph_xmin = ttk.Entry(top, width=8); self.graph_xmin.pack(side="left", padx=4); self.graph_xmin.insert(0, "-10")
        ttk.Label(top, text="x max").pack(side="left")
        self.graph_xmax = ttk.Entry(top, width=8); self.graph_xmax.pack(side="left", padx=4); self.graph_xmax.insert(0, "10")
        ttk.Button(top, text="Plot", command=self._plot_graph).pack(side="left", padx=4)
        ttk.Button(top, text="Save PNG", command=self._save_graph_png).pack(side="left", padx=4)

        self.fig = Figure(figsize=(8, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title("Graph")
        self.ax.grid(True, alpha=0.3)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_tab)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill="both", expand=True)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.graph_tab)
        self.toolbar.update()

    def _plot_graph(self):
        try:
            expr = self.graph_expr.get()
            xmin = float(self.graph_xmin.get())
            xmax = float(self.graph_xmax.get())
            xs = np.linspace(xmin, xmax, 1000)
            ns = build_math_namespace(self.degrees_mode.get())
            ys = np.array([safe_eval(expr, {**ns, "x": x}) for x in xs], dtype=float)
            self.ax.clear()
            self.ax.plot(xs, ys)
            self.ax.set_title(f"f(x) = {expr}")
            self.ax.grid(True, alpha=0.3)
            self.canvas.draw()
            self._set_status("Graph plotted.")
            self._log_history("Graph", expr, f"[{xmin}, {xmax}]")
        except Exception as exc:
            messagebox.showerror("Graph", str(exc))

    def _save_graph_png(self):
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG image", "*.png")])
        if path:
            self.fig.savefig(path, bbox_inches="tight")
            self._set_status(f"Graph saved to {path}")

    def _build_financial_tab(self):
        outer = ttk.Frame(self.financial_tab)
        outer.pack(fill="both", expand=True)

        left = ttk.LabelFrame(outer, text="Core finance")
        left.pack(side="left", fill="both", expand=True, padx=(0, 8), pady=4)
        right = ttk.LabelFrame(outer, text="Loans and time value")
        right.pack(side="right", fill="y", padx=(8, 0), pady=4)

        self.fin_principal = ttk.Entry(left); self.fin_principal.pack(fill="x", padx=5, pady=4); self.fin_principal.insert(0, "10000")
        self.fin_rate = ttk.Entry(left); self.fin_rate.pack(fill="x", padx=5, pady=4); self.fin_rate.insert(0, "8")
        self.fin_years = ttk.Entry(left); self.fin_years.pack(fill="x", padx=5, pady=4); self.fin_years.insert(0, "5")
        self.fin_months = ttk.Entry(left); self.fin_months.pack(fill="x", padx=5, pady=4); self.fin_months.insert(0, "60")
        self.fin_periods = ttk.Entry(left); self.fin_periods.pack(fill="x", padx=5, pady=4); self.fin_periods.insert(0, "12")
        self.fin_cashflows = ttk.Entry(left); self.fin_cashflows.pack(fill="x", padx=5, pady=4); self.fin_cashflows.insert(0, "-1000, 300, 400, 500")

        for label, cmd in [
            ("Compound interest", self._finance_compound),
            ("EMI", self._finance_emi),
            ("NPV", self._finance_npv),
            ("IRR", self._finance_irr),
            ("Future value", self._finance_fv),
            ("Present value", self._finance_pv),
            ("Annuity", self._finance_annuity),
        ]:
            ttk.Button(left, text=label, command=cmd).pack(fill="x", padx=5, pady=2)

        self.finance_out = tk.Text(left, height=14, undo=True)
        self.finance_out.pack(fill="both", expand=True, padx=5, pady=5)

        self.loan_amount = ttk.Entry(right); self.loan_amount.pack(fill="x", padx=5, pady=4); self.loan_amount.insert(0, "500000")
        self.loan_rate = ttk.Entry(right); self.loan_rate.pack(fill="x", padx=5, pady=4); self.loan_rate.insert(0, "10")
        self.loan_months = ttk.Entry(right); self.loan_months.pack(fill="x", padx=5, pady=4); self.loan_months.insert(0, "240")
        ttk.Button(right, text="Amortization schedule", command=self._finance_amortization).pack(fill="x", padx=5, pady=4)
        self.amort_out = tk.Text(right, height=20, width=45, undo=True)
        self.amort_out.pack(fill="both", expand=True, padx=5, pady=5)

    def _finance_write(self, text: str):
        self.finance_out.insert("end", text + "\n")
        self.finance_out.see("end")

    def _finance_compound(self):
        try:
            p = float(self.fin_principal.get())
            r = float(self.fin_rate.get())
            y = float(self.fin_years.get())
            n = int(self.fin_periods.get())
            self._finance_write(f"Compound amount: {format_number(compound_interest(p, r, n, y))}")
        except Exception as exc:
            self._finance_write(f"Error: {exc}")

    def _finance_emi(self):
        try:
            p = float(self.fin_principal.get())
            r = float(self.fin_rate.get())
            m = int(self.fin_months.get())
            self._finance_write(f"EMI: {format_number(emi(p, r, m))}")
        except Exception as exc:
            self._finance_write(f"Error: {exc}")

    def _finance_npv(self):
        try:
            rate = float(self.fin_rate.get()) / 100
            cashflows = [float(x.strip()) for x in self.fin_cashflows.get().split(",")]
            self._finance_write(f"NPV: {format_number(npv(rate, cashflows))}")
        except Exception as exc:
            self._finance_write(f"Error: {exc}")

    def _finance_irr(self):
        try:
            cashflows = [float(x.strip()) for x in self.fin_cashflows.get().split(",")]
            self._finance_write(f"IRR: {format_number(irr(cashflows) * 100)}%")
        except Exception as exc:
            self._finance_write(f"Error: {exc}")

    def _finance_fv(self):
        try:
            p = float(self.fin_principal.get())
            r = float(self.fin_rate.get()) / 100
            y = float(self.fin_years.get())
            self._finance_write(f"Future value: {format_number(fv(p, r, y))}")
        except Exception as exc:
            self._finance_write(f"Error: {exc}")

    def _finance_pv(self):
        try:
            amount = float(self.fin_principal.get())
            r = float(self.fin_rate.get()) / 100
            y = float(self.fin_years.get())
            self._finance_write(f"Present value: {format_number(pv(amount, r, y))}")
        except Exception as exc:
            self._finance_write(f"Error: {exc}")

    def _finance_annuity(self):
        try:
            payment = float(self.fin_principal.get())
            r = float(self.fin_rate.get()) / 100
            y = float(self.fin_years.get())
            self._finance_write(f"Annuity future value: {format_number(annuity(payment, r, y))}")
        except Exception as exc:
            self._finance_write(f"Error: {exc}")

    def _finance_amortization(self):
        try:
            p = float(self.loan_amount.get())
            annual_rate = float(self.loan_rate.get()) / 100
            months = int(self.loan_months.get())
            r = annual_rate / 12
            payment = emi(p, annual_rate * 100, months)
            balance = p
            self.amort_out.delete("1.0", "end")
            self.amort_out.insert("end", "Month | Payment | Interest | Principal | Balance\n")
            self.amort_out.insert("end", "-" * 58 + "\n")
            for m in range(1, months + 1):
                interest = balance * r
                principal_paid = payment - interest
                balance = max(0.0, balance - principal_paid)
                self.amort_out.insert("end", f"{m:>5} | {payment:>8.2f} | {interest:>8.2f} | {principal_paid:>9.2f} | {balance:>8.2f}\n")
                if m >= 60:
                    self.amort_out.insert("end", "Schedule truncated to first 60 months.\n")
                    break
        except Exception as exc:
            messagebox.showerror("Amortization", str(exc))

    def _build_programming_tab(self):
        outer = ttk.Frame(self.programming_tab)
        outer.pack(fill="both", expand=True)

        left = ttk.LabelFrame(outer, text="Base and bitwise")
        left.pack(side="left", fill="both", expand=True, padx=(0, 8), pady=4)
        right = ttk.LabelFrame(outer, text="Bit operations")
        right.pack(side="right", fill="y", padx=(8, 0), pady=4)

        self.prog_value = ttk.Entry(left); self.prog_value.pack(fill="x", padx=5, pady=4); self.prog_value.insert(0, "255")
        self.prog_bits = ttk.Entry(left); self.prog_bits.pack(fill="x", padx=5, pady=4); self.prog_bits.insert(0, "8")
        ttk.Button(left, text="Show binary/octal/hex", command=self._prog_show_bases).pack(fill="x", padx=5, pady=4)
        self.prog_out = tk.Text(left, height=12, undo=True)
        self.prog_out.pack(fill="both", expand=True, padx=5, pady=5)

        self.bit_a = ttk.Entry(right); self.bit_a.pack(fill="x", padx=5, pady=4); self.bit_a.insert(0, "12")
        self.bit_b = ttk.Entry(right); self.bit_b.pack(fill="x", padx=5, pady=4); self.bit_b.insert(0, "5")
        self.bit_shift = ttk.Entry(right); self.bit_shift.pack(fill="x", padx=5, pady=4); self.bit_shift.insert(0, "2")
        for label, cmd in [
            ("AND", self._bit_and), ("OR", self._bit_or), ("XOR", self._bit_xor), ("NOT A", self._bit_not),
            ("A << shift", self._bit_lshift), ("A >> shift", self._bit_rshift), ("Two's complement", self._bit_twos),
        ]:
            ttk.Button(right, text=label, command=cmd).pack(fill="x", padx=5, pady=2)
        self.bit_out = tk.Text(right, height=12, width=36, undo=True)
        self.bit_out.pack(fill="both", expand=True, padx=5, pady=5)

    def _prog_write(self, text: str):
        self.prog_out.insert("end", text + "\n")
        self.prog_out.see("end")

    def _bit_write(self, text: str):
        self.bit_out.insert("end", text + "\n")
        self.bit_out.see("end")

    def _prog_show_bases(self):
        try:
            n = int(self.prog_value.get())
            bits = int(self.prog_bits.get())
            self._prog_write(f"Decimal: {n}")
            self._prog_write(f"Binary: {bin(n)}")
            self._prog_write(f"Octal: {oct(n)}")
            self._prog_write(f"Hex: {hex(n)}")
            self._prog_write(f"Two's complement ({bits} bits): {twos_complement(n, bits)}")
        except Exception as exc:
            self._prog_write(f"Error: {exc}")

    def _bit_values(self):
        return int(self.bit_a.get()), int(self.bit_b.get()), int(self.bit_shift.get())

    def _bit_and(self):
        try:
            a, b, _ = self._bit_values()
            self._bit_write(f"A AND B = {a & b}")
        except Exception as exc:
            self._bit_write(f"Error: {exc}")

    def _bit_or(self):
        try:
            a, b, _ = self._bit_values()
            self._bit_write(f"A OR B = {a | b}")
        except Exception as exc:
            self._bit_write(f"Error: {exc}")

    def _bit_xor(self):
        try:
            a, b, _ = self._bit_values()
            self._bit_write(f"A XOR B = {a ^ b}")
        except Exception as exc:
            self._bit_write(f"Error: {exc}")

    def _bit_not(self):
        try:
            a, _, _ = self._bit_values()
            bits = int(self.prog_bits.get())
            self._bit_write(f"NOT A ({bits} bits) = {bit_not(a, bits)}")
        except Exception as exc:
            self._bit_write(f"Error: {exc}")

    def _bit_lshift(self):
        try:
            a, _, s = self._bit_values()
            self._bit_write(f"A << {s} = {a << s}")
        except Exception as exc:
            self._bit_write(f"Error: {exc}")

    def _bit_rshift(self):
        try:
            a, _, s = self._bit_values()
            self._bit_write(f"A >> {s} = {a >> s}")
        except Exception as exc:
            self._bit_write(f"Error: {exc}")

    def _bit_twos(self):
        try:
            a, _, _ = self._bit_values()
            bits = int(self.prog_bits.get())
            self._bit_write(f"Two's complement = {twos_complement(a, bits)}")
        except Exception as exc:
            self._bit_write(f"Error: {exc}")

    def _build_utilities_tab(self):
        outer = ttk.Frame(self.utilities_tab)
        outer.pack(fill="both", expand=True)

        left = ttk.LabelFrame(outer, text="Math and utility tools")
        left.pack(side="left", fill="both", expand=True, padx=(0, 8), pady=4)
        right = ttk.LabelFrame(outer, text="Dates, BMI, tip, random")
        right.pack(side="right", fill="y", padx=(8, 0), pady=4)

        self.n_value = ttk.Entry(left); self.n_value.pack(fill="x", padx=5, pady=4); self.n_value.insert(0, "10")
        self.r_value = ttk.Entry(left); self.r_value.pack(fill="x", padx=5, pady=4); self.r_value.insert(0, "3")
        self.rng_a = ttk.Entry(left); self.rng_a.pack(fill="x", padx=5, pady=4); self.rng_a.insert(0, "1")
        self.rng_b = ttk.Entry(left); self.rng_b.pack(fill="x", padx=5, pady=4); self.rng_b.insert(0, "100")

        for label, cmd in [
            ("Prime check", self._util_prime),
            ("GCD/LCM", self._util_gcd_lcm),
            ("Random number", self._util_random),
        ]:
            ttk.Button(left, text=label, command=cmd).pack(fill="x", padx=5, pady=2)

        self.util_out = tk.Text(left, height=16, undo=True)
        self.util_out.pack(fill="both", expand=True, padx=5, pady=5)

        self.bmi_weight = ttk.Entry(right); self.bmi_weight.pack(fill="x", padx=5, pady=4); self.bmi_weight.insert(0, "70")
        self.bmi_height = ttk.Entry(right); self.bmi_height.pack(fill="x", padx=5, pady=4); self.bmi_height.insert(0, "1.75")
        ttk.Button(right, text="BMI", command=self._util_bmi).pack(fill="x", padx=5, pady=2)

        self.tip_subtotal = ttk.Entry(right); self.tip_subtotal.pack(fill="x", padx=5, pady=4); self.tip_subtotal.insert(0, "500")
        self.tip_percent = ttk.Entry(right); self.tip_percent.pack(fill="x", padx=5, pady=4); self.tip_percent.insert(0, "10")
        self.tip_split = ttk.Entry(right); self.tip_split.pack(fill="x", padx=5, pady=4); self.tip_split.insert(0, "2")
        ttk.Button(right, text="Tip calculator", command=self._util_tip).pack(fill="x", padx=5, pady=2)

        self.date1 = ttk.Entry(right); self.date1.pack(fill="x", padx=5, pady=4); self.date1.insert(0, "2026-01-01")
        self.date2 = ttk.Entry(right); self.date2.pack(fill="x", padx=5, pady=4); self.date2.insert(0, "2026-12-31")
        ttk.Button(right, text="Days between", command=self._util_days).pack(fill="x", padx=5, pady=2)

        self.util_result = tk.StringVar()
        ttk.Entry(right, textvariable=self.util_result, state="readonly").pack(fill="x", padx=5, pady=4)

    def _util_write(self, text: str):
        self.util_out.insert("end", text + "\n")
        self.util_out.see("end")

    def _util_prime(self):
        try:
            n = int(self.prog_value.get())
            self._util_write(f"{n} is {'prime' if prime_check(n) else 'not prime'}.")
        except Exception as exc:
            self._util_write(f"Error: {exc}")

    def _util_gcd_lcm(self):
        try:
            a = int(self.bit_a.get()); b = int(self.bit_b.get())
            g, l = gcd_lcm(a, b)
            self._util_write(f"GCD: {g}, LCM: {l}")
        except Exception as exc:
            self._util_write(f"Error: {exc}")

    def _util_random(self):
        try:
            a = int(self.rng_a.get()); b = int(self.rng_b.get())
            self._util_write(f"Random number: {random_number(a, b)}")
        except Exception as exc:
            self._util_write(f"Error: {exc}")

    def _util_bmi(self):
        try:
            result = bmi(float(self.bmi_weight.get()), float(self.bmi_height.get()))
            self.util_result.set(f"BMI: {format_number(result)}")
        except Exception as exc:
            self.util_result.set(f"Error: {exc}")

    def _util_tip(self):
        try:
            total, per = tip_bill(float(self.tip_subtotal.get()), float(self.tip_percent.get()), int(self.tip_split.get()))
            self.util_result.set(f"Total: {format_number(total)} | Per person: {format_number(per)}")
        except Exception as exc:
            self.util_result.set(f"Error: {exc}")

    def _util_days(self):
        try:
            days = days_between(self.date1.get(), self.date2.get())
            self.util_result.set(f"Days between: {days}")
        except Exception as exc:
            self.util_result.set(f"Error: {exc}")

    def _build_history_tab(self):
        top = ttk.Frame(self.history_tab)
        top.pack(fill="x", pady=4)
        ttk.Button(top, text="Save JSON", command=self._export_history_json).pack(side="left", padx=4)
        ttk.Button(top, text="Export CSV", command=self._export_history_csv).pack(side="left", padx=4)
        ttk.Button(top, text="Load JSON", command=self._import_history_json).pack(side="left", padx=4)
        ttk.Button(top, text="Clear history", command=self._clear_history).pack(side="left", padx=4)

        cols = ("timestamp", "category", "expression", "result")
        self.history_tree = ttk.Treeview(self.history_tab, columns=cols, show="headings")
        for col in cols:
            self.history_tree.heading(col, text=col.title())
            self.history_tree.column(col, width=220 if col != "expression" else 420, anchor="w")
        self.history_tree.pack(fill="both", expand=True, padx=4, pady=4)

    def _export_history_json(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not path:
            return
        data = [item.__dict__ for item in self.history]
        Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")
        self._set_status(f"History exported to {path}")

    def _export_history_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["timestamp", "category", "expression", "result"])
            writer.writeheader()
            writer.writerows([item.__dict__ for item in self.history])
        self._set_status(f"History exported to {path}")

    def _import_history_json(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            payload = json.loads(Path(path).read_text(encoding="utf-8"))
            self.history = [HistoryItem(**item) for item in payload]
            self._refresh_history_view()
            self._save_history_file()
            self._set_status(f"History loaded from {path}")
        except Exception as exc:
            messagebox.showerror("History", str(exc))

    def _clear_history(self):
        self.history.clear()
        self._refresh_history_view()
        self._save_history_file()
        self._set_status("History cleared.")

    def _relabel_angle_hint(self):
        mode = "degrees" if self.degrees_mode.get() else "radians"
        self._set_status(f"Angle mode set to {mode}.")

    # Hook stats widgets defined late
    @property
    def n_value(self): return self._n_value
    @n_value.setter
    def n_value(self, widget): self._n_value = widget

    @property
    def r_value(self): return self._r_value
    @r_value.setter
    def r_value(self, widget): self._r_value = widget

    @property
    def bin_k(self):
        if not hasattr(self, "_bin_k"):
            self._create_stats_side_inputs()
        return self._bin_k

    @property
    def bin_n(self):
        if not hasattr(self, "_bin_n"):
            self._create_stats_side_inputs()
        return self._bin_n

    @property
    def bin_p(self):
        if not hasattr(self, "_bin_p"):
            self._create_stats_side_inputs()
        return self._bin_p

    @property
    def norm_x(self):
        if not hasattr(self, "_norm_x"):
            self._create_stats_side_inputs()
        return self._norm_x

    @property
    def norm_mu(self):
        if not hasattr(self, "_norm_mu"):
            self._create_stats_side_inputs()
        return self._norm_mu

    @property
    def norm_sigma(self):
        if not hasattr(self, "_norm_sigma"):
            self._create_stats_side_inputs()
        return self._norm_sigma

    def _create_stats_side_inputs(self):
        # Attach to statistics tab after widgets exist
        host = self.scientific_tab
        # Reuse a hidden frame on the right stats panel if not present
        # These are created lazily and placed at the end of the frame.
        stats_frame = self.scientific_tab.winfo_children()[0].winfo_children()[1]
        if hasattr(self, "_bin_k"):
            return
        inputs = ttk.LabelFrame(stats_frame, text="Distribution params")
        inputs.pack(fill="x", padx=5, pady=5)
        ttk.Label(inputs, text="n").pack(anchor="w"); self._bin_n = ttk.Entry(inputs); self._bin_n.pack(fill="x"); self._bin_n.insert(0, "10")
        ttk.Label(inputs, text="k").pack(anchor="w"); self._bin_k = ttk.Entry(inputs); self._bin_k.pack(fill="x"); self._bin_k.insert(0, "3")
        ttk.Label(inputs, text="p").pack(anchor="w"); self._bin_p = ttk.Entry(inputs); self._bin_p.pack(fill="x"); self._bin_p.insert(0, "0.5")
        ttk.Label(inputs, text="Normal x").pack(anchor="w"); self._norm_x = ttk.Entry(inputs); self._norm_x.pack(fill="x"); self._norm_x.insert(0, "1")
        ttk.Label(inputs, text="μ").pack(anchor="w"); self._norm_mu = ttk.Entry(inputs); self._norm_mu.pack(fill="x"); self._norm_mu.insert(0, "0")
        ttk.Label(inputs, text="σ").pack(anchor="w"); self._norm_sigma = ttk.Entry(inputs); self._norm_sigma.pack(fill="x"); self._norm_sigma.insert(0, "1")

    def run(self):
        self.mainloop()


def main():
    app = SuperCalculatorApp()
    app.run()


if __name__ == "__main__":
    main()
