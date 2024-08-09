from setuptools import setup, find_packages

setup(
    name='pdulate',
    version='0.1.0',
    description='A library for parsing and manipulating Pure Data files',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Natsume Ishikawa',
    url='',
    packages=['pdulate'],
    package_dir={'pdulate': 'src'},
    package_data={
        'pdulate': ['../scripts/*.py'],
    },
    entry_points={
        'console_scripts': [
            'pdu=pdulate.scripts:main',
        ],
    },
    install_requires=[],
    extras_require={
        'cli': [
            'resampy>=0.4.3',
            'soundfile>=0.12.1'
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: The Unlicense (Unlicense)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
