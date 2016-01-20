try:
    from setuptools import setup
except:
    from distutils.core import setup

config = {
    'description': 'Studio Raspberry Pi Controller',
    'author': 'Robin Gloster',
    'author_email': 'robin.gloster@ffs-synchron.de',
    'version': '0.1',
    'install_requires': [
        'nose',
    ],
    'scripts': ['bin/stupicon'],
    'packages': ['stupicon'],
    'name': 'stupicon',
}

setup(**config)
