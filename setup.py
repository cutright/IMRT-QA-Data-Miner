from setuptools import setup, find_packages

requires = [
    'pdfminer.six',
    'pdfminer > 19',
    'numpy',
    'python-dateutil',
    'chardet == 3.0.4',
    'pathvalidate',
    'bokeh',
    'python-dateutil',
    'pathvalidate'
]

with open('README.md', 'r') as doc:
    long_description = doc.read()

setup(
    name='IQDM',
    include_package_data=True,
    packages=find_packages(),
    version='0.3.1',
    description='Scans a directory for IMRT QA results',
    author='Dan Cutright',
    author_email='dan.cutright@gmail.com',
    url='https://github.com/cutright/IMRT-QA-Data-Miner/',
    download_url='https://github.com/cutright/IMRT-QA-Data-Miner/archive/master.zip',
    license="MIT License",
    keywords=['radiation therapy', 'qa', 'research'],
    classifiers=[],
    install_requires=requires,
    entry_points={
        'console_scripts': [
            'IQDM=IQDM.main:main',
        ],
    },
    long_description=long_description,
    long_description_content_type="text/markdown"
)