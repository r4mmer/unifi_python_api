# coding: utf-8

from setuptools import setup, find_packages

setup(
    name = "unifi_api",
    version = "0.1",
    packages = find_packages(),
    install_requires = [
        'requests>=2.21.0,<3',
        'trafaret>=1.2.0<1.3',
    ],
    author='André Carneiro',
    author_email='acarneiro.dev@gmail.com',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Information Technology',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
    ],
)
