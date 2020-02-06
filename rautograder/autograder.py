## Notes for refactor: Feb 2020

import sys
import os
import glob
import argparse
from pymongo.errors import ServerSelectionTimeoutError
from pymongo import MongoClient

from .Submission import Submission
from .reports import make_report

def get_args():
    # parse arguments
    parser = argparse.ArgumentParser(
        description='Run autograder')
    parser.add_argument('-s', '--submission_dir',
                        required=True,
                        help='submissions directory')
    parser.add_argument('-w', '--week',
                        required=True,
                        type=int,
                        help='week number')
    parser.add_argument('-m', '--master_file',
                        help='master file for pset',
                        default='../data/Master.Rmd')
    args = parser.parse_args()
    return(args)

def get_submission_files(submission_dir, suffix='.Rmd'):
    files = glob.glob(os.path.join(
        submission_dir, '*' + suffix
    ))
    return(files)

def process_submission(submission_file, master_submission, week):
    # load the submission
    print(f'loading {submission_file}')

    submission = Submission(
        submission_file, 
        week)
    print('Extra deductions:',submission.extra_deductions)

    # knit the Rmd file, generating an R file, record if failed
    submission.knit_rmd_file()
    print('Knitted:',submission.knitted)

    # source the resulting R file and save Rdata, record failure
    submission.source_r_file()
    print('Sourced:',submission.sourced)

    # check for existence of all variables of interest
    # compare student's values to completed values

    # make sure required packages were loaded

    # render the Rmd file to html
    submission.render_r_file()
    print('Rendered:',submission.rendered)

    submission.compare_data(master_submission.rdata_file)

    v = submission.get_vars_to_save()

    submission.save_assignment_to_db(v)

    return submission

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

    # load complete Pset Rmd 
    master_submission = Submission(args.master_file, args.week)
    # run and save variable values of interest to RData file for grading
    master_submission.knit_rmd_file()
    # source master, save file to master_Rdata
    master_submission.source_r_file(rdata_path='master_Rdata')

    # get list of student Rmd files from specified submissions directory
    submission_files = get_submission_files(args.submission_dir)
    submission_files = ['../data/submissions/dfVarError.Rmd']
    # for each submission:
    for submission_file in submission_files:

        submission = process_submission(submission_file, master_submission,args.week)
        make_report(submission)


    # generate report for each student

    # generate overall summary of grades


