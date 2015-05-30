import os

__VERSION__ = "0.2.0"

from distutils.core import setup
setup(
  name = 'asana-hub',
  packages = ['asana_hub'],
  version = __VERSION__,
  description = 'A python lib & tool for creating issues and tasks simultaneously on github and asana, and keeping them in sync.',
  license = 'MIT',
  author = 'Josh Whelchel',
  author_email = 'josh+asanahub@loudr.fm',
  url = 'https://github.com/loudr/asana-hub',
  download_url = 'https://github.com/loudr/asana-hub/tarball/0.2.0',
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
      "asana-hub",
    ]]
)