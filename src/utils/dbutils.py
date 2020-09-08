from pymongo import MongoClient
from utils.logging_utils import logging

# instantiate logger
logger = logging.getLogger(__name__)


# unpacking utility functions
def unpack_student_create_params(request):
    id_num = request.json.get('id_number', None)
    first_name = request.json.get('first_name', None)
    last_name = request.json.get('last_name', None)
    email = request.json.get('email', None)

    logger.info(f"unpacking student params. id: {id_num}, fname: {first_name}, lname: {last_name}, email: {email}")
    return id_num, first_name, last_name, email


def unpack_student_modify_params(request):
    current_id = request.json.get("current_id", None)
    new = request.json.get("new", {})
    mod_params = {'id_number': new.get('id_number', None),
                  'first_name': new.get('first_name', None),
                  'last_name': new.get('last_name', None),
                  'email': new.get('email', None)
                  }
    return current_id, {k: v for k, v in mod_params.items() if v}


def unpack_course_creation_params(request):
    """
    extract parameters for course creation from request body.
    """
    course_id = request.json.get('course_id', None)
    name = request.json.get('name', None)
    students = request.json.get('students', None)
    logger.info(f"unpacking course params. cid: {course_id}, name: {name}, students: {str(students)}")
    return course_id, name, students


def unpack_course_modification_params(request):
    """
    extract parameters for course modification from request body.
    """
    current_id = request.json.get("current_id", None)
    new = request.json.get("new", {})
    mod_params = {'course_id': new.get('course_id', None),
                  'name': new.get('name', None),
                  'students': new.get('students', None)
                  }
    return current_id, {k: v for k, v in mod_params.items() if v}


def unpack_grade_creation_params(request):
    """
    unpack params from request body
    """
    grade = request.json.get('grade', None)
    student_id = request.json.get('student_id', None)
    course_id = request.json.get('course_id', None)
    logger.info(f"unpacking grade params. sid: {student_id}, cid: {course_id}, grade: {grade}")
    return student_id, course_id, grade


def unpack_grade_modification_params(request):
    current_student_id = request.json.get("current_sid", None)
    current_course_id = request.json.get("current_cid", None)
    new = request.json.get("new", {})
    mod_params = {'student_id': new.get('student_id', None),
                  'course_id': new.get('course_id', None),
                  'grade': new.get('grade', None)
                  }
    return current_student_id, current_course_id, {k: v for k, v in mod_params.items() if v}


# validation utility functions
def validate_student_creation_params(id_num: int, first_name: str, last_name: str, email: str):
    """
    check if the parameters given are the correct types for the student document.
    :param id_num: integer
    :param first_name: str
    :param last_name: str
    :param email: str
    :return: bool
    """
    val_id = isinstance(id_num, int)
    val_fn = isinstance(first_name, str)
    val_ln = isinstance(last_name, str)
    val_em = isinstance(email, str)
    logger.info(f"validation: id: {val_id}, fn: {val_fn}, ln: {val_ln}, em: {val_em}")
    return val_id and val_fn and val_ln and val_em


def validate_student_modification_params(curr_id, mod_params, client):
    if len(mod_params) == 0:  # there most be some new param to update
        return False
    elif not isinstance(curr_id, int):  # current id must be an integer
        return False

    # check the modification params types, if params isn't given, ignore.
    id_val = isinstance(mod_params.get('id_number', 0), int)
    fn_val = isinstance(mod_params.get('first_name', ''), str)
    ln_val = isinstance(mod_params.get('last_name', ''), str)
    em_val = isinstance(mod_params.get('email', ''), str)

    # if new id is given, make sure it is not in use
    id_used = False
    if 'id_number' in mod_params and mod_params['id_number'] != curr_id:
        id_used = client.school.students.find({'id_number': mod_params['id_number']}).count() > 0

    return id_val and fn_val and ln_val and em_val and not id_used


