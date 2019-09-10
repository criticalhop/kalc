"""
CHAI runs formal check of Kubernetes configurations using Poodle AI planner
"""
from setuptools import find_namespace_packages, setup

dependencies = ['click']

setup(
    python_requires='>=3.7',
    name='kubectl-val',
    version='0.1.0',
    url='https://github.com/criticalhop/kubectl-val',
    license='BSD',
    author='CriticalHop Team',
    author_email='info@criticalhop.com',
    description='Run formal check of Kubernetes configurations using Poodle AI planner',
    long_description=__doc__,
    packages=find_namespace_packages(exclude=['tests']),
    package_dir = {'guardctl': 'guardctl'},
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=dependencies,
    entry_points={
        'console_scripts': [
            'kubectl-val = guardctl.cli:run',
        ],
    },
    classifiers=[
        # As from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        # 'Development Status :: 1 - Planning',
        # 'Development Status :: 2 - Pre-Alpha',
        'Development Status :: 3 - Alpha',
        # 'Development Status :: 4 - Beta',
        # 'Development Status :: 5 - Production/Stable',
        # 'Development Status :: 6 - Mature',
        # 'Development Status :: 7 - Inactive',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'OSI Approved :: Apache Software License',
        'Operating System :: POSIX',
        'Operating System :: MacOS',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
