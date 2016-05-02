import os
from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-ipsconnect3',
    version='0.5.2',
    packages=['ipsconnect3'],
    include_package_data=True,
    license='GPLv3+',
    description='A Django app to authenticate against an InvisionPower IPS Connect 3.x master, supplied by IP.Board 3.x.',
    long_description=README,
    url='https://github.com/phbaum/django_ipsconnect3',
    author='Philippe Baumann',
    author_email='mail@phbaum.ch',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.6',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        # Replace these appropriately if you are stuck on Python 2.
        #'Programming Language :: Python :: 3',
        #'Programming Language :: Python :: 3.2',
        #'Programming Language :: Python :: 3.3',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
