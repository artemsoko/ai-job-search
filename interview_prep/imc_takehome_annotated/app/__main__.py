# ANNOTATED COPY of the submitted app/__main__.py.
from logging import INFO, basicConfig

from app.run import main

# basicConfig lives ONLY here. Library modules call getLogger(__name__) and configure nothing.
# That split is correct -- getting it backwards is the most common logging mistake in Python.
basicConfig(level=INFO, format='%(levelname)s %(message)s')

# SHIPPED GAP: main() runs at IMPORT time. Fine for `python -m app`, because that is exactly
# what -m does, but importing app.__main__ for any reason -- a test, a REPL -- runs the program.
main()

# ALTERNATIVE:
#
#   if __name__ == '__main__':
#       main()
