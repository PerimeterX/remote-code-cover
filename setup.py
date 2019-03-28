from os import path
from setuptools import setup, find_packages
from setuptools.command.install import install

CUR_DIR = path.dirname(__file__)

install_requires = open('requirements.txt', 'r').readlines()

setup(
    name='remote_code_cover',
    version='1.0.0',
    author='PerimeterX',
    author_email='ilai@perimeterx.com',
    description='A CLI tool for code instrumentation and test coverage reporting',
    long_description=open(path.join(CUR_DIR, 'README.md')).read(),
    keywords='perimeterx fastly vcl api instrumentation test-coverage',
    packages=find_packages(exclude=['contrib', 'docs', 'tests*', 'deploy', 'tmp']),
    py_modules=['cli'],
    install_requires=install_requires,
    zip_safe=False,
    include_package_data=True,
    entry_points='''
        [console_scripts]
        rcc=cli:main
    ''',
    classifiers=[
        'Operating System :: OS Independent', 'Programming Language :: Python',
        'License :: OSI Approved :: MIT License',
        'Development Status :: 1 - Alpha', 'Topic :: Utilities'
    ]
)
