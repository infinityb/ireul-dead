import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'gevent',
    'flyrc', # git://github.com/mrflea/flyrc.git
    'libsre', # git://github.com/infinityb/libsre.git
    'audiotools', # git://github.com/tuffy/python-audio-tools.git
    ]

setup(name='hanyuu2',
      version='0.0',
      description='Internet radio backend',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
        "Programming Language :: Python",
        ],
      author='Stacey Ell',
      author_email='stacey.ell@gmail.com',
      url='',
      keywords='radio',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires)
