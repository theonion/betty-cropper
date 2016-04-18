#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup
from setuptools.command.test import test as TestCommand
import os
import re
import sys


name = 'betty-cropper'
package = 'betty'
description = "A django-powered image server"
url = "https://github.com/theonion/betty-cropper"
author = "Chris Sinchok"
author_email = 'csinchok@theonion.com'
license = 'MIT'

setup_requires = []


def read_requirements(name):
    return open(os.path.join('requirements', name + '.txt')).readlines()


imgmin_requires = read_requirements('imgmin')

dev_requires = read_requirements('dev') + imgmin_requires

install_requires = read_requirements('common')

# Optional S3 storage, included for convenience
s3_requires = read_requirements('s3')


if 'test' in sys.argv:
    setup_requires.extend(dev_requires)


def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(package, "__init__.py")).read()
    return re.search("^__version__ = ['\"]([^'\"]+)['\"]", init_py, re.MULTILINE).group(1)


def get_packages(package):
    """
    Return root package and all sub-packages.
    """
    return [dirpath
            for dirpath, dirnames, filenames in os.walk(package)
            if os.path.exists(os.path.join(dirpath, '__init__.py'))]


def get_package_data(package):
    """
    Return all files under the root package, that are not in a
    package themselves.
    """
    walk = [(dirpath.replace(package + os.sep, '', 1), filenames)
            for dirpath, dirnames, filenames in os.walk(package)
            if not os.path.exists(os.path.join(dirpath, '__init__.py'))]

    filepaths = []
    for base, filenames in walk:
        filepaths.extend([os.path.join(base, filename)
                          for filename in filenames])
    return {package: filepaths}


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ['tests']
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


setup(
    name=name,
    version=get_version(package),
    url=url,
    license=license,
    description=description,
    author=author,
    author_email=author_email,
    packages=get_packages(package),
    package_data={
        "betty": ["cropper/templates/image.js", "cropper/font/OpenSans-Semibold.ttf"]
    },
    install_requires=install_requires,
    tests_require=dev_requires,
    extras_require={
        'dev': dev_requires,
        'imgmin': imgmin_requires,
        's3': s3_requires,
    },
    entry_points={
        "console_scripts": [
            "betty-cropper = betty.cropper.utils.runner:main",
        ],
    },
    cmdclass={'test': PyTest}
)
