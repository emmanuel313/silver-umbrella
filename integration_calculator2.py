import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import sys
import sympy as sp
from sympy import Symbol, exp, log, sin, cos, tan, asin, acos, atan
from typing import Tuple, List, Optional, Union
import threading

# Try to import Matplotlib for LaTeX rendering
try:
    import matplotlib
    matplotlib.use('TkAgg')
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# Import LaTeX parser
try:
    from sympy.parsing.latex import parse_latex
except ImportError:
    print("Error: SymPy's LaTeX parser requires the 'antlr4' package.")
    print("Please install it with: pip install antlr4-python3-runtime")
    sys.exit(1)


# ======================================================================
# Core Functions (from integration_by_parts.py)
# ======================================================================

def liate_priority(expr: sp.Expr, var: sp.Symbol) -> int:
    if isinstance(expr, sp.log):
        return 1
    if expr.func in (sp.asin, sp.acos, sp.atan, sp.acsc, sp.asec, sp.acot):
        return 2
    if expr.is_polynomial(var) or (expr.is_Pow and expr.base == var and expr.exp.is_constant()):
        return 3
    if expr.func in (sp.sin, sp.cos, sp.tan, sp.cot, sp.sec, sp.csc):
        return 4
    if isinstance(expr, sp.exp) or (expr.is_Pow and expr.base.is_constant() and expr.exp.has(var)):
        return 5
    return 6


def is_log_or_inverse(expr: sp.Expr, var: sp.Symbol) -> bool:
    return liate_priority(expr, var) in (1, 2)


def split_factors(expr: sp.Expr, var: sp.Symbol) -> Tuple[List[sp.Expr], List[sp.Expr]]:
    if not isinstance(expr, sp.Mul):
        if expr.has(var):
            return [], [expr]
        else:
            return [expr], []
    const = []
    var_f = []
    for arg in expr.args:
        if arg.has(var):
            var_f.append(arg)
        else:
            const.append(arg)
    return const, var_f


def is_exp_trig_product(integrand: sp.Expr, var: sp.Symbol) -> Optional[Tuple[sp.Expr, sp.Expr, sp.Function, sp.Expr]]:
    coeff = sp.Integer(1)
    rest = integrand
    if isinstance(integrand, sp.Mul):
        const_part, var_part = split_factors(integrand, var)
        if const_part:
            coeff = sp.Mul(*const_part)
            if len(var_part) == 1:
                rest = var_part[0]
            else:
                rest = sp.Mul(*var_part)
    else:
        rest = integrand

    exp_part = None
    trig_part = None
    if isinstance(rest, sp.Mul):
        for arg in rest.args:
            if isinstance(arg, sp.exp) or (arg.is_Pow and arg.base.is_constant() and arg.exp.has(var)):
                exp_part = arg
            elif arg.func in (sp.sin, sp.cos):
                trig_part = arg
        if exp_part and trig_part:
            if isinstance(exp_part, sp.exp):
                a = sp.Wild('a', exclude=[var])
                match = exp_part.match(sp.exp(a * var))
                if match:
                    a = match[a]
                else:
                    return None
            else:
                base, exponent = exp_part.as_base_exp()
                if exponent == var:
                    a = sp.log(base)
                else:
                    return None
            b = sp.Wild('b', exclude=[var])
            if trig_part.func == sp.sin:
                match = trig_part.match(sp.sin(b * var))
            else:
                match = trig_part.match(sp.cos(b * var))
            if match:
                b = match[b]
                return (a, b, trig_part.func, coeff)
    return None


def integrate_exp_trig(a: sp.Expr, b: sp.Expr, trig_func: sp.Function, coeff: sp.Expr, var: sp.Symbol) -> sp.Expr:
    denom = a**2 + b**2
    exp_term = sp.exp(a * var)
    if trig_func == sp.sin:
        antideriv = exp_term * (a * sp.sin(b * var) - b * sp.cos(b * var)) / denom
    else:
        antideriv = exp_term * (a * sp.cos(b * var) + b * sp.sin(b * var)) / denom
    return coeff * antideriv


