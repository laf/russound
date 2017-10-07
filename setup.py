# pylint: disable=invalid-name, exec-used
"""Setup russound package."""
from __future__ import absolute_import
import sys
import os
from setuptools import setup, find_packages
# import subprocess
sys.path.insert(0, '.')

CURRENT_DIR = os.path.dirname(__file__)

# to deploy to pip, please use
# make pythonpack
# python setup.py register sdist upload
# and be sure to test it firstly using "python setup.py register sdist upload -r pypitest"
setup(name='russound',
      description='Python API for select Russound RNET commands to provide Russound support within home-assistant.io',
      version='0.1.9',
      long_description=open(os.path.join(CURRENT_DIR, 'README.md')).read(),
      install_requires=['requests'],
      maintainer='Neil Lathwood',
      maintainer_email='neil@lathwood.co.uk',
      zip_safe=False,
      packages=find_packages(),
      include_package_data=True,
      url='https://github.com/laf/russound.git')
