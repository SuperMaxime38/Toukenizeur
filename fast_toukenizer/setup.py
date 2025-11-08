from setuptools import setup, Extension
import sys
import pybind11

extra_compile_args = ["-O3", "-std=c++17"]
if sys.platform == "win32":
    extra_compile_args = ["/O2", "/std:c++17"]

ext_modules = [
    Extension(
        "fastbpe._fastbpe",   # 👈 module C++ interne (note le nom complet)
        ["fastbpe/_fastbpe.cpp"],
        include_dirs=[pybind11.get_include()],
        language="c++",
        extra_compile_args=extra_compile_args,
    )
]

setup(
    name="fastbpe",
    version="0.2.1",
    author="Poutre Cosmique",
    description="Fast BPE tokenizer (C++ backend with Python wrapper)",
    packages=["fastbpe"],     # le package Python principal
    ext_modules=ext_modules,  # module C++ interne
    python_requires=">=3.10",
    setup_requires=["pybind11>=2.10.0"],
)