from setuptools import setup

setup(
    name='dlcask',
    packages=['dlcask'],
    include_package_data=True,
    install_requires=[
        'flask',
        'google-api-python-client'
    ],
)
