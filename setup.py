from setuptools import find_packages, setup
import os

try:
    import pypandoc

    README = pypandoc.convert(os.path.join(os.path.dirname(__file__), 'README.md'), 'rst')
except (ImportError, OSError) as e:
    print("Can't convert readme: {}".format(e))
    README = ""

setup(
    name='py_elf_structs',
    version='1.1',
    packages=find_packages(),
    include_package_data=True,
    install_requires=['cstruct==1.8', 'pyelftools'],
    license='MIT License',
    description='Python package to extract struct and type information from dwarf and build python cstructs',
    long_description=README,
    url='https://github.com/jonatanSh/py-elf-structs',
    author='Jonathan Shimon',
    author_email='jonatanshimon@gmail.com',

)
