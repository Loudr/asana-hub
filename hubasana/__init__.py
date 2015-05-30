"""
Github.com / Asana.com issue tool.
Synchronises creation of github issues and asana tasks.
"""

VERSION = 0.1

from .tool import ToolApp

def tool_app():
    """Starts the tool."""
    app = ToolApp(version=VERSION)
    exit(app.exit_code)