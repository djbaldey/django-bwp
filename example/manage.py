#!/usr/bin/env python
import os

# Set name directory of environ
ENV = '.virtualenvs/django1.4'

def getenv():
    path = os.path.abspath(os.path.dirname(__file__))
    while path:
        env = os.path.join(path, ENV)
        found = os.path.exists(env)
        if path == '/' and not found:
            raise EnvironmentError('Path `%s` not found' % ENV)
        elif found:
            return env
        else:
            path = os.path.dirname(path)


if __name__ == "__main__":

    if ENV:
        import sys

        env = getenv()
        python = 'python%s.%s' % sys.version_info[:2]
        packages = os.path.join(env, 'lib', python, 'site-packages')
        sys.path.insert(0, packages)

    # additional local develop folder:
    cwd = os.path.abspath(os.path.dirname(__file__))
    develop_dir = os.path.dirname(cwd)
    if os.path.exists(develop_dir):
        sys.path.insert(0, develop_dir)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
