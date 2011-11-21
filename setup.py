from setuptools import setup

setup(
    name = "swift-informant",
    version = "0.1",
    author = "Florian Hines",
    author_email = "syn@ronin.io",
    description = ("Swift Middleware to send events to statsd"),
    license = "Apache License, (2.0)",
    keywords = "openstack swift middleware",
    url = "http://github.com/pandemicsyn/informant",
    packages=['informant'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.6',
        'Environment :: No Input/Output (Daemon)',
        ],
    entry_points={
        'paste.filter_factory': [
            'informant=informant.informant:filter_factory',
            ],
        },
    )