def integrate_by_parts_rec(integrand: sp.Expr, var: sp.Symbol) -> sp.Expr:
    exp_trig = is_exp_trig_product(integrand, var)
    if exp_trig is not None:
        a, b, trig_func, coeff = exp_trig
        return integrate_exp_trig(a, b, trig_func, coeff, var)

    const_factors, var_factors = split_factors(integrand, var)

    if not var_factors:
        return sp.integrate(integrand, var)

    if len(var_factors) == 1:
        expr = var_factors[0]
        if is_log_or_inverse(expr, var):
            u = expr
            dv = sp.Integer(1)
            v = sp.integrate(dv, var)
            du = sp.diff(u, var)
            new_integrand = v * du
            if const_factors:
                new_integrand = sp.Mul(*const_factors) * new_integrand
            return u * v - integrate_by_parts_rec(new_integrand, var)
        else:
            return sp.integrate(integrand, var)

    var_factors_sorted = sorted(var_factors, key=lambda f: liate_priority(f, var))
    u = var_factors_sorted[0]
    dv_factors = var_factors_sorted[1:]
    dv = sp.Mul(*(const_factors + dv_factors))
    v = sp.integrate(dv, var)
    du = sp.diff(u, var)
    new_integrand = v * du
    return u * v - integrate_by_parts_rec(new_integrand, var)


def integrate_by_parts(latex_str: str) -> Tuple[Union[sp.Expr, sp.Float], Optional[sp.Float]]:
    """
    Returns (symbolic_result, numeric_result) where numeric_result is None for indefinite.
    """
    expr = parse_latex(latex_str)
    expr = expr.replace(sp.Symbol('e'), sp.E)

    if not isinstance(expr, sp.Integral):
        raise ValueError("Input does not represent a valid integral")

    limits = expr.limits
    if len(limits) == 0:
        raise ValueError("Integral has no integration variable")
    var = limits[0][0]
    lower = None
    upper = None
    if len(limits[0]) == 3:
        lower, upper = limits[0][1], limits[0][2]
    integrand = expr.function

    antiderivative = integrate_by_parts_rec(integrand, var)
    symbolic_result = sp.simplify(antiderivative)

    if lower is not None and upper is not None:
        # Definite integral
        result_expr = symbolic_result.subs(var, upper) - symbolic_result.subs(var, lower)
        symbolic_result = sp.simplify(result_expr)
        numeric_result = symbolic_result.evalf()
        return symbolic_result, numeric_result
    else:
        # Indefinite integral: factor nicely and return without +C
        symbolic_result = sp.factor(symbolic_result) if symbolic_result.is_polynomial() else sp.simplify(symbolic_result)
        return symbolic_result, None


# ======================================================================
# GUI Application with LaTeX Rendering Add‑On
# ======================================================================

class IntegrationByPartsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Integration by Parts Calculator")
        self.root.geometry("1000x850")
        self.root.configure(bg="#f0f0f0")

        # Configure style
        style = ttk.Style()
        style.theme_use('clam')

        # Main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Title
        title_label = ttk.Label(main_frame, text="Integration by Parts Calculator",
                                font=("Arial", 18, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=10)

        # Input section
        input_frame = ttk.LabelFrame(main_frame, text="Input", padding="10")
        input_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), padx=5, pady=5)

        ttk.Label(input_frame, text="Enter LaTeX integral:", font=("Arial", 10)).grid(row=0, column=0, sticky=tk.W)

        self.input_text = ttk.Entry(input_frame, width=70, font=("Arial", 11))
        self.input_text.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        self.input_text.insert(0, r"\int x \sin(x) dx")

        ttk.Label(input_frame, text="Example: \\int x \\sin(x) dx",
                  font=("Arial", 9), foreground="gray").grid(row=2, column=0, sticky=tk.W)

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=10)

        self.calculate_btn = ttk.Button(button_frame, text="Calculate", command=self.calculate)
        self.calculate_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="Clear", command=self.clear_all).pack(side=tk.LEFT, padx=5)

        # Output section: LaTeX raw code
        output_frame = ttk.LabelFrame(main_frame, text="LaTeX Output", padding="10")
        output_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S),
                          padx=5, pady=5)

        self.symbolic_text = scrolledtext.ScrolledText(output_frame, height=8, width=80,
                                                       font=("Courier", 10))
        self.symbolic_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        # NEW: Rendered Expression section (Matplotlib)
        self.render_frame = ttk.LabelFrame(main_frame, text="Rendered Expression", padding="10")
        self.render_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S),
                               padx=5, pady=5)

        # Initialize Matplotlib canvas if available
        self.matplotlib_available = MATPLOTLIB_AVAILABLE
        self.canvas = None
        self.figure = None
        self.ax = None
        if self.matplotlib_available:
            self.figure = Figure(figsize=(8, 2.5), dpi=100)
            self.ax = self.figure.add_subplot(111)
            self.ax.axis('off')
            self.canvas = FigureCanvasTkAgg(self.figure, master=self.render_frame)
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        else:
            label = ttk.Label(self.render_frame,
                              text="Matplotlib not installed.\nInstall with 'pip install matplotlib' to see rendered expressions.",
                              foreground="red", justify=tk.CENTER)
            label.pack(padx=10, pady=10)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)

        # Configure grid weights for resizing
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        main_frame.rowconfigure(4, weight=1)
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
        self.render_frame.columnconfigure(0, weight=1)
        self.render_frame.rowconfigure(0, weight=1)

    def update_rendered_expression(self, latex_str: str):
        """Render the LaTeX string using Matplotlib's mathtext."""
        if not self.matplotlib_available or self.canvas is None:
            return
        # Clear and redraw
        self.ax.clear()
        self.ax.axis('off')
        # Wrap in math mode for proper rendering
        rendered_latex = f"${latex_str}$"
        self.ax.text(0.5, 0.5, rendered_latex, fontsize=14, ha='center', va='center')
        self.canvas.draw()

    def update_output(self, symbolic: sp.Expr, numeric: Optional[sp.Float], _latex_input: str):
        """Update both the LaTeX code view and the rendered expression."""
        # Generate raw LaTeX
        latex_raw = sp.latex(symbolic)

        # Append +C for indefinite integrals
        if numeric is None:
            display_latex = latex_raw + " + C"
        else:
            display_latex = latex_raw

        # Update raw LaTeX text area
        self.symbolic_text.config(state=tk.NORMAL)
        self.symbolic_text.delete(1.0, tk.END)
        self.symbolic_text.insert(tk.END, display_latex)
        self.symbolic_text.config(state=tk.DISABLED)

        # Update rendered expression
        self.update_rendered_expression(display_latex)

        # Update status and re-enable calculate button
        self.status_var.set("✓ Calculation successful")
        self.calculate_btn.config(state=tk.NORMAL)

    def show_error(self, err_msg: str):
        """Display an error message and re-enable the calculate button."""
        messagebox.showerror("Calculation Error", f"Error: {err_msg}")
        self.status_var.set(f"✗ Error: {err_msg}")
        self.calculate_btn.config(state=tk.NORMAL)

    def calculate(self):
        latex_input = self.input_text.get().strip()
        if not latex_input:
            messagebox.showwarning("Input Error", "Please enter a LaTeX integral")
            return

        # Disable button and update status
        self.calculate_btn.config(state=tk.DISABLED)
        self.status_var.set("Calculating...")
        self.root.update()

        # Run calculation in a separate thread
        thread = threading.Thread(target=self._calculate_thread, args=(latex_input,))
        thread.daemon = True
        thread.start()

    def _calculate_thread(self, latex_input: str):
        try:
            symbolic, numeric = integrate_by_parts(latex_input)
            # Schedule GUI update in the main thread
            self.root.after(0, lambda: self.update_output(symbolic, numeric, latex_input))
        except Exception as e:
            self.root.after(0, lambda: self.show_error(str(e)))

    def clear_all(self):
        self.input_text.delete(0, tk.END)
        self.symbolic_text.config(state=tk.NORMAL)
        self.symbolic_text.delete(1.0, tk.END)
        self.symbolic_text.config(state=tk.DISABLED)
        # Clear the rendered expression
        if self.matplotlib_available and self.ax is not None:
            self.ax.clear()
            self.ax.axis('off')
            self.canvas.draw()
        self.status_var.set("Ready")
        self.input_text.focus()


# ======================================================================
# Main Entry Point
# ======================================================================

if __name__ == "__main__":
    root = tk.Tk()
    app = IntegrationByPartsApp(root)
    root.mainloop()