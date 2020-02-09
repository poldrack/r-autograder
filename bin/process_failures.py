#!/usr/bin/env python3

"""
processing failed assignments
- copy to submissions_broken
"""

from rautograder.Database import Database
import json
import os
import argparse
import shutil

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Process failed assignments')
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
    
    print('Finding failures for week %d' % args.week)
    db = Database()

    # find bad assignments for this week
    failures = [ p for p in db.assignment_db.find(
        {'week': args.week,
        'total_score': None})]

    if not os.path.exists('submissions_broken'):
        os.mkdir('submissions_broken')

    for f in failures:
        shutil.copy(f['filename'], 'submissions_broken')
