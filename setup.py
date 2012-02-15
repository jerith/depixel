from setuptools import setup, find_packages

version = '0.1'

setup(name='depixel',
      version=version,
      description='Depixeling tool, based on "Depixelizing Pixel Art"',
      long_description=open('README','rb').read(),
      # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=["Topic :: Multimedia :: Graphics"],
      author='Jeremy Thurgood',
      author_email='firxen@gmail.com',
      url='https://github.com/jerith/depixel',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'networkx',
          'pypng',
          'svgwrite',
      ],
      entry_points="""
      [console_scripts]
      depixel_png = depixel.scripts.depixel_png:main
      """,
      )
