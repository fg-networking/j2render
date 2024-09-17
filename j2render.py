#! /usr/bin/env python3

# j2render.py - render document from Jinja2 template and YAML variables
# Copyright (C) 2020-2024  Erik Auerswald <auerswald@fg-networking.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
This module provides a CLI tool to render Jinja2 templates.

The CLI tool j2render.py allows creating (rendering) a document based
on templates in Jinja2 format together with variable definitions read
from a YAML file.

This module is not intended for import into Python programs and has no
documented API.  All functions and data are internal to the CLI tool.
"""

import argparse
import fileinput
import os.path
import sys
import jinja2
import yaml

# information about the program
PROG = 'j2render'
VERSION = '0.0.8'
COPYRIGHT_YEARS = '2020-2024'
AUTHORS = 'Erik Auerswald <auerswald@fg-networking.de>'

# definitions for help and version functionality
DESC = '''\
Create (render) a document based on a Jinja2 template and variable
definitions given in YAML format.
'''
VERS = f'''\
{PROG} version {VERSION}
Copyright (C) {COPYRIGHT_YEARS}  {AUTHORS}
License GPLv3+: GNU GPL version 3 or later <https://gnu.org/licenses/gpl.html>
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.
'''
EPIL = f'''\
{PROG} reads the template from STDIN, unless one or more template files
are specified.

By default, all templates are concatenated to create one output document.

The output document is written to STDOUT unless an output filename is
specified with the --output option, or the --outdir option is given.

If the --outdir option is given, {PROG} treats templates separately
and creates one output document per template, using the template name
without the last extension as file name (e.g., my.txt.j2 -> my.txt).

The options --output and --outdir mutually exclude each other.

If several variable files are given (using one --variables option per file),
their contents are merged into a single data structure.
'''

# global state variables to control logging output
debug = None    # pylint: disable=invalid-name
verbose = None  # pylint: disable=invalid-name
quiet = None    # pylint: disable=invalid-name


def dbg(message):
    """Generate debugging information."""
    if debug is not None:
        print(f'{PROG}: debug: {message}', file=sys.stderr)


def err(message):
    """Print an error message."""
    print(f'{PROG}: error: {message}', file=sys.stderr)


def wrn(message):
    """Print a warning message."""
    if quiet is None:
        print(f'{PROG}: warning: {message}', file=sys.stderr)


def vrb(message):
    """Generate verbose information."""
    if verbose is not None and quiet is None:
        print(f'{PROG}: info: {message}', file=sys.stderr)


def parse_arguments():
    """Parse command line arguments."""
    arg_prs = argparse.ArgumentParser(
        prog=PROG,
        description=DESC,
        epilog=EPIL,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    arg_prs.add_argument('-V', '--version', action='version', version=VERS)
    arg_prs.add_argument(
        'TEMPLATE',
        nargs='*',
        help='Jinja2 template'
    )
    arg_prs.add_argument(
        '-v',
        '--variables',
        action='append',
        help='YAML variables file (can be given mutiple times)'
    )
    arg_prs.add_argument(
        '-o',
        '--output',
        default=sys.stdout,
        help='output filename when combining templates'
    )
    arg_prs.add_argument(
        '-d',
        '--outdir',
        help='directory for output file(s) per template(s)'
    )
    arg_prs.add_argument(
        '--verbose',
        action='store_true',
        help='print progress information'
    )
    arg_prs.add_argument(
        '--quiet',
        action='store_true',
        help='suppress warning and informational messages'
    )
    arg_prs.add_argument(
        '--debug',
        action='store_true',
        help='print debugging information (includes --verbose)'
    )
    arg_prs.add_argument(
        '--remove-root-key',
        action='store_true',
        help='shorten variable names by removing the root key from the name'
    )

    args = arg_prs.parse_args()

    if not args.TEMPLATE and args.outdir is not None:
        err('per template rendering requires template file(s).')
        sys.exit(2)
    if args.outdir and args.output is not sys.stdout:
        err('options "--output" and "--outdir" cannot be used together.')
        exit(2)
    if args.debug:
        args.verbose = True
        args.quiet = False

    return args


def process_combined(file_list, variables, output):
    """Render one output document by combining all templates."""
    vrb('processing combined template(s).')
    template_lines = []
    last_file = ''

    with fileinput.input(file_list) as f:  # pylint: disable=invalid-name
        for line in f:                     # pylint: disable=invalid-name
            current_file = f.filename()    # pylint: disable=invalid-name
            if current_file != last_file:
                vrb(f'reading template file "{current_file}".')
                last_file = current_file
            template_lines.append(line)

    template_string = ''.join(template_lines)
    template = jinja2.Template(template_string)
    vrb('rendering document.')
    document = template.render(**variables)
    if output is sys.stdout:
        vrb('writing output to STDOUT.')
        print(document)
    else:
        vrb(f'writing output to file "{output}".')
        # pylint: disable=invalid-name
        with open(output, 'w') as f:
            print(document, file=f)
    return 0


def process_separate(file_list, variables, outdir):
    """Render one output document per template."""
    vrb('processing separate template files.')
    for template_file in file_list:
        vrb(f'processing template file "{template_file}".')
        with open(template_file) as f:  # pylint: disable=invalid-name
            template_string = f.read()  # pylint: disable=invalid-name
        template = jinja2.Template(template_string)
        output_basename = os.path.splitext(os.path.basename(template_file))[0]
        dbg(f'output_basename = {output_basename}')
        output = os.path.sep.join([outdir, output_basename])
        vrb(f'writing output to "{output}".')
        # pylint: disable=invalid-name
        with open(output, 'w') as f:
            print(template.render(**variables), file=f)
    return 0


def main():
    """Entry point for command line tool."""
    global debug    # pylint: disable=global-statement,invalid-name
    global verbose  # pylint: disable=global-statement,invalid-name
    global quiet    # pylint: disable=global-statement,invalid-name
    variables = {}

    # parse command line arguments
    args = parse_arguments()
    if args.verbose:
        verbose = True
        vrb('enabling progress information.')
    if args.quiet:
        quiet = True
        vrb('enabling progress information.')
    if args.debug:
        debug = True
        dbg('enabling debug information.')
    vrb('parsed command line arguments.')

    # load variables
    vrb('looking for variable definitions.')
    if args.variables:
        if len(args.variables) > 1 and not args.remove_root_key:
            wrn('variables with identical root key overwrite each other.')
        for vars_file in args.variables:
            vrb(f'reading variables from file "{vars_file}".')
            with open(vars_file, 'r') as f:    # pylint: disable=invalid-name
                tmp = yaml.safe_load(f)        # pylint: disable=invalid-name
            dbg(f'{tmp=}')
            if tmp and not isinstance(tmp, dict):
                err('variables must be given as key/value pairs.')
                return 1
            if (args.remove_root_key and tmp and isinstance(tmp, dict) and
                    len(tmp.keys()) == 1):
                dbg(f'removing root key from vars in file "{vars_file}"')
                tmp = tmp[next(iter(tmp.keys()))]
                dbg(f'{tmp=}')
            vrb('merging just read variables.')
            variables.update(tmp)
            dbg(f'{variables=}')

    # render templates (two general cases: separate or combined output)
    dbg(f'args.TEMPLATE = {args.TEMPLATE}')
    # case of combining all templates to produce one output file
    if args.outdir is None:
        dbg(f'calling process_combined({args.TEMPLATE}, {variables}, ' +
            f'{args.output})')
        ret = process_combined(args.TEMPLATE, variables, args.output)
    # case of writing one output file per template
    else:
        dbg(f'args.outdir = {args.outdir}')
        outdir = os.path.normpath(args.outdir)
        dbg(f'calling process_separate({args.TEMPLATE}, {variables}, ' +
            f'{outdir})')
        ret = process_separate(args.TEMPLATE, variables, outdir)
    dbg(f'rendering function returned "{ret}"')

    return ret


if __name__ == '__main__':
    exit_code = main()  # pylint: disable=invalid-name
    sys.exit(exit_code)