def validate_course_student_list(student_ids, client):
    """
    checks if all the given student ids exist in the database.
    :param student_ids: list of student ids
    :param client: connected pymong client
    :return: true if all students exist, false otherwise
    """
    # make sure a list was given
    if not isinstance(student_ids, list):
        return False

    # make sure students are in db
    db = client.school
    collection = db.students
    existing_students = collection.find({'id_number': {'$in': student_ids}})
    if existing_students.count() == len(student_ids):
        logger.info(f"course validation passed. given students: {str(student_ids)}, existing: {str(list(existing_students))}")
        return True
    else:
        logger.info(f"course validation fail. given students: {str(student_ids)}, existing: {str(list(existing_students))}")
        return False


def validate_course_creation_params(course_id, name, students, client: MongoClient):
    """
    make sure given parameters for a course a of the correct types
    """
    val_cid = isinstance(course_id, int)
    val_name = isinstance(name, str)
    val_students = validate_course_student_list(students, client)
    logger.info(f"course validation. cid: {val_cid}, name: {val_name}, val_students: {val_students}")
    return val_cid and val_name and val_students


def validate_course_modification_params(curr_id, mod_params, client: MongoClient):
    """
    make sure that the new cours_id doesn't exist, that all enrolled students
    exist already, and that name is a valid string.
    """
    # make sure new id doesn't exist already
    if 'course_id' in mod_params:
        existing_new_id = client.school.courses.find({'course_id': mod_params['course_id']}).count() > 0
        if existing_new_id:
            return False

    # make sure all new students exist
    if 'students' in mod_params and isinstance(mod_params['students'], list):
        students_val = validate_course_student_list(mod_params['students'], client)
        if not students_val:
            return False

    # check name
    if 'name' in mod_params and not isinstance(mod_params['name'], str):
        return False

    # check current id validity
    valid_curr_id = isinstance(curr_id, int)
    return valid_curr_id


def validate_grade_creation_params(student_id, course_id, grade, client: MongoClient):
    """
    checks if the student and course paired with the grade exist, and if
    grade is a valid numeric value.
    """
    # make sure student exists
    existing_student = get_student(student_id, client)
    if existing_student is None:
        logger.info(f"attempted to create grade with non-existing student. sid: {student_id}")
        return False

    # make sure course exists
    existing_course = get_course(course_id, client)
    if existing_course is None:
        logger.info(f"attempted to create grade with non-existing course. cid: {course_id}")
        return False

    # make sure student is enrolled in the course
    enrolled_in = client.school.courses.find_one({'course_id': {'$eq': course_id}, 'students': student_id})
    if not enrolled_in:
        logger.info(f"attempted to add grade for student who is not enrolled in the course.")
        return False

    # make sure grade is a non negative number
    is_numeric = isinstance(grade, int) or isinstance(grade, float)
    is_positive = grade >= 0 if is_numeric else False
    logger.info(f"validating grade. numeric: {is_numeric}, positive: {is_positive}, dependents: ok")
    return is_positive


