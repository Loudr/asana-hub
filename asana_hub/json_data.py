"""
Maintains JSON based data file manipulated as a dictionary.
"""

import json

class JSONData(object):

    def __init__(self, filename, args, version):
        """
        Args:
            filename:
                Filename for database.
            args:
                Program arguments.
            version:
                Version of file.
        """
        self.args = args
        self.version = version

        self.filename = filename

        try:
            with open(self.filename, 'rb') as file:
                self.data = json.load(file)
        except IOError:
            self.data = {}

    def assert_version(self):
        """Asserts that the version and data file exists."""

        if not self.has_key('version'):
            raise Exception("`asana-hub connect` must be run first.")

        self.data['version'] = self.version

    def save(self):
        """Save data."""

        with open(self.filename, 'wb') as file:
            self.prune()
            self.data['version'] = self.version
            json.dump(self.data,
                file,
                sort_keys=True, indent=2)

    def __setitem__(self, key, value):
        """Set a value by key."""
        self.data[key] = value

    def __getitem__(self, key):
        """Get a value by key."""
        return self.data[key]

    def prune(self, data=None):
        if data is None:
            data = self.data

        empty_keys = [k for k, v in data.iteritems() if not v]
        for k in empty_keys:
            del data[k]

        for v in data.values():
            if isinstance(v, dict):
                self.prune(data=v)

    def apply(self, key, value, prompt=None,
        on_load=lambda a: a, on_save=lambda a: a):
        """Applies a setting value to a key, if the value is not `None`.

        Returns without prompting if either of the following:
            * `value` is not `None`
            * already present in the dictionary

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
            elif prompt is not None:
                value = raw_input(prompt + ": ")

            if value is None:
                if self.data.has_key(key): del self.data[key]
                return None

            self.data[key] = on_save(value)
            return value

        return on_load(self.data[key])

    def assert_key(self, key):
        assert self.data.get(key), "%s missing from data" % key

    def has_key(self, *args, **kwargs):
        return self.data.has_key(*args, **kwargs)

    def get(self, key, default_value=None):
        try:
            return self.data[key]
        except KeyError:
            if default_value is not None:
                self.data[key] = default_value

            return default_value

