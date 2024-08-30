class Request:
        def __init__(self,id, type, year, degree, uni, phone, help, description, profile, grades):
            self.id=id
            self.type = type
            self.year = year
            self.degree = degree
            self.uni = uni
            self.phone = phone
            self.help = help
            self.description = description
            self.profile = profile
            self.grades = grades

        def __repr__(self):
            return f"StudentProfile(type={self.type}, year={self.year}, degree={self.degree}, uni={self.uni}, phone={self.phone}, help={self.help}, description={self.description}, profile={self.profile}, grades={self.grades})"
