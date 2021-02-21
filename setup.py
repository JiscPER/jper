from setuptools import setup, find_packages

setup(
    name = 'jper',
    version = '1.0.0',
    packages = find_packages(),
    install_requires = [
        "werkzeug",
        "Flask",
        "Flask-Login",
        "requests",
        "simplejson",
        "lxml",
        "Flask-WTF",
        "nose",
        "Flask-Mail",
        "Flask-Babel",
        "python-dateutil",
        "unidecode",
        "esprit",
        "schedule",
        "jsonpath-rw-ext",
        "unicodecsv"
    ],
    url = 'http://cottagelabs.com/',
    author = 'Cottage Labs',
    author_email = 'us@cottagelabs.com',
    description = 'Jisc Publications Event Router',
    classifiers = [
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)
