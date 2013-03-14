from setuptools import setup, find_packages
import os
from bwp import VERSION

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()
README = read('README.md')

setup(
    name='BWP',
    version=VERSION,
    description='The "Business Web Package" is Django-application. Contains models, templates and other preparations for the fast building of ERP system',
    long_description=README,
    author='Grigoriy Kramarenko',
    author_email='root@rosix.ru',
    url='http://develop.rosix.ru/bwp/',
    license='GNU General Public License v3 or later (GPLv3+)',
    platforms='any',
    zip_safe=False,
    packages=find_packages(),
    include_package_data = True,
    install_requires=['django-quickapi'],
    classifiers=[
        'Development Status :: 1 - Planning',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Framework :: Django',
        'Natural Language :: Russian',
    ],
)
