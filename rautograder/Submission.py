"""
class for individual submissions

TODO:
- df value error
- deduct if markdown rendering fails

"""
import random
import string
import os
import shutil
import numpy
import collections
import rpy2
import numbers
from rpy2.robjects.packages import importr
import rpy2.robjects as robjects 
from rpy2.robjects import pandas2ri
from . Database import Database

def write_error(student, solution, sunet, error_dir='errors'):
    msg = ''
    write_error(msg, sunet, error_dir)

def log_error(msg, sunet, error_dir='errors'):
    if not os.path.exists(error_dir):
        os.mkdir(error_dir)
    error_file = os.path.join(
        error_dir,
        '%s.txt' % sunet
    )
    with open(error_file, 'a') as f:
        f.write(msg + '\n')
    print(msg)
    
class Submission:
    def __init__(self,
                filename,
                week,
                max_score=10,
                deduction_per_error=0.5,
                render_deduction=1,
                added_ignore_vars=None,
                verbose=False):

        self.filename = filename
        self.week = week
        self.db = Database()
        self.added_ignore_vars = added_ignore_vars
        self.verbose = verbose
        self.max_score = max_score
        self.deduction_per_error = deduction_per_error
        self.render_deduction = render_deduction
        # data variables
        self.lines = None
        self.lines_clean = None
        self.student_data = None

        # status variables
        self.rendered = None
        self.knitted = None
        self.sourced = None

        # file variables
        self.knitted_R_file = None
        self.rdata_file = None
        self.rendered_html_file = None

        # outcome variables
        self.sunet = None
        self.extra_deductions = None
        self.missing_vars = None
        self.size_errors = None
        self.value_errors = None
        self.df_missing_vars = None
        self.df_shape_error = None
        self.df_value_errors = None
        self.num_errors = None
        self.total_score = None

        # load and prepare submission
        self.load_submission(filename)
        self.get_sunet()
        self.cleanup_submission()
        self.get_extra_deductions()


    def load_submission(self,filename,replace_dict=None):
        """
        load the submission file
        """
        if self.verbose:
            print('loading %s'%self.filename)
        self.lines = [i.strip() for i in open(filename).readlines()]

    def get_sunet(self):
        """
        extract sunet ID from the file
        """
        sunet_line = None
        for l in self.lines:
            if l.find('sunetID <-') > -1:
                sunet_line = l.replace("'",'').replace('"','')
                break
        if sunet_line is not None:
            self.sunet = sunet_line.split(' ')[2].replace('_','')
        else:
            self.sunet = []
        if len(self.sunet) == 0:
            self.sunet = 'unknown_%s'%''.join(random.choices(string.ascii_letters + string.digits, k=6))

            print('using %s for %s'%(self.sunet,self.filename))

        # check whether it's in the list - if not, try to replace
        if not self.sunet in [i['sunet'] for i in self.db.get_all_students()]:
            if isinstance(self.sunet, str):
                # add to list
                student_dict = {
                    'sunet': self.sunet,
                    'email': 'Unknown',
                    'name': 'Unknown',
                    'id': None}
                result = self.db.students_db.insert_one(student_dict)
                print(f'added {self.sunet} to students database')
               
            # try to replace id with sunet
            elif isinstance(self.sunet, (int, float)):
                try:
                    i = int(self.sunet)
                    self.sunet = self.db.get_student_by_id(i)['sunet']
                    print('replaced with',self.sunet)
                except (ValueError,KeyError) as e:
                    print('cannot convert',e)
            else:
                raise ValueError('bad sunet ID value')
            
    def cleanup_submission(self,
                           replace_dict=None,
                           clean_dir = 'submissions_clean'):
        """
        comment out problematic commands
        - add additional ones with replace_dict
        """
        replacements = {
            'View(':'#View(',
            'view(':'#view(',
            'install.packages':'#install.packages'}
        if replace_dict is not None:
            for d in replace_dict:
                replacements[d] = replace_dict[d]
        # comment out bad lines
        self.lines_clean = []
        for l in self.lines:
            cl = l
            for r in replacements:
                cl = cl.replace(r,replacements[r])
            self.lines_clean.append(cl)
        # write cleaned file
        self.cleaned_file = os.path.join(
            clean_dir,
            '%s.Rmd' % self.sunet
        )
        if not os.path.exists(clean_dir):
            os.mkdir(clean_dir)

        with open(self.cleaned_file, 'w') as f:
            for l in self.lines_clean:
                f.writelines(l + '\n')

    def get_extra_deductions(self,
                             deduction_marker='RP FIX'):
        """
        check whether there were any manual deductions
        """
        self.extra_deductions = 0
        for l in self.lines:
            if l.find(deduction_marker)> -1:
                self.extra_deductions += 1

    def knit_rmd_file(self, output_dir = 'knit_Rfiles'):

        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        outfile = os.path.join(
            output_dir,
            '%s.R' % self.sunet
        )
        assert outfile != self.cleaned_file

        importr('knitr')
        rcode = '''
            Sys.setenv(RSTUDIO_PANDOC = "%s")
            Rfile=knit('%s' , output='%s', tangle=TRUE)
        ''' % (shutil.which('pandoc'), self.cleaned_file, outfile)
        robjects.r(rcode)

        self.knitted = os.path.exists(outfile)
        if not self.knitted:
            if self.verbose:
                print('problem knitting R file')
        else:
            self.knitted_R_file = outfile

    def source_r_file(self, rdata_path='rdata_files'):

        if not os.path.exists(rdata_path):
            os.mkdir(rdata_path)

        outfile = os.path.join(
            rdata_path,
            '%s.Rdata' % self.sunet
        )

        base = importr('base')
        r = robjects.r
        r('rm(list=ls())')
        assert os.path.exists(self.knitted_R_file)
        try:
            r.source(self.knitted_R_file)
            base.save_image(outfile)
        except: # need to use blank except here
            print('problem sourcing R file')
        self.sourced = os.path.exists(outfile)
        if self.sourced:
            self.rdata_file = outfile

    def render_r_file(self, render_dir = 'rendered_html'):
        # 
        if not os.path.isabs(render_dir):
            render_dir = os.path.abspath(render_dir)

        if not os.path.exists(render_dir):
            os.mkdir(render_dir)

        r = robjects.r
        rmarkdown = importr('rmarkdown')
        outfile = os.path.join(
            render_dir,
            '%s.nb.html' % self.sunet
        )
        print(outfile)
        try:
            rmarkdown.render(self.cleaned_file, 
                         output_file = outfile)
        except:
            print('problem rendering rmarkdown')

        if not os.path.exists(outfile):
            self.rendered = False
        else:
            self.rendered = True
            self.rendered_html_file = outfile


    def compare_data(
        self, 
        master_rdata,
        verbose=False,
        error_dir='errors',
        ignore_vars = [
                'solutionData',
                'studentData',
                'sunetID',
                'yourName',
                'Rfile']):
        """
        compare student values to master
        """

        if self.rdata_file is None:
            print('no R data, returning without comparison')
            return
        
        if self.added_ignore_vars is not None:
            print('adding ignored vars:', self.added_ignore_vars)
            assert isinstance(self.added_ignore_vars, list)
            for v in self.added_ignore_vars:
                ignore_vars.append(v)

        # load student and master values from rdata files
        rcode = '''
        rm(list=ls())
        solutionData = new.env()
        load('%s',envir = solutionData)
        solutionVars = ls(envir = solutionData)
        studentData = new.env()
        load('%s',envir = studentData)
        studentVars = ls(envir = studentData)
        ''' % (master_rdata, self.rdata_file)

        robjects.r(rcode)

        student_list = list(robjects.r('ls(envir= studentData)'))

        solution_list = list(robjects.r('ls(envir= solutionData)'))

        # remove ignored variables from solution list
        for v in ignore_vars:
            if verbose:
                print("ignoring", v)
            if v in solution_list:
                solution_list.remove(v)
            if v in student_list:
                student_list.remove(v)

        # classify variables as dataframe vs not
        data_frames = []
        non_df_variables = []
        for v in solution_list:
            if list(robjects.r('is.data.frame(solutionData$%s)' % v))[0]:
                data_frames.append(v)
                print('found data frame:', v)
            else:
                non_df_variables.append(v)
                print('found regular variable:', v)
               

        # check for missing variables in submission
        self.num_errors = 0
        self.missing_vars = []
        for s in solution_list:
            if s not in student_list:
                self.missing_vars.append(s)
                self.num_errors += 1
                log_error('missing variable: %s' % s, self.sunet)

        print('Missing:', self.missing_vars)

        self.student_data = collections.defaultdict(None)

        # test non-data frame variables for size/value errors
        self.size_errors = []
        self.value_errors = []
        for v in non_df_variables:
            # skip missing vars
            if v in self.missing_vars:
                continue
            if verbose:
                print(v)
            student_value = numpy.array(robjects.r("studentData$%s" % v))
            solution_value = numpy.array(robjects.r("solutionData$%s" % v))
            if verbose:
                print(v, ':', student_value)
                print(v, ':', solution_value)

            # check for bad variable (no length)
            try:
                len(student_value)
            except TypeError:
                # self.size_errors.append(v)
                # self.num_errors += 1
                # msg = f'nonDf bad variable error: {v} {student_value}'
                # log_error(msg, self.sunet)
                # fix variable here, will be a size error below
                student_value = []
               
            if len(student_value) != len(solution_value):
                # will catch zero length
                self.size_errors.append(v)
                self.num_errors += 1
                msg = f'nonDf size error: {v} {len(student_value)} vs {len(solution_value)}'
                log_error(msg, self.sunet)
            else:
                # catch other errors
                if isinstance(student_value[0], numbers.Number):
                    isError = not numpy.allclose(student_value,solution_value)
                else: # other types of vars
                    isError = not numpy.all(student_value == solution_value)
                if isError:
                    self.value_errors.append(v)
                    self.num_errors += 1
                    msg = f'value error: {v} {student_value} vs {solution_value}'
                    log_error(msg, self.sunet)
                else:
                    msg = f'value correct: {v} {student_value} vs {solution_value}'
                    log_error(msg, self.sunet)
            # move this down to save fixed versions
            if isinstance(student_value, list):
                self.student_data[v] = student_value
            else:
                self.student_data[v] = student_value.tolist()
                   


        # test data frames for missing vars, shape errors, and value errors
        self.df_missing_vars = collections.defaultdict(list)
        self.df_shape_error = []
        self.df_value_errors = collections.defaultdict(list)

        for df in data_frames:
            # first check existence of variable in student space
            if df in self.missing_vars:
                continue

            # convert to pandas data frames
            student_value = pandas2ri.rpy2py_dataframe(robjects.r("studentData$%s" % df))
            self.student_data[v] = student_value.to_json()
            solution_value = pandas2ri.rpy2py_dataframe(robjects.r("solutionData$%s" % df))

            # check for length
            if student_value.shape[0] != solution_value.shape[0]:
                self.df_shape_error.append(df)
                self.num_errors += 1

            # check for same variables
            shared_vars = set(student_value.columns).intersection(solution_value.columns)
            diff = set(solution_value.columns).difference(student_value.columns)
            if len(diff) > 0:
                self.df_missing_vars[df] = list(diff)
                self.num_errors += 1

            for v in shared_vars:
                try:
                    print(f'checking {v}')
                    print(student_value[v])
                    print(solution_value[v])
                    eq = numpy.allclose(student_value[v],solution_value[v])

                    if not eq:
                        self.df_value_errors[df].append(v)
                        self.num_errors += 1
                except TypeError:
                    eq = numpy.equal(student_value[v],solution_value[v])
                    if eq.mean() != 1:
                        self.df_value_errors[df].append(v)
                        self.num_errors += 1
                except ValueError:
                    print(f'problem comparing {v} in {df}')
                    # this probably occurred because of a shape error
                    # which should have been caught above
                    # if not, then store it here
                    if df not in self.df_shape_error:
                        self.df_value_errors[df].append(v)
                        self.num_errors += 1

        self.total_score = self.max_score - self.extra_deductions - self.num_errors*self.deduction_per_error   
        if self.rendered is None:
            self.total_score -= self.render_deduction
        self.total_score = numpy.min(self.total_score, 0)
        print('Total score:', self.total_score)
  
    def get_vars_to_save(self):
        v = vars(self).copy()
        print(v)
        del v['db']
        return v

    def save_assignment_to_db(self, v):
        sunet_matches = [i for i in self.db.assignment_db.find({'sunet':self.sunet})]
        if len(sunet_matches) == 0:
            print("inserting",self.sunet)
            return(self.db.assignment_db.insert_one(v))
        else:
            print("updating",self.sunet)
            return(self.db.assignment_db.update_one({'sunet':self.sunet},{'$set':v}))

