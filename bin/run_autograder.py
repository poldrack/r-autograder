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
from rautograder.reports import make_report
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
        sys.exit(0)

    db = Database()
    # load complete Pset Rmd 
    master_submission = Submission(args.master_file, args.week)
    # run and save variable values of interest to RData file for grading
    master_submission.knit_rmd_file()
    # source master, save file to master_Rdata
    master_submission.source_r_file(rdata_path='master_Rdata')

    # get list of student Rmd files from specified submissions directory
    submission_files = get_submission_files(args.submission_dir)
    # for each submission:
    failures = {}
    for submission_file in submission_files:
        try:
            submission = process_submission(submission_file, master_submission,args.week)
            submission_record = [ p for p in db.assignment_db.find(
                {'week':args.week, 'sunet':submission.sunet})]
            make_report(submission_record[0], args.week, 'reports')
        except Exception as e: 
            # I KNOW THIS IS BAD! but R throws various types of exceptions
            # I at least save the exception so we can look at it later
            failures[submission_file] = e

    make_summary_file(args.week)

    print('Failed processing on %d submissions' % len(failures))
    for f in failures:
        print(f, failures[f])

    if not os.path.exists('submissions_broken'):
        os.mkdir('submissions_broken')
    for file in failures:
        shutil.copy(file, 'submissions_broken')

    
    