def validate_grade_modification_params(student_id: int, course_id: int, mod_params: dict, client: MongoClient):
    """
    checks if given modification of a grade is valid with respect to existing students,
    courses and enrollment.
    """
    # make sure current student exists
    existing_student = get_student(student_id, client)
    if existing_student is None:
        logger.info(f"attempted to modify grade of non-existing student. sid: {student_id}")
        return False

    # make sure new student id exists
    new_sid = mod_params.get('student_id', None)
    if new_sid:
        new_existing = get_student(new_sid, client)
        if new_existing is None:
            logger.info(f"attempted to modify grade to non-existing sudent: sid: {new_sid}")
            return False

    # make sure current course exists
    existing_course = get_course(course_id, client)
    if existing_course is None:
        logger.info(f"attempted to create grade with non-existing course. cid: {course_id}")
        return False

    # make sure new course exists and enrollment is sufficient
    new_cid = mod_params.get('course_id', None)
    if new_cid:
        new_existing = get_course(new_cid, client)
        if new_existing is None:
            logger.info(f"attempted to modify grade to non existing course. cid: {new_cid}")
            return False
        # make sure the new student id is enrolled in new course
        elif new_sid not in new_existing['students']:
            logger.info(f"attempted to modify grade to student who isn't enrolled in course. sid: {new_sid}, cid: {new_cid}")
            return False
        # make sure current student id is enrolled
        elif student_id not in new_existing['students']:
            logger.info(f"attempted to modify grade to coure where the student is not enrolled. sid: {student_id}, cid: {new_cid}")

    # make sure grade is a non negative number
    new_grade = mod_params.get('grade', None)
    if new_grade:
        is_numeric = isinstance(new_grade, int) or isinstance(new_grade, float)
        is_positive = new_grade >= 0 if is_numeric else False
        logger.info(f"validating grade. numeric: {is_numeric}, positive: {is_positive}, dependents: ok")
        return is_numeric and is_positive
    else:
        logger.info(f"attempted to modify grade with invalid value. grade: {new_grade}")
        return False


# creation functions
def create_student(id_num: int, first_name: str, last_name: str, email: str, client: MongoClient):
    """
    creates a student document and adds it to the student collection.
    assumes given parameters are valid. checks if given id exists in the
    collection. returns the new student if created, None if not.
    """
    existing_student = get_student(id_num, client)

    # if id is allready in use, return None
    if existing_student:
        logger.info(f"attempted to create existing student with id: {id_num}.")
        return None

    # otherwise, write to the db
    student_object = {'id_number': id_num, 'first_name': first_name, 'last_name': last_name, 'email': email}
    _id = client.school.students.insert_one(student_object).inserted_id

    # add the unique id to the object and return
    student_object['_id'] = str(_id)
    logger.info(f'writing new student to db. id: {id_num}, _id: {str(_id)}')
    return student_object


def create_course(course_id: int, name: str, students: list, client: MongoClient):
    """
    add a course document with given params to the database.
    """
    existing_course = get_course(course_id, client)
    if existing_course:
        logger.info(f"attempted to create existing course. id: {course_id}")
        return None

    # create new course
    new_course = {'course_id': course_id, 'name': name, 'students': students}
    _id = client.school.courses.insert_one(new_course).inserted_id
    new_course['_id'] = str(_id)
    logger.info(f'writing new course to db. id: {course_id}, _id: {str(_id)}')
    return new_course


def create_grade(student_id: int, course_id: int, grade: int, client: MongoClient):
    """
    add a grade to the database, returns None if it already exists.
    """
    # if grade exists, don't overide
    existing_grade = get_grade(student_id, course_id, client)
    if existing_grade:
        logger.info(f"attempted to create existing grade. sid: {student_id}, cid: {course_id}")
        return None

    # create new grade
    new_grade = {'course_id': course_id, 'student_id': student_id, 'grade': grade}
    _id = client.school.grades.insert_one(new_grade).inserted_id
    new_grade['_id'] = str(_id)
    logger.info(f"created new grade. sid: {student_id}, cid: {course_id}, grade: {grade}")
    return new_grade


# update functions
def update_student(id_num: int, new_params: dict, client: MongoClient):
    """
    update the student with the given id numbers with the given params. returns
    updated student if exists, None otherwise.
    """
    required_student = get_student(id_num, client)
    # if student doesn't exist, no update
    if required_student is None:
        logger.info(f"attempted to update non-existing student. id: {id_num}")
        return None

    # update the student with the new values
    student_filter = {'id_number': id_num}
    new_values = {"$set": {**required_student, **new_params}}
    client.school.students.update_one(student_filter, new_values)
    new_student = {k: v for k, v in new_values['$set'].items()}

    # update course enrollment and grades with new id if necessary
    if 'id_number' in new_params and new_params['id_number'] != id_num:
        mod_courses = update_all_student_courses(id_num, new_params['id_number'], client)
        mod_grades = update_all_student_grades(id_num, new_params['id_number'], client)
        logger.info(f"updating student id from {id_num} to {new_params['id_number']}. mod courses: {mod_courses}, mod grades: {mod_grades}")
    logger.info(f"updated existing student: {id_num}")
    return new_student


