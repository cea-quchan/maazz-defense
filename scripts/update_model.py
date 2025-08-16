#!/usr/bin/env python
"""
اسکریپتی برای به‌روزرسانی مدل موجود.
این اسکریپت می‌تواند به‌صورت زمان‌بندی‌شده اجرا شود تا مدل بر اساس داده‌های جدید آموزش ببیند.

در این نسخهٔ ساده تنها اجرای دوبارهٔ `train_iforest.py` را فراخوانی می‌کند.
"""

import subprocess
import sys
import os


def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    train_script = os.path.join(root_dir, "models", "train_iforest.py")
    print("Retraining model...")
    result = subprocess.run([sys.executable, train_script], check=True)
    print("Model retrained.")


if __name__ == "__main__":
    main()