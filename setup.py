from setuptools import find_packages, setup
import os

try:
    import pypandoc

    README = pypandoc.convert(os.path.join(os.path.dirname(__file__), 'README.md'), 'rst')
except (ImportError, OSError):
    print("Can't convert readme")
    README = ""

setup(
    name='py_elf_structs',
    version='1',
    packages=find_packages(),
    include_package_data=True,
    install_requires=['cstruct==1.8', 'pyelftools'],
    license='MIT License',
    description='A simple Django app to create rest applications',
    url='https://github.com/jonatanSh/py-elf-structs',
    author='Jonathan Shimon',
    author_email='jonatanshimon@gmail.com',

)
