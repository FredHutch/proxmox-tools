from setuptools import setup

__version__ = "1.4"

#try:
#    from pypandoc import convert
#    read_md = lambda f: convert(f, 'rst')
#except ImportError:
#    print("warning: pypandoc module not found, could not convert Markdown to RST")
#    read_md = lambda f: open(f, 'r').read()

CLASSIFIERS = [
    "Development Status :: 5 - Production/Stable",
    "Environment :: Console",
    "Intended Audience :: Customer Service",
    "Intended Audience :: Developers",
    "Intended Audience :: Education",
    "Intended Audience :: End Users/Desktop",
    "Intended Audience :: Information Technology",
    "Intended Audience :: Science/Research",
    "Intended Audience :: System Administrators",
    "License :: OSI Approved :: Apache Software License",
    "Natural Language :: English",
    "Operating System :: MacOS :: MacOS X",
    "Operating System :: POSIX",
    "Operating System :: POSIX :: Linux",
    "Operating System :: POSIX :: Other",
    "Operating System :: Unix",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.4",
    "Programming Language :: Python :: 3.5",
    "Programming Language :: Python :: Implementation :: CPython",
    "Programming Language :: Unix Shell",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: System :: Systems Administration",
    "Topic :: Utilities"
]

setup(
    name='proxmox-tools',
    version=__version__,
    description='prox is a command line interface to rapidly deploy LXC containers on proxmox from a remote host using proxmox REST API',
    long_description=open('README.rst', 'r').read(),
    packages=['prox'],
    scripts=['prox/prox'],
    author = 'dipe',
    author_email = 'dp@nowhere.com',
    url = 'https://github.com/FredHutch/proxmox-tools',
    download_url = 'https://github.com/FredHutch/proxmox-tools/tarball/%s' % __version__,
    keywords = ['proxmox', 'tools', 'containers', 'virtualization'], # arbitrary keywords
    classifiers = CLASSIFIERS,
    install_requires=[
        'paramiko',
        'requests'
        ],
    entry_points={
        # we use console_scripts here to allow virtualenv to rewrite shebangs
        # to point to appropriate python and allow experimental python 2.X
        # support.
        'console_scripts': [
            'cmdprox.py=prox.cmdprox:main',
        ]
    }
)
