"""
reporting functions
"""

import os
import pandas
import collections

from .Database import Database


def make_reports(
        week,
        sunets=None,
        reports_dirname='reports',
        output_dir='./'):
    # get all submissions for this week
    db = Database()
    submissions_all = [p for p in db.assignment_db.find(
        {'week': week})]
    if sunets is not None:
        assert isinstance(sunets, list)
        # restrict to sunets of interest
        submissions = []
        for s in submissions_all:
            if s['sunet'] in sunets:
                submissions.append(s)
    else:
        submissions = submissions_all
    print(f'found {len(submissions)} matching submissions')
    for submission in submissions:
        make_report(submission, week, reports_dirname)


def make_report(submission, week, reports_dirname, output_dir):

    reports_dir = os.path.join(output_dir, reports_dirname)
    if not os.path.exists(reports_dir):
        os.mkdir(reports_dir)
    report_file = os.path.join(
        reports_dir,
        '%s_Week%d_report.txt' % (submission['sunet'], week)
    )

    # write the report
    with open(report_file, 'w') as f:
        f.write('Week %d pset grading report for %s\n' %
                (week, submission['sunet']))

        if submission.get('knitted', False):
            f.write('File knitted successfully\n')
        else:
            f.write('Problem knitting file\n')

        if submission.get('sourced', False):
            f.write('R code processed successfully\n')
        else:
            f.write('Problem processing R code\n')

        if submission.get('rendered', False):
            f.write('RMarkdown rendered successfully\n')
        else:
            f.write('Problem rendering RMarkdown file\n')

        if submission.get('extra_deductions', 0) > 0:
            f.write('Extra deduction for manual fixes: %d points\n' %
                    submission['extra_deductions'])

        if isinstance(submission.get('missing_vars', None), list):
            if len(submission['missing_vars']) > 0:
                f.write('The following variables were missing:\n')
                for v in submission['missing_vars']:
                    f.write(v + '\n')

        if isinstance(submission.get('missing_vars', None), list):
            if len(submission['size_errors']) > 0:
                f.write('The following variables were incorrectly sized:\n')
                for v in submission['size_errors']:
                    f.write(v + '\n')

        if isinstance(submission.get('value_errors', None), list):
            if len(submission['value_errors']) > 0:
                f.write('The following variables had incorrect values:\n')
                for v in submission['value_errors']:
                    f.write(v + '\n')

        if isinstance(submission.get('df_missing_vars', None), list):
            if len(submission['df_missing_vars']) > 0:
                f.write('The following data frames had missing variables:\n')
                for v in submission['df_missing_vars']:
                    f.write(v + '\n')

        if isinstance(submission.get('df_shape_error', None), list):
            if len(submission['df_shape_error']) > 0:
                f.write('The following data frames were incorrectly sized:\n')
                for v in submission['df_shape_error']:
                    f.write(v + '\n')

        if isinstance(submission.get('df_value_errors', None), dict):
            if len(submission['df_value_errors']) > 0:
                f.write('The following data frames had incorrect values:\n')
                for v in submission['df_value_errors']:
                    for k in submission['df_value_errors'][v]:
                        f.write('%s:%s\n' % (v, k))

        if submission.get('total_score', None) is not None:
            f.write('Total score: %0.1f points' % submission['total_score'])


def make_summary_file(week, output_dir):
    db = Database()
    outfile = os.path.join(
        output_dir,
        f'SummaryDataWeek{week}.csv')
    submissions = [p for p in db.assignment_db.find(
        {'week': week})]

    vars_to_save = ['sunet',
                    'rendered',
                    'knitted',
                    'sourced',
                    'extra_deductions',
                    'num_errors',
                    'total_score']
    summaryDf = pandas.DataFrame(columns=vars_to_save)

    for i, submission in enumerate(submissions):
        data_to_save = collections.OrderedDict()
        for v in vars_to_save:
            data_to_save[v] = submission[v]
        summaryDf.loc[i] = data_to_save
    summaryDf.to_csv(outfile, index=False)


if __name__ == '__main__':
    make_reports(0)
    make_summary_file(0)
