from setuptools import setup, find_packages

setup(
    name="doc_scraper",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'PyQt6>=6.4.0',
        'requests>=2.28.0',
        'beautifulsoup4>=4.11.0',
        'tqdm>=4.65.0',
    ],
) 