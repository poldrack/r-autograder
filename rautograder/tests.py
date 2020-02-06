"""
tests using included data files
to check for specific errors
"""
import pytest
from Submission import Submission
from autograder import process_submission
from reports import make_report, make_summary_file
from Database import Database

WEEK = 0

@pytest.fixture(scope="session")
def master():
    master = Submission('../data/Master.Rmd', WEEK)
    # run and save variable values of interest to RData file for grading
    master.knit_rmd_file()
    # source master, save file to master_Rdata
    master.source_r_file(rdata_path='master_Rdata')
    print('master:',master.rdata_file)
    return(master)


def test_clean():
    # clean out database for Week 0
    db = Database()
    db.clean_assignment_db(0)
    a = db.get_all_assignments(0)
    assert len(a) == 0


def test_master(master):
    submission = process_submission(
        '../data/submissions/Master.Rmd',
        master,
        WEEK
    )
    assert submission.total_score == 10


def test_dfSizeError(master):
    submission = process_submission(
        '../data/submissions/dfSizeError.Rmd',
        master,
        WEEK
    )
    assert submission.total_score == 9.5


def test_dfValueError(master):
    submission = process_submission(
        '../data/submissions/dfValueError.Rmd',
        master,
        WEEK
    )
    assert submission.total_score == 9.5


def test_dfVarError(master):
    submission = process_submission(
        '../data/submissions/dfVarError.Rmd',
        master,
        WEEK
    )
    assert submission.total_score == 9.5


def test_ManualFix(master):
    submission = process_submission(
        '../data/submissions/manualFix.Rmd',
        master,
        WEEK
    )
    assert submission.total_score == 9


def test_MarkdownError(master):
    submission = process_submission(
        '../data/submissions/markdownError.Rmd',
        master,
        WEEK
    )
    assert submission.total_score == 10


def test_sizeError(master):
    submission = process_submission(
        '../data/submissions/sizeError.Rmd',
        master,
        WEEK
    )
    assert submission.total_score == 9.5


def test_twoValueErrors(master):
    submission = process_submission(
        '../data/submissions/twoValueErrors.Rmd',
        master,
        WEEK
    )
    assert submission.total_score == 9


def test_ValueError(master):
    submission = process_submission(
        '../data/submissions/ValueError.Rmd',
        master,
        WEEK
    )
    assert submission.total_score == 9.5


def test_reporting():
    db = Database()
    for submission in db.get_all_assignments(0):
        make_report(submission, 0, 'test_reports')

def test_summary():
    make_summary_file(0)