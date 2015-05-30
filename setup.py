from distutils.core import setup
setup(
  name = 'hubasana',
  packages = ['hubasana'],
  version = '0.1',
  description = 'A python tool for creating issues and tasks simultaneously on github and asana, and keeping them in sync.',
  license = 'MIT',
  author = 'Josh Whelchel',
  author_email = 'josh+hubasana@loudr.fm',
  url = 'https://github.com/loudr/hubasana',
  download_url = 'https://github.com/loudr/hubasana/tarball/0.1',
  keywords = ['github', 'asana', 'connect'],
  classifiers = [],
  requires = [
    'asana',
    'PyGithub',
    'certifi',
    'requests',
    'urllib3'
  ]
)