from root_falsepos import false_position_method

cases = [
    ("x^3 + 4*x^2 - 10", 1, 2),
    ("sin(x) - 0.5", 0, 1),
    ("x*e**(-x) - 0.1", 0, 1),
    ("x^4 - 10", 1, 2),
]

for func, a, b in cases:
    print("\n--- Testing:", func, f" on [{a}, {b}]")
    try:
        root, logs, iters = false_position_method(func, a, b, tol=1e-8, max_iter=1000)
        print(f"Root: {root} (iters={iters})")
        if logs:
            print("Logs (last 5):")
            for line in logs[-5:]:
                print("  ", line)
    except Exception as e:
        print("Error:", repr(e))

print("\nDone tests.")
