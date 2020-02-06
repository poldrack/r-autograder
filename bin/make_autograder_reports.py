#!/usr/bin/env python3
"""
reporting functions
"""


import argparse

from rautograder.reports import make_reports, make_summary_file

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Run autograder')
    parser.add_argument('-w', '--week',
                        required=True,
                        type=int,
                        help='week number')
    args = parser.parse_args()
    make_reports(args.week)
    make_summary_file(args.week)

