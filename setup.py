from setuptools import setup, find_packages
import os
from bwp import __version__

def read(fname):
    try:
        return open(os.path.join(os.path.dirname(__file__), fname)).read()
    except:
        return ''

setup(
    name='BWP',
    version=__version__,
    description='The Business Web Platform is Django-application. ' \
                'Contains models, templates and other preparations for ' \
                'the fast building of ERP system',
    long_description=read('README.md'),
    author='Grigoriy Kramarenko',
    author_email='root@rosix.ru',
    url='https://bitbucket.org/rosix/bwp/',
    license='GNU General Public License v3 or later (GPLv3+)',
    platforms='any',
    zip_safe=False,
    packages=find_packages(),
    include_package_data = True,
    install_requires=['django-quickapi', 'pytz', 'django-reportapi'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Natural Language :: Russian',
        'Operating System :: OS Independent',
        'Programming Language :: JavaScript',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Internet :: WWW/HTTP :: Site Management',
        'Topic :: Office/Business',
    ],
)
