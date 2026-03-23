"""
🔍 Environment Checker for Audio Intelligence Suite
Run this before the app to verify all dependencies are ready.
Usage: python check_setup.py
"""

import sys
import shutil
from pathlib import Path

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
CHECK = f"{GREEN}✓{RESET}"
CROSS = f"{RED}✗{RESET}"
WARN = f"{YELLOW}!{RESET}"

errors = []
warnings = []

print("\n🔍 Audio Intelligence Suite — Environment Check\n" + "=" * 50)

# Python version
v = sys.version_info
print(f"\n{'Python':.<30} {CHECK} {v.major}.{v.minor}.{v.micro}")
if v < (3, 9):
    errors.append("Python 3.9+ required")

# ffmpeg
def find_ffmpeg():
    path = shutil.which("ffmpeg")
    if path:
        return path
    if sys.platform == "win32":
        for loc in [
            Path("C:/ffmpeg/bin/ffmpeg.exe"),
            Path("C:/tools/ffmpeg/bin/ffmpeg.exe"),
        ]:
            if loc.exists():
                return str(loc)
        import os
        conda = os.environ.get("CONDA_PREFIX")
        if conda:
            p = Path(conda) / "Library" / "bin" / "ffmpeg.exe"
            if p.exists():
                return str(p)
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass
    return None

ffmpeg = find_ffmpeg()
if ffmpeg:
    print(f"{'ffmpeg':.<30} {CHECK} {ffmpeg}")
else:
    print(f"{'ffmpeg':.<30} {CROSS} NOT FOUND")
    errors.append("ffmpeg not found. Fix: pip install imageio-ffmpeg")

# Python packages
packages = {
    "streamlit": "streamlit",
    "whisper": "openai-whisper",
    "torch": "torch",
    "transformers": "transformers",
    "sklearn": "scikit-learn",
    "plotly": "plotly",
    "scipy": "scipy",
    "numpy": "numpy",
}

for import_name, pip_name in packages.items():
    try:
        mod = __import__(import_name)
        ver = getattr(mod, "__version__", "ok")
        print(f"{pip_name:.<30} {CHECK} {ver}")
    except ImportError:
        print(f"{pip_name:.<30} {CROSS} not installed")
        errors.append(f"pip install {pip_name}")

# imageio-ffmpeg (optional but recommended on Windows)
try:
    import imageio_ffmpeg
    print(f"{'imageio-ffmpeg':.<30} {CHECK} {imageio_ffmpeg.__version__}")
except ImportError:
    if sys.platform == "win32" and not ffmpeg:
        print(f"{'imageio-ffmpeg':.<30} {CROSS} not installed (NEEDED on Windows)")
        errors.append("pip install imageio-ffmpeg")
    else:
        print(f"{'imageio-ffmpeg':.<30} {WARN} not installed (optional)")
        warnings.append("pip install imageio-ffmpeg (recommended backup)")

# GPU
print()
try:
    import torch
    if torch.cuda.is_available():
        print(f"{'GPU (CUDA)':.<30} {CHECK} {torch.cuda.get_device_name(0)}")
    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        print(f"{'GPU (MPS)':.<30} {CHECK} Apple Silicon")
    else:
        print(f"{'GPU':.<30} {WARN} CPU only (slower but works fine)")
        warnings.append("No GPU detected — models will run on CPU (slower)")
except Exception:
    pass

# Summary
print("\n" + "=" * 50)
if errors:
    print(f"\n{RED}❌ {len(errors)} issue(s) to fix:{RESET}")
    for e in errors:
        print(f"   {CROSS} {e}")
    print(f"\n{YELLOW}Quick fix — run this:{RESET}")
    print(f"   pip install {' '.join(packages.values())} imageio-ffmpeg")
else:
    print(f"\n{GREEN}✅ All good! Run the app:{RESET}")
    print(f"   streamlit run audio_analytics_app.py")

if warnings:
    print(f"\n{YELLOW}Warnings:{RESET}")
    for w in warnings:
        print(f"   {WARN} {w}")

print()
