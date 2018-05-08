from setuptools import setup, find_packages

setup(
    name='pyresceneauto',
    version='0.0.5',
    description='Effortlessly turn extracted scene releases back into their original glory with the aid of pyRescene and srrdb.com',
    author='stick',
    license='WTFPL',
    url='https://bitbucket.org/sticki/pyautorescene',
    packages=find_packages(),
    scripts=['bin/autorescene.py'],

    keywords=['rescene', 'srr', 'srs', 'scene', 'resample', 'automate', 'auto'],
    install_requires=['requests', 'colorama'],
    # requests is used for HTTP requests to srrdb.com
    # colorama is used for pretty printing in verbose mode
)
