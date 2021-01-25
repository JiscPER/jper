from setuptools import setup, find_packages

setup(
    name = 'jper',
    version = '1.0.0',
    packages = find_packages(),
    install_requires = [
        "werkzeug==0.8.3",
        "Flask==0.9",
        "Flask-Login==0.1.3",
        "requests",
        "simplejson",
        "lxml==3.4.4",
        "Flask-WTF==0.8.3",
        "nose",
        "Flask-Mail==0.9.1",
        "python-dateutil",
        "unidecode",
        "esprit",
        "schedule==0.3.2",
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
