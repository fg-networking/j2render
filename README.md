# j2render - Create (Render) Documents from Jinja2 Templates

The `j2render.py` [Python](https://www.python.org/) (version 3) script
reads templates in [Jinja2](https://palletsprojects.com/p/jinja/) format
and variable definitions in [YAML](https://yaml.org/) format to create
(or *render*) textual output.

This allows to easily integrate Jinja2 templating
in build systems on Unix-like systems, e.g., using
[make](https://pubs.opengroup.org/onlinepubs/9699919799/utilities/make.html).
