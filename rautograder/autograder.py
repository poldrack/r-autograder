import sys
import os
import glob
import argparse
import json
from pymongo.errors import ServerSelectionTimeoutError
from pymongo import MongoClient

from .Submission import Submission
from .reports import make_report


def get_args():
    """
    parse arguments
    """
    parser = argparse.ArgumentParser(
        description='Run autograder')
    parser.add_argument('-s', '--submission_dir',
                        help='submissions directory')
    parser.add_argument('-f', '--submission_file',
                        help='single submission file to analyze')
    parser.add_argument('-w', '--week',
                        type=int,
                        help='week number')
    parser.add_argument('-e', '--extra_deduction',
                        type=float,
                        default=1.0,
                        help='deduction for manual fixes')
    parser.add_argument('-m', '--master_file',
                        help='master file for pset',
                        default='../data/Master.Rmd')
    parser.add_argument('-d', '--output_dir',
                        help='output dir for results',
                        default='./')
    parser.add_argument('-t', '--test_mode',
                        help='test mode',
                        action='store_true')
    parser.add_argument('-c', '--config_file',
                        help='json config',
                        default='config.json')
    parser.add_argument('--ignore', nargs='+',
                        help='variables to ignore')
    parser.add_argument('--ignore_sign_vars', nargs='+',
                        help='variables to ignore')
    args = parser.parse_args()

    if args.config_file:
        args = get_args_from_json(args)
    return(args)


def get_args_from_json(args, config_file='config.json'):
    # check for additional args in json
    if not os.path.exists(config_file):
        print(f'config file {config_file} not present')
        return(args)
    print(f"loading config from {config_file}")
    print('These will override any command line entries')
    with open(config_file, 'r') as f:
        config = json.load(f)
    for v in config:
        setattr(args, v, config[v])
    return(args)


def get_submission_files(submission_dir, suffix='.Rmd'):
    files = glob.glob(os.path.join(
        submission_dir, '*' + suffix
    ))
    return(files)


def process_submission(
    submission_file,
    master_submission,
    week,
    output_dir,
    added_ignore_vars=None,
    extra_deduction_size=1,
    ignore_sign_vars=None):
    # load the submission
    print(f'loading {submission_file}')

    submission = Submission(
        submission_file,
        week,
        output_dir=output_dir,
        added_ignore_vars=added_ignore_vars,
        extra_deduction_size=extra_deduction_size,
        ignore_sign_vars=ignore_sign_vars)
    
    print('Extra deductions:', submission.extra_deductions)

    # knit the Rmd file, generating an R file, record if failed
    submission.knit_rmd_file()
    print('Knitted:', submission.knitted)

    # source the resulting R file and save Rdata, record failure
    submission.source_r_file()
    print('Sourced:', submission.sourced)

    # render the Rmd file to html
    submission.render_r_file()
    print('Rendered:', submission.rendered)

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

    if args.test_mode:
        print('test mode, exiting')
        sys.exit(0)
    # load complete Pset Rmd
    master_submission = Submission(
        args.master_file,
        args.week,
        output_dir=args.output_dir)
    # run and save variable values of interest to RData file for grading
    master_submission.knit_rmd_file()
    # source master, save file to master_Rdata
    master_submission.source_r_file(rdata_path='master_Rdata')

    # get list of student Rmd files from specified submissions directory
    submission_files = get_submission_files(args.submission_dir)
    submission_files = ['../data/submissions/dfVarError.Rmd']
    # for each submission:
    for submission_file in submission_files:

        submission = process_submission(
            submission_file,
            master_submission,
            args.week,
            output_dir=args.output_dir)
        make_report(submission)
