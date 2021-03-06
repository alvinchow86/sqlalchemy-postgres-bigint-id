from os import path
from setuptools import setup

# get version
__version__ = None
exec(open('sqlalchemy_bigint_id/version.py').read())

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md')) as f:
    long_description = f.read()

setup(
    name='sqlalchemy-postgres-bigint-id',
    version=__version__,
    description="SQLAlchemy-Postgres-BigInt-ID",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/alvinchow86/sqlalchemy-postgres-bigint-id',
    author='Alvin Chow',
    author_email='alvinchow86@gmail.com',
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
    packages=[
        'sqlalchemy_bigint_id',
    ],
    package_data={},
    scripts=[],
    install_requires=[
        'sqlalchemy>=1.2',
        'python-dateutil>=2.7',
    ],
    python_requires='>=3.6',
)
