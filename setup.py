import os

__VERSION__ = "0.2.7"

from distutils.core import setup
setup(
  name = 'asana-hub',
  packages = ['asana_hub', 'asana_hub.actions'],
  version = __VERSION__,
  description = 'A python lib & tool for creating issues and tasks simultaneously on github and asana, and keeping them in sync.',
  license = 'MIT',
  author = 'Josh Whelchel',
  author_email = 'josh+asanahub@loudr.fm',
  url = 'https://github.com/loudr/asana-hub',
  download_url = 'https://github.com/Loudr/asana-hub/archive/%22'+__VERSION__+'%22.tar.gz',
  keywords = ['github', 'asana', 'connect'],
  classifiers = [],
  install_requires = [
    'asana>=0.1.5',
    'PyGithub>=1.25.2',
    'certifi',
    'requests',
    'urllib3'
  ],
  scripts=[os.path.join(".", name) for name in [
      "asana-hub",
    ]]
)