from setuptools import find_packages
import os
from distutils.core import setup

current_directory = os.path.dirname(os.path.abspath(__file__))
try:
    with open(os.path.join(current_directory, 'README.md'), encoding='utf-8') as f:
        long_description = f.read()
except Exception:
    long_description = ''


setup(
	name='frame_stamp',
	packages=find_packages('.'),
	version='0.0.1',
	license='',
	description='Render technical info on image',
	long_description=long_description,
	long_description_content_type='text/markdown',
	author='paulwinex',
	author_email='paulwinex@gmail.com',
	url='https://github.com/paulwinex/frame-stamp',
	download_url='https://github.com/paulwinex/frame-stamp',
	install_requires=['pillow', 'PySide6'],
	classifiers=[]
)
