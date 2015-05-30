"""
Maintains JSON based settings file manipulated as a dictionary.
"""

import json

class Settings(object):

    def __init__(self, args, version):
        self.args = args
        self.version = version

        self.filename = args.settings_file or ".hubasana"

        try:
            with open(self.filename, 'rb') as file:
                self.data = json.load(file)
        except IOError:
            self.data = {}

    def assert_version(self):
        """Asserts that the version and settings file exists."""

        if not self.has_key('version'):
            raise Exception("hubasana.py connect must be run first.")

        self.data['version'] = self.version

    def save(self):
        """Save settings."""

        with open(self.filename, 'wb') as file:
            self.data['version'] = self.version
            json.dump(self.data, file)

    def __setitem__(self, key, value):
        """Set a settings value by key."""
        self.data[key] = value

    def __getitem__(self, key):
        """Get a settings value by key."""
        return self.data[key]

    def apply(self, key, value, prompt, on_load=lambda a: a, on_save=lambda a: a):
        """Applies a setting value to a key, if the value is not `None`.

        Returns without prompting if either of the following:
            * `value` is not `None`
            * already present in the settings

        Args:
            prompt:
                May either be a string to prompt via `raw_input` or a
                method (callable) that returns the value.

            on_load:
                lambda. Value is passed through here after loaded.

            on_save:
                lambda. Value is saved as this value.
        """

        # Reset value if flag exists without value
        if value == '':
            value = None
            if key and self.data.has_key(key): del self.data[key]

        # If value is explicitly set from args.
        if value is not None:
            value = on_load(value)
            if key: self.data[key] = on_save(value)
            return value

        elif not key or not self.has_key(key):
            if callable(prompt):
                value = prompt()
            else:
                value = raw_input(prompt + ": ")

            if value is None:
                if self.data.has_key(key): del self.data[key]
                return None

            self.data[key] = on_save(value)
            return value

        return on_load(self.data[key])

    def assert_key(self, key):
        assert self.data.get(key), "%s missing from settings" % key

    def has_key(self, *args, **kwargs):
        return self.data.has_key(*args, **kwargs)

    def get(self, *args, **kwargs):
        return self.data.get(*args, **kwargs)

