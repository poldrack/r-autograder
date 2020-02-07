#!/usr/bin/env python3

"""
clear out assignment db for particular week
using config.json
"""

from rautograder.Database import Database
import json
import os
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Clear assignment database')
    parser.add_argument('-t', '--test_mode',
                        help='test mode',
                        action='store_true')
    parser.add_argument('-w', '--week',
                        type=int,
                        help='week number')
    parser.add_argument('-c', '--config_file',
                        help='json config',
                        default='config.json')
    args = parser.parse_args()

    if os.path.exists(args.config_file):
        print(f"loading config from {args.config_file}")

        with open(args.config_file,'r') as f:
            config = json.load(f)
        for v in config:
            setattr(args, v, config[v])
    
    print('Clearing database for week %d' % args.week)
    db = Database()

    db.clean_assignment_db(args.week)