import os
import glob
import sys
from setuptools import setup, find_packages
from setuptools.extension import Extension
from setuptools.command.build_ext import build_ext as _build_ext
from setuptools.command.sdist import sdist as _sdist
from setupext import \
    check_for_openmp

def get_version(filename):
    """
    Get version from a file.

    Inspired by https://github.mabuchilab/QNET/.
    """
    with open(filename) as f:
        for line in f.readlines():
            if line.startswith("__version__"):
                return line.split("=")[1].strip()[1:-1]
    raise RuntimeError(
        "Could not get version from %s." % filename)


VERSION = get_version("yt_astro_analysis/__init__.py")

if os.path.exists('MANIFEST'):
    os.remove('MANIFEST')

with open('README.md') as file:
    long_description = file.read()

if check_for_openmp() is True:
    omp_args = ['-fopenmp']
else:
    omp_args = None

if os.name == "nt":
    std_libs = []
else:
    std_libs = ["m"]

cython_extensions = [
    Extension("yt_astro_analysis.ppv_cube.ppv_utils",
              ["yt_astro_analysis/ppv_cube/ppv_utils.pyx"],
              libraries=std_libs),
]

extensions = [
    Extension("yt_astro_analysis.halo_analysis.halo_finding.fof.EnzoFOF",
              ["yt_astro_analysis/halo_analysis/halo_finding/fof/EnzoFOF.c",
               "yt_astro_analysis/halo_analysis/halo_finding/fof/kd.c"],
              libraries=std_libs),
    Extension("yt_astro_analysis.halo_analysis.halo_finding.hop.EnzoHop",
              glob.glob("yt_astro_analysis/halo_analysis/halo_finding/hop/*.c")),
]

dev_requirements = [
    'astropy', 'codecov', 'flake8', 'girder-client', 'gitpython', 'nose',
    'nose-timer', 'pytest', 'scipy', 'sphinx', 'sphinx_bootstrap_theme',
    'twine', 'wheel']

# ROCKSTAR
if os.path.exists("rockstar.cfg"):
    try:
        rd = open("rockstar.cfg").read().strip()
    except IOError:
        print("Reading Rockstar location from rockstar.cfg failed.")
        print("Please place the base directory of your")
        print("rockstar-galaxies install in rockstar.cfg and restart.")
        print("(ex: \"echo '/path/to/rockstar-galaxies' > rockstar.cfg\" )")
        sys.exit(1)

    rockstar_extdir = "yt_astro_analysis/halo_analysis/halo_finding/rockstar"
    rockstar_extensions = [
        Extension("yt_astro_analysis.halo_analysis.halo_finding.rockstar.rockstar_interface",
                  sources=[os.path.join(rockstar_extdir, "rockstar_interface.pyx")]),
        Extension("yt_astro_analysis.halo_analysis.halo_finding.rockstar.rockstar_groupies",
                  sources=[os.path.join(rockstar_extdir, "rockstar_groupies.pyx")])
    ]
    for ext in rockstar_extensions:
        ext.library_dirs.append(rd)
        ext.libraries.append("rockstar-galaxies")
        ext.define_macros.append(("THREADSAFE", ""))
        ext.include_dirs += [rd,
                             os.path.join(rd, "io"), os.path.join(rd, "util")]
    extensions += rockstar_extensions

class build_ext(_build_ext):
    # subclass setuptools extension builder to avoid importing cython and numpy
    # at top level in setup.py. See http://stackoverflow.com/a/21621689/1382869
    def finalize_options(self):
        from Cython.Build import cythonize
        self.distribution.ext_modules[:] = cythonize(
                self.distribution.ext_modules)
        _build_ext.finalize_options(self)
        # Prevent numpy from thinking it is still in its setup process
        # see http://stackoverflow.com/a/21621493/1382869
        if isinstance(__builtins__, dict):
            # sometimes this is a dict so we need to check for that
            # https://docs.python.org/3/library/builtins.html
            __builtins__["__NUMPY_SETUP__"] = False
        else:
            __builtins__.__NUMPY_SETUP__ = False
        import numpy
        self.include_dirs.append(numpy.get_include())

class sdist(_sdist):
    # subclass setuptools source distribution builder to ensure cython
    # generated C files are included in source distribution.
    # See http://stackoverflow.com/a/18418524/1382869
    def run(self):
        # Make sure the compiled Cython files in the distribution are up-to-date
        from Cython.Build import cythonize
        cythonize(cython_extensions)
        _sdist.run(self)

setup(
    name="yt_astro_analysis",
    version=VERSION,
    description="yt astrophysical analysis modules extension",
    long_description = long_description,
    long_description_content_type='text/markdown',
    classifiers=["Development Status :: 5 - Production/Stable",
                 "Environment :: Console",
                 "Intended Audience :: Science/Research",
                 "License :: OSI Approved :: BSD License",
                 "Operating System :: MacOS :: MacOS X",
                 "Operating System :: POSIX :: Linux",
                 "Operating System :: Unix",
                 "Natural Language :: English",
                 "Programming Language :: C",
                 "Programming Language :: Python :: 3",
                 "Programming Language :: Python :: 3.6",
                 "Programming Language :: Python :: 3.7",
                 "Programming Language :: Python :: 3.8",
                 "Programming Language :: Python :: 3.9",
                 "Topic :: Scientific/Engineering :: Astronomy",
                 "Topic :: Scientific/Engineering :: Physics",
                 "Topic :: Scientific/Engineering :: Visualization"],
    keywords='astronomy astrophysics visualization ' +
    'amr adaptivemeshrefinement',
    entry_points={},
    packages=find_packages(),
    include_package_data = True,
    setup_requires=[
        'cython',
        'numpy',
    ],
    install_requires=[
        'h5py',
        'more_itertools',
        'numpy',
        'setuptools>=19.6,<58',
        'sympy',
        'unyt',
        'yt>=4.0.1',
    ],
    extras_require = {
        'dev':  dev_requirements,
    },
    cmdclass={'sdist': sdist, 'build_ext': build_ext},
    author="The yt project",
    author_email="yt-dev@python.org",
    url="https://github.com/yt-project/yt_astro_analysis",
    project_urls={
        'Homepage': 'https://yt-project.org/',
        'Documentation': 'https://yt-astro-analysis.readthedocs.io/',
        'Source': 'https://github.com/yt-project/yt_astro_analysis/',
        'Tracker': 'https://github.com/yt-project/yt_astro_analysis/issues'
    },
    license="BSD 3-Clause",
    zip_safe=False,
    scripts=[],
    ext_modules=cython_extensions + extensions,
    python_requires='>=3.6'
)
