try:
    from setuptools import setup
except:
    from distutils.core import setup
import os
import sys
from warnings import warn

def find_packages():
    import os
    packages = []
    walker = os.walk('src')
    prefix = os.path.join(os.path.curdir,'src')
    for thisdir, itsdirs, itsfiles in walker:
        if '__init__.py' in itsfiles:
            packages.append(thisdir[len(prefix)-1:])
    
    return packages
            
def find_data():
    import os
    import re
    data_pattern = re.compile(r'.*(.|_)(yaml|nc|net|irr|phy|ptb|sum|voc|txt|xls|graffle)$')
    data = []
    prefix = os.path.join(os.path.curdir,'src', 'pyPA')
    walker = os.walk('src')
    for thisdir, itsdirs, itsfiles in walker:
        if thisdir != os.path.join('src','pyPA.egg-info'):
            data.extend([os.path.join(thisdir[len(prefix)-1:],f) for f in itsfiles if data_pattern.match(f) is not None])
    
    return data

packages = find_packages()
data = find_data()

setup(name = 'pyPA',
      version = '2.0',
      author = 'Barron Henderson',
      author_email = 'barronh@gmail.com',
      maintainer = 'Cam Phelan',
      maintainer_email = 'cam_phelan@berkeley.edu',
      packages = packages,
      package_dir = {'': 'src'},
      package_data = {'pyPA': data},
      requires = ['numpy (>=1.2)', 'yaml', 'PseudoNetCDF', 'netCDF4'],
      url = 'https://code.google.com/p/pypa'
      )
