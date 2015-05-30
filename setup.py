import os

__VERSION__ = "0.1.3"

from distutils.core import setup
setup(
  name = 'hubasana',
  packages = ['hubasana'],
  version = str(__VERSION__),
  description = 'A python tool for creating issues and tasks simultaneously on github and asana, and keeping them in sync.',
  license = 'MIT',
  author = 'Josh Whelchel',
  author_email = 'josh+hubasana@loudr.fm',
  url = 'https://github.com/loudr/hubasana',
  download_url = 'https://github.com/loudr/hubasana/tarball/0.1.3',
  keywords = ['github', 'asana', 'connect'],
  classifiers = [],
  requires = [
    'asana',
    'PyGithub',
    'certifi',
    'requests',
    'urllib3'
  ],
  scripts=[os.path.join(".", name) for name in [
      "hub-asana",
    ]]
)