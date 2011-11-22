from setuptools import setup, find_packages

from informant import __version__ as version

name = "informant"

setup(
    name = name,
    version = version,
    author = "Florian Hines",
    author_email = "syn@ronin.io",
    description = "Informant",
    license = "Apache License, (2.0)",
    keywords = "openstack swift middleware",
    url = "http://github.com/pandemicsyn/informant",
    packages=find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.6',
        'Environment :: No Input/Output (Daemon)',
        ],
    install_requires=[],
    entry_points={
        'paste.filter_factory': [
            'informant=informant.middleware:filter_factory',
            ],
        },
    )
