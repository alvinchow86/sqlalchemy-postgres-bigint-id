from setuptools import setup

# get version
__version__ = None
exec(open('sqlalchemy_bigid/version.py').read())

setup(
    name='sqlalchemy-postgres-bigid',
    version=__version__,
    description="SQLAlchemy Postgres Big Integer ID",
    url='https://github.com/alvinchow86/sqlalchemy-postgres-bigid',
    author='Alvin Chow',
    author_email='alvinchow86@gmail.com',
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
    packages=[
        'sqlalchemy_bigid',
    ],
    package_data={},
    scripts=[],
    install_requires=[
        'sqlalchemy>=1.2',
        'python-dateutil>=2.7',
    ],
    python_requires='>=3.6',
)
