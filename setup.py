from setuptools import find_packages, setup

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
