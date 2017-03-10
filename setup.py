from setuptools import setup

setup(
    name="xvalidator",
    version="1.0.0",
    install_requires=[
        'PyYaml',
        'jinja2',
        'glob2'
    ],
    author = "Dan Clayton",
    author_email = "dan@azwebmaster.com",
    description = "Used to validate yaml or json files.",
    license = "MIT",
    keywords = "scaffold",
    url = "https://github.com/azweb76/x-validator",
    packages=['xvalidator'],
    entry_points={
        'console_scripts': [
            'xvalidator=xvalidator.xvalidator:main',
        ],
    },
)
