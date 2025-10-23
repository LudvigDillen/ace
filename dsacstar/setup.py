from setuptools import setup
from torch.utils.cpp_extension import CppExtension, BuildExtension, library_paths
import os
import subprocess, shlex

opencv_inc_dir = os.environ.get("OPENCV_INCLUDE_DIR", "")
opencv_lib_dir = os.environ.get("OPENCV_LIB_DIR", "")

def try_pkg_config():
    try:
        cflags = subprocess.check_output(shlex.split("pkg-config --cflags opencv4")).decode().strip()
        libs   = subprocess.check_output(shlex.split("pkg-config --libs opencv4")).decode().strip()
        inc = [f[2:] for f in cflags.split() if f.startswith("-I")]
        libdirs = [f[2:] for f in libs.split() if f.startswith("-L")]
        return (inc[0] if inc else ""), (libdirs[0] if libdirs else "")
    except Exception:
        return "", ""

# Try env vars first, then pkg-config, then common Linux defaults
if not opencv_inc_dir or not opencv_lib_dir:
    inc, lib = try_pkg_config()
    if not opencv_inc_dir: opencv_inc_dir = inc
    if not opencv_lib_dir: opencv_lib_dir = lib

if not opencv_inc_dir:
    for cand in ("/usr/include/opencv4", "/usr/local/include/opencv4"):
        if os.path.exists(cand):
            opencv_inc_dir = cand
            break
if not opencv_lib_dir:
    for cand in ("/usr/lib/x86_64-linux-gnu", "/usr/local/lib", "/usr/lib"):
        if os.path.exists(os.path.join(cand, "libopencv_core.so")):
            opencv_lib_dir = cand
            break

if len(opencv_inc_dir) == 0:
    print("Error: You have to provide an OpenCV include directory. Edit this file.")
    exit()
if len(opencv_lib_dir) == 0:
    print("Error: You have to provide an OpenCV library directory. Edit this file.")
    exit()

# Compile/link flags
extra_compile_args = ["-fopenmp", "-std=c++17"]

# Torch shared library directories (libc10.so, libtorch.so, etc.)
torch_lib_dirs = library_paths()

# Bake rpaths so the loader finds Torch + OpenCV at runtime without LD_LIBRARY_PATH
extra_link_args = []
for p in torch_lib_dirs + [opencv_lib_dir]:
    if p:
        extra_link_args += [f"-Wl,-rpath,{p}"]

setup(
    name='dsacstar',
    ext_modules=[CppExtension(
        name='dsacstar',
        sources=['dsacstar.cpp', 'thread_rand.cpp'],
        include_dirs=[opencv_inc_dir],
        library_dirs=[opencv_lib_dir] + torch_lib_dirs,
        libraries=['opencv_core', 'opencv_calib3d'],
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
    )],
    cmdclass={'build_ext': BuildExtension}
)
