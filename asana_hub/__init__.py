"""
Github.com / Asana.com issue tool.
Synchronises creation of github issues and asana tasks.
"""

__VERSION__ = "0.2.7"

from .tool import ToolApp

def tool_app():
    """Starts the tool."""
    app = ToolApp(version=__VERSION__)
    exit(app.exit_code)