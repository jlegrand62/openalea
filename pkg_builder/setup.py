import os, sys
pj = os.path.join

from setuptools import setup, find_packages
from openalea.deploy.metainfo import read_metainfo

# Reads the metainfo file
metadata = read_metainfo('metainfo.ini', verbose=True)
for key,value in metadata.iteritems():
    exec("%s = '%s'" % (key, value))


setup(
    name=name,
    version=version,
    description=description,
    author=author,
    author_email=author_email,
    url=url,
    license=license,

    namespace_packages=['openalea'],

    packages = find_packages('src'),
    package_dir={ '' : 'src' },
    zip_safe = True,

    # Dependencies
    install_requires = ['openalea.core'],
    dependency_links = ['http://openalea.gforge.inria.fr/pi'],

    entry_points = {
        "console_scripts": [
                 "alea_create_package = openalea.pkg_builder.layout.main",
                 ],
    }

)

