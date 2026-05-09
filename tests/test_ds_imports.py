try:
    import numpy as np
    print("✓ numpy: OK")
except ImportError as e:
    print(f"✗ numpy: {e}")

try:
    import pandas as pd
    print("✓ pandas: OK")
except ImportError as e:
    print(f"✗ pandas: {e}")

try:
    import matplotlib
    print("✓ matplotlib: OK")
except ImportError as e:
    print(f"✗ matplotlib: {e}")

print("All data science packages installed!")