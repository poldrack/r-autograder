"""
class for database
"""

import pandas
from pymongo import MongoClient


class Database:
    def __init__(self, 
                 student_file=None,
                 verbose=False):
        self.verbose = verbose
        self.get_client()
        self.classroom_db = self.client.autograder_classroom
        self.students_db = self.classroom_db.students
        self.assignment_db = self.classroom_db.assignment

        if student_file is not None:
            self.load_student_info(student_file)
        else:
            print('no student file available')

    def clean_assignment_db(self, week):
        myquery = {"week": week}
        x = self.assignment_db.delete_many(myquery)
        print(f'{x.deleted_count} documents deleted for week {week}')

    def get_all_assignments(self, week):
        return([ p for p in self.assignment_db.find({"week": week})])

    def get_client(self, maxSevSelDelay=10):
        self.client = MongoClient(serverSelectionTimeoutMS=maxSevSelDelay)
        # returns ServerSelectionTimeoutError
        # exception if server is not running
        self.client.server_info()

    def get_all_students(self):
        return([ p for p in self.students_db.find()])

    def get_student_by_sunet(self,sunet):
        return(self.students_db.find_one({"sunet": sunet}))

    def get_student_by_id(self,id):
        return(self.students_db.find_one({"id": id}))

    def update_student(self,sunet,field,value):
        return(self.students_db.update_one({"sunet": sunet}, {'$set':{field:value}}))

    def load_student_info(self, file):
        """load student data from canvas output"""
        sdata = pandas.read_csv(file,index_col=0)
        # drop two extra lines
        sdata = sdata.iloc[2:,:]
        sdata = sdata.dropna(subset = ['SIS User ID'])

        for s in sdata.index:
            si = sdata.loc[s]
            student_dict = {'sunet':sdata.loc[s,'SIS Login ID'],
                            'email':'%s@#stanford.edu' % sdata.loc[s,'SIS Login ID'],
                            'name':s,
                            'id':int(sdata.loc[s,'SIS User ID'])}
            sunet_matches = [i for i in self.students_db.find({'sunet':student_dict['sunet']})]
            if len(sunet_matches) == 0:
                result = self.students_db.insert_one(student_dict)
            if self.verbose:
                print('Adding: {0}'.format(result.inserted_id))

