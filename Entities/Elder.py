from Entities.Request import Request


class Elder(Request):
    def __init__(self, id, type, year, degree, uni, phone, help, description, profile, grades, students=None,hours=0):
        super().__init__(id, type, year, degree, uni, phone, help, description, profile, grades)
        self.students = students if students is not None else []
        self.hours=hours


class Student(Request):
    def __init__(self, id, type, year, degree, uni, phone, help, description, profile, grades, teachers=None,classes_to_approve=None):
        super().__init__(id, type, year, degree, uni, phone, help, description, profile, grades)
        self.teachers = teachers if teachers is not None else []
        self.classes_to_aprove = classes_to_approve if classes_to_approve is not None else []
def convert_request_to_specific_type(request_data, target_type):
    # Check if request_data is a dictionary
    if not isinstance(request_data, dict):
        raise ValueError("Input must be a dictionary")

    # Extract common fields from the request_data dictionary
    id = request_data.get('id')
    type = request_data.get('type')
    year = request_data.get('year')
    degree = request_data.get('degree')
    uni = request_data.get('uni')
    phone = request_data.get('phone')
    help_text = request_data.get('help')
    description = request_data.get('description')
    profile_url = request_data.get('profile_url')
    grades_url = request_data.get('grades_url')

    # Prepare common arguments for both Elder and Student
    args = (id, type, year, degree, uni, phone, help_text, description, profile_url, grades_url)

    if target_type == 'Elder':
        # Convert to Elder, assuming an empty students list by default
        return Elder(*args)

    elif target_type == 'Student':
        # Convert to Student, assuming an empty teachers list by default
        return Student(*args)

    else:
        raise ValueError("Target type must be 'Elder' or 'Student'")