def update_course(course_id: int, new_params: dict, client: MongoClient):
    """
    update the course with given id with the given params, overwrite existing
    values.
    """
    required_course = get_course(course_id, client)
    if required_course is None:
        logger.info(f"attempted to update non-existing course. cid: {course_id}")
        return None

    # update course with new params
    course_filter = {'course_id': course_id}
    new_values = {"$set": {**required_course, **new_params}}
    client.school.courses.update_one(course_filter, new_values)
    new_course = {k: v for k, v in new_values['$set'].items()}

    # check if students were removed from the course and delete their grades if necessary
    removed_students = set(required_course['students']).difference(set(new_params['students']))
    if len(removed_students) > 0:
        num_grades_deleted = delete_students_grades_from_course(list(removed_students), course_id, client)
        logger.info(f"removing grades for students in course: {course_id}, num_deleted: {num_grades_deleted}")

    # check if course id was changed, and update grades if it was
    num_modified_grades = 0
    if course_id != new_params['course_id']:
        num_modified_grades = update_all_course_grades(course_id, new_params['course_id'], client)
    logger.info(f"updated course. cid: {course_id}, students removed from course: {len(removed_students)}, grades modified: {num_modified_grades}")
    return new_course


def update_grade(student_id: int, course_id: int, new_params: dict, client: MongoClient):
    """
    update the value of a given grade
    """
    required_grade = get_grade(student_id, course_id, client)
    if required_grade is None:
        logger.info(f"attempted to update non-existing grade. sid: {student_id}, cid: {course_id}")
        return None

    grade_filter = {'course_id': course_id, 'student_id': student_id}
    new_values = {"$set": {**required_grade, **new_params}}
    client.school.grades.update_one(grade_filter, new_values)
    new_grade = {k: v for k, v in new_values['$set'].items()}
    logger.info(f"updating grade. sid: {student_id}, cid: {course_id}")
    return new_grade


def update_all_student_courses(student_id: int, new_id: int, client: MongoClient):
    """
    replace the old student id with the new one in all courses
    where the old student id is enrolled.
    """
    db = client.school
    collection = db.courses
    students_courses = collection.find({'students': student_id})
    num_updated = 0
    for c in students_courses:
        # replace used
        current_students = c['students']
        # remove current id
        current_students.pop(current_students.index(student_id))
        # add new id
        current_students.append(new_id)
        # update course document
        client.school.courses.update_one({'course_id': c['course_id']}, {'$set': {'students': current_students}})
        num_updated += 1
    return num_updated


def update_all_student_grades(student_id: int, new_id: int, client: MongoClient):
    """
    replace the old student id with the new one in all the grade listings
    return the number of grades changed.
    """
    db = client.school
    collection = db.grades
    grade_filter = {'student_id': student_id}
    result = collection.update_many(grade_filter, {'$set': {'student_id': new_id}})
    return result.modified_count


def update_all_course_grades(course_id: int, new_id: int,  client: MongoClient):
    """
    update the course id in all relevant grades with the new id.
    """
    db = client.school
    collection = db.grades
    grade_filter = {'course_id': course_id}
    result = collection.update_many(grade_filter, {'$set': {'course_id': new_id}})
    return result.modified_count


# getter function
def get_student(id_num: int, client: MongoClient):
    """
    get the student with the given id from the db, return None
    if it doesn't exist.
    """
    db = client.school
    collection = db.students
    required_student = collection.find_one({'id_number': id_num})
    logger.info(f"getting student with id: {id_num}")
    return required_student


