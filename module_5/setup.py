"""Setup configuration for Graduate School Applicant Database Analysis System.

This setup.py makes the project installable as a Python package, enabling:
- Editable installs (pip install -e .) for development
- Consistent import behavior across different environments
- Dependency management via setuptools
- Integration with tools like uv for reproducible environments
"""

from setuptools import setup, find_packages

# Read long description from README
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

# Read requirements from requirements.txt
with open('requirements.txt', 'r', encoding='utf-8') as f:
    requirements = []
    for line in f:
        line = line.strip()
        # Skip comments and empty lines
        if line and not line.startswith('#'):
            requirements.append(line)

setup(
    name='gradcafe-analytics',
    version='1.0.0',
    author='Brad Ballinger',
    author_email='bballin2@jhu.edu',
    description='PostgreSQL-backed Flask web application for analyzing graduate school application data',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/bradleyballinger/jhu-software-concepts/tree/main/module_5',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Framework :: Flask',
        'Topic :: Database',
    ],
    python_requires='>=3.8',
    install_requires=[
        'psycopg[binary]>=3.1.0',
        'Flask>=3.0.0',
        'reportlab>=4.0.0',
        'beautifulsoup4>=4.12.0',
        'urllib3==2.6.3',  # Pinned: SNYK High severity fixes
        'Pillow==12.1.1',  # Pinned: SNYK High severity Out-of-bounds Write fix
        'charset-normalizer>=3.0.0',
        # Security patches for indirect dependencies
        'jinja2==3.1.6',  # Pinned: XSS/Template Injection fixes (Flask dep)
        'requests==2.32.4',  # Pinned: Sensitive info leakage fix (Sphinx dep)
        'certifi==2024.7.4',  # Pinned: Verification issue fix
    ],
    extras_require={
        'dev': [
            'pytest>=7.4.0',
            'pytest-mock>=3.12.0',
            'pytest-cov>=4.1.0',
            'pylint>=3.0.0',
            'pydeps>=3.0.0',
        ],
        'docs': [
            'sphinx>=7.2.0',
            'sphinx-rtd-theme>=2.0.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'gradcafe-app=app:main',
            'gradcafe-load=load_data:main',
            'gradcafe-query=query_data:main',
        ],
    },
    include_package_data=True,
    package_data={
        '': ['templates/*.html', 'static/css/*.css'],
    },
    zip_safe=False,
)
