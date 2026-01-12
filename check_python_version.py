import sys
import platform
with open("python_version_info.txt", "w") as f:
    f.write(f"Version: {sys.version}\n")
    f.write(f"Platform: {platform.platform()}\n")
    f.write(f"Architecture: {platform.architecture()}\n")