def get_course(course_id: int, client: MongoClient):
    """
    get course document object of given course id
    """
    logger.info(f"getting course id: {course_id}")
    return client.school.courses.find_one({'course_id': course_id})


def get_grade(student_id: int, course_id: int, client: MongoClient):
    """
    get the document of a given grade from db
    """
    logger.info(f"getting grade. sid: {student_id}, cid: {course_id}")
    return client.school.grades.find_one({'course_id': course_id, 'student_id': student_id})


# deletion functions
def delete_student(id_num: int, client: MongoClient):
    """
    delete a student with the given id. delete the students grades
    and remove him from any courses he is enrolled in.
    """
    # check if student exists
    required_student = get_student(id_num, client)
    if required_student is None:
        logger.info(f"attempted to delete non-existing student. id: {id_num}")
        return False

    # delete the student
    client.school.students.delete_one({'id_number': id_num})

    # delete the student from courses he is enrolled in
    num_courses_removed = delete_student_from_courses(id_num, client)

    # delete the grade that are registered for the student
    num_grades_removed = delete_all_student_grades(id_num, client)
    logger.info(f"deleting existing student. id: {id_num}, mod courses: {num_courses_removed}, del grades: {num_grades_removed}")
    return True


def delete_course(course_id: int, client: MongoClient):
    """
    delete from the db the course with given id.
    """
    required_course = get_course(course_id, client)
    if required_course is None:
        logger.info(f"attempted to delete non-existing course. cid: {course_id}")
        return False

    # delete the course
    client.school.courses.delete_one({'course_id': course_id})
    # delete grades associated with the course
    deleted_grades = delete_all_course_grades(course_id, client)
    logger.info(f"deleted course. cid: {course_id}, num grades deleted: {deleted_grades}")
    return True


def delete_grade(student_id: int, course_id: int, client: MongoClient):
    """
    delete the document of a given grade from db
    """
    required_grade = get_grade(student_id, course_id, client)
    if required_grade:
        client.school.grades.delete_one({'course_id': course_id, 'student_id': student_id})
        logger.info(f"deleting grade. sid: {student_id}, cid: {course_id}")
        return True
    else:
        logger.info(f"attempted to delete non-existing grade. sid: {student_id}, cid: {course_id}")
        return False


def delete_all_course_grades(course_id: int, client: MongoClient):
    """
    delete all listed grades with given course id, return number of
    documents that were deleted.
    """
    db = client.school
    collection = db.grades
    result = collection.delete_many({'course_id': {'$eq': course_id}})
    logger.info(f"deleting all grade for course: {course_id}, num_deleted: {result.deleted_count}")
    return result.deleted_count


def delete_all_student_grades(student_id: int, client: MongoClient):
    """
    delete all grades associated with a given student id, return number
    of documents that were deleted.
    """
    db = client.school
    collection = db.grades
    result = collection.delete_many({'student_id': {'$eq': student_id}})
    logger.info(f"deleting all grades for student: {student_id}, num_deleted: {result.deleted_count}")
    return result.deleted_count


def delete_student_from_courses(student_id: int, client: MongoClient):
    """
    remove the student from any course that he is in.
    """
    db = client.school
    collection = db.courses
    students_courses = collection.find({'students': student_id})
    num_deleted = 0
    for c in students_courses:
        # replace used
        current_students = c['students']
        # remove current id
        current_students.pop(current_students.index(student_id))
        # update course document
        client.school.courses.update_one({'course_id': c['course_id']}, {'$set': {'students': current_students}})
        num_deleted += 1
    return num_deleted


def delete_students_grades_from_course(student_ids: list, course_id: int, client: MongoClient):
    """
    remove the the grades of the given students in the given course. return the number
    of grades that were deleted.
    """
    db = client.school
    collection = db.grades
    result = collection.delete_many({'course_id': {'$eq': course_id}, 'student_id': {'$in': student_ids}})
    return result.deleted_count

