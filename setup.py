#!/usr/bin/env python

'''
Setuptools Install Script
'''

from setuptools import setup, find_packages

requires = [
    'click',
]

setup(
    name='develop-servicelab',
    version='0.1',
    description='The CLI for Cisco Cloud Services',
    long_description=open('README.md').read(),
    author='Alex Altmann, Nick Foster',
    author_email='aaltman@cisco.com, nickfost@cisco.com',
    packages=find_packages(exclude=['tests*']),
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=requires,
    entry_points='''
        [console_scripts]
        stack = servicelab.stack:cli
        ''',
    classifiers=[
        # 'Development Status :: 1 - Planning',
         'Development Status :: 2 - Pre-Alpha',
        # 'Development Status :: 3 - Alpha',
        # 'Development Status :: 4 - Beta',
        # 'Development Status :: 5 - Production/Stable',
        # 'Development Status :: 6 - Mature',
        # 'Development Status :: 7 - Inactive',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: Cisco Systems',
        'Operating System :: POSIX',
        'Operating System :: MacOS',
        'Operating System :: Unix',
        # 'Operating System :: Windows',
        'Programming Language :: Python :: 2.7',
    ],
)
