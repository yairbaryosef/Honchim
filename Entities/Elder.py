from Entities.Request import Request


class Elder(Request):
    def __init__(self, id, type, year, degree, uni, phone, help, description, profile, grades):
        super().__init__(id, type, year, degree, uni, phone, help, description, profile, grades)
        self.students=[]

    def __init__(self, id, type, year, degree, uni, phone, help, description, profile, grades,students):
        super().__init__(id, type, year, degree, uni, phone, help, description, profile, grades)
        self.students = students

class Student(Request):
    def __init__(self, id, type, year, degree, uni, phone, help, description, profile, grades):
        super().__init__(id, type, year, degree, uni, phone, help, description, profile, grades)
        self.teachers=[]

    def __init__(self, id, type, year, degree, uni, phone, help, description, profile, grades,students):
        super().__init__(id, type, year, degree, uni, phone, help, description, profile, grades)
        self.teachers = students





