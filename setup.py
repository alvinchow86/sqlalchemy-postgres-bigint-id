from setuptools import setup

# get version
__version__ = None
exec(open('sqlalchemy_bigid/version.py').read())

setup(
    name='sqlalchemy-postgres-bigid',
    version=__version__,
    description="SQLAlchemy Postgres Big Integer ID",
    author='Alvin Chow',
    packages=[
        'sqlalchemy_bigid',
    ],
    package_data={},
    scripts=[],
    install_requires=[
        'sqlalchemy>=1.2',
        'python-dateutil>=2.7',
    ],
)
