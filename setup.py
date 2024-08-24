from setuptools import setup, find_packages
VERSION = '0.2.0'
DESCRIPTION = ("Post processor of Powerful Pixiv Downloader")

setup(
    name='ppp',
    version=VERSION,
    description=DESCRIPTION,
    author='ZhenShuo2021',
    author_email='noreply@example.com',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'matplotlib',
        'urllib3<2',
        'beautifulsoup4',
        'requests',
        'toml',
        'setuptools',
    ],
    entry_points={
        'console_scripts': [
            'ppp=src.main:main',
        ],
    },
)
