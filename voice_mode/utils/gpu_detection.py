"""GPU detection utilities."""
import platform
import subprocess

def detect_gpu():
    return True, "cuda"
