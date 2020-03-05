#!/usr/bin/env python3

import sys
import shutil
import os
import glob
import argparse
from pymongo.errors import ServerSelectionTimeoutError
from pymongo import MongoClient

from rautograder.Database import Database
from rautograder.Submission import Submission
from rautograder.reports import make_report, make_summary_file
from rautograder.autograder import get_args, get_submission_files, process_submission


if __name__ == '__main__':

    # start mongodb (or at least make sure it's running)
    try:
        client = MongoClient(serverSelectionTimeoutMS=10)
        # returns exception if mongo is not active
        client.server_info() 
    except ServerSelectionTimeoutError:
        print('MongoDB is not running')
        sys.exit(0)

    args = get_args()

    if args.test_mode:
        print('Test mode:')
        print('Args:', args)

    db = Database()

    if not args.test_mode:
        # load complete Pset Rmd 
        master_submission = Submission(
            args.master_file,
            args.week,
            added_ignore_vars=args.ignore)
        # run and save variable values of interest to RData file for grading
        master_submission.knit_rmd_file()
        # source master, save file to master_Rdata
        master_submission.source_r_file(rdata_dirname='master_Rdata')

    # get list of student Rmd files from specified submissions directory
    if args.submission_file is not None:
        submission_files = [args.submission_file]
        print("processing single file:", args.submission_file)
    else:
        submission_files = get_submission_files(args.submission_dir)
    # for each submission:
    failures = {}
    for submission_file in submission_files:
        print(f'Processing {submission_file}')
        if args.test_mode:
            continue
        try:
            submission = process_submission(
                submission_file, 
                master_submission,
                args.week,
                output_dir='./',
                added_ignore_vars=args.ignore,
                extra_deduction_size=args.extra_deduction,
                ignore_sign_vars=args.ignore_sign_vars)
            submission_record = [ p for p in db.assignment_db.find(
                {'week':args.week, 'sunet':submission.sunet})]
            make_report(submission_record[0], args.week, 'reports')
        except Exception as e: 
            # I KNOW THIS IS BAD! but R throws various types of exceptions
            # I at least save the exception so we can look at it later
            failures[submission_file] = e

    if not args.test_mode:
        make_summary_file(args.week)

        print('Failed processing on %d submissions' % len(failures))
        for f in failures:
            print(f, failures[f])    
    

