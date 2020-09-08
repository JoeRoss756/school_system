from flask import Flask, jsonify, request, make_response
import redis
import yaml
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

from utils import dbutils
from utils import stats_utils
from utils import logging_utils
from utils import redis_utils
import logging

# create flask app
app = Flask(__name__)

# load configuration
config = yaml.load(open('config.yml'), Loader=yaml.Loader)

# instantiate logger
logger = logging.getLogger(__name__)

# create mongo client
mongo_client = MongoClient(**config['mongo'])

# setup caching structures
redis_client = redis.Redis(host=config['redis']['host'], port=config['redis']['port'])
redis_utils.setup_caching_struct(redis_client)


@app.route('/', methods=['GET'])
def main_page():
    # test connection to redis
    r = redis.Redis(host=config['redis']['host'], port=config['redis']['port'])
    try:
        ret = r.mset({'test': 'checking redis, if this returns, success!'})
    except ConnectionError:
        ret = False
    r.close()

    # test connection to mongodb
    try:
        # The ismaster command is cheap and does not require auth.
        mongo_client.admin.command('ismaster')
        status = True
    except ConnectionError:
        status = False

    # return html showing status of mongo and redis
    return f"<b>redis</b>: {'on' if ret else 'error'}<br><b>mongo:</b> {'on' if status else 'error'}"


@app.route('/students', methods=['POST'])
def create_student():
    # unpack student params from request
    id_num, first_name, last_name, email = dbutils.unpack_student_create_params(request)

    # validate params
    is_valid = dbutils.validate_student_creation_params(id_num, first_name, last_name, email)
    if not is_valid:
        return make_response(jsonify({'error': 'invalid data was given for creating a student.'}), 404)

    # create the student
    new_student = dbutils.create_student(id_num, first_name, last_name, email, mongo_client)
    if new_student is None:
        return make_response(jsonify({'error': 'given id for student already exists.'}, 404))
    else:
        logger.info(f"creating student: {id_num}, invalidating caches.")
        redis_utils.invalidate_all_caches(redis_client)
        return make_response(jsonify({'new_student_id': id_num}), 200)


@app.route('/students', methods=['GET'])
def get_student():
    # unpack student id from body
    id_num = int(request.args.get('id_number', None))
    if id_num is None:
        return make_response(jsonify({'error': 'student id was not given in url.'}), 404)

    # get student from db
    requested_student = dbutils.get_student(id_num, mongo_client)
    if requested_student:
        requested_student['_id'] = str(requested_student['_id'])
        return make_response(jsonify(requested_student), 200)
    else:
        return make_response(jsonify({'error': f'student with given id: {id_num} was not found.'}), 404)


@app.route('/students', methods=['PUT'])
def update_student():
    # unpack student params from request
    id_num, new_params = dbutils.unpack_student_modify_params(request)

    # validate params
    is_valid = dbutils.validate_student_modification_params(id_num, new_params, mongo_client)
    if not is_valid:
        return make_response(jsonify({'error': 'invalid data was given for creating a student.'}), 404)

    # update the student
    updated_student = dbutils.update_student(id_num, new_params, mongo_client)
    if updated_student:
        updated_student['_id'] = str(updated_student['_id'])
        redis_utils.invalidate_all_caches(redis_client)
        logger.info(f"updating student: {id_num}, invalidating cache.")
        return make_response(jsonify(updated_student), 200)
    else:
        return make_response(jsonify({'error': f'student with given id: {id_num} was not found.'}), 404)


@app.route('/students', methods=['DELETE'])
def delete_student():
    id_num = request.json.get('id_number', None)
    if id_num is None:  # attempting id doesn't exist
        return make_response(jsonify({'error': 'student id was not given'}), 404)

    # delete the student, his grades and his enrollment.
    deleted = dbutils.delete_student(id_num, mongo_client)
    if deleted:
        redis_utils.invalidate_all_caches(redis_client)
        logger.info(f"deleting student: {id_num}, invalidating cache.")
        return make_response(jsonify({'deleted_student_id:': id_num}), 200)
    else:
        return make_response(jsonify({'error': f'student with given id: {id_num} was not found.'}), 404)


@app.route('/courses', methods=['POST'])
def create_course():
    # unpack params
    course_id, name, students = dbutils.unpack_course_creation_params(request)

    # validate params
    is_valid = dbutils.validate_course_creation_params(course_id, name, students, mongo_client)
    if not is_valid:
        return make_response(jsonify({'error': 'invalid data was given for creating a course'}), 404)

    # create course
    new_course = dbutils.create_course(course_id, name, students, mongo_client)
    if new_course is None:
        return make_response(jsonify({'error': 'given id for course already exists'}), 404)
    else:
        logger.info(f"created new course: {new_course['course_id']}")
        return make_response(jsonify({'new_course_id': new_course['course_id']}))


@app.route('/courses', methods=['GET'])
def get_course():
    # unpack student id from body
    course_id = int(request.args.get('course_id', None))
    if course_id is None:
        return make_response(jsonify({'error': 'course id was not given in url'}), 404)

    requested_course = dbutils.get_course(course_id, mongo_client)
    if requested_course:
        requested_course['_id'] = str(requested_course['_id'])
        return make_response(jsonify(requested_course), 200)
    else:
        return make_response(jsonify({'error': f'course with id {course_id} was not found.'}), 404)


@app.route('/courses', methods=['PUT'])
def update_course():
    # unpack params
    course_id, new_params = dbutils.unpack_course_modification_params(request)

    # validate params
    is_valid = dbutils.validate_course_modification_params(course_id, new_params, mongo_client)
    if not is_valid:
        return make_response(jsonify({'error': 'invalid data was given for creating a course'}), 404)

    # update course
    updated_course = dbutils.update_course(course_id, new_params, mongo_client)
    if updated_course:
        updated_course['_id'] = str(updated_course['_id'])
        redis_utils.invalidate_all_caches(redis_client)
        logger.info(f"updating course: {course_id}, invalidating cache.")
        return make_response(jsonify(updated_course), 200)
    else:
        return make_response(jsonify({'error': f'course with id {course_id} was not found.'}), 404)


@app.route('/courses', methods=['DELETE'])
def delete_course():
    # unpack course id from request
    course_id = request.json.get('course_id', None)
    if course_id is None:
        return make_response(jsonify({'error': 'course id was not given'}), 404)

    deleted = dbutils.delete_course(course_id, mongo_client)
    if deleted:
        redis_utils.invalidate_all_caches(redis_client)
        logger.info(f"deleting course: {course_id}, invalidating cache.")
        return make_response(jsonify({'deleted_course_id': course_id}))
    else:
        return make_response(jsonify({'error': f'course with id {course_id} was not found.'}), 404)


@app.route('/grades', methods=['POST'])
def create_grade():
    # unpack
    student_id, course_id, grade = dbutils.unpack_grade_creation_params(request)

    # validate params
    is_valid = dbutils.validate_grade_creation_params(student_id, course_id, grade, mongo_client)
    if not is_valid:
        return make_response(jsonify({'error': 'invalid data was given for creating a grade.'}), 404)

    # create the student
    new_grade = dbutils.create_grade(student_id, course_id, grade, mongo_client)
    if new_grade is None:
        return make_response(jsonify({'error': 'given id for grade already exists.'}, 404))
    else:
        redis_utils.invalidate_all_caches(redis_client)
        logger.info(f"new grade was created, sid: {student_id}, cid: {course_id}. invalidating cache.")
        return make_response(jsonify({'new_grade_student_id': student_id, 'new_grade_course_id': course_id}), 200)


@app.route('/grades', methods=['GET'])
def get_grade():
    # unpack grade identifiers
    course_id = int(request.args.get('course_id', None))
    student_id = int(request.args.get('student_id', None))
    if course_id is None or student_id is None:
        return make_response(jsonify({'error': 'course and student id were not given in url.'}), 404)

    # get the grade
    requested_grade = dbutils.get_grade(student_id, course_id, mongo_client)
    if requested_grade:
        requested_grade['_id'] = str(requested_grade['_id'])
        return make_response(jsonify(requested_grade), 200)
    else:
        return make_response(jsonify({'error': f'grade with student id {student_id} and course id {course_id} was not found.'}), 404)


@app.route('/grades', methods=['PUT'])
def update_grade():
    # unpack params
    current_sid, current_cid, new_params = dbutils.unpack_grade_modification_params(request)

    # validate params
    is_valid = dbutils.validate_grade_modification_params(current_sid, current_cid, new_params, mongo_client)
    if not is_valid:
        return make_response(jsonify({'error': 'invalid data was given for updating a grade.'}), 404)

    # update grade
    updated_grade = dbutils.update_grade(current_sid, current_sid, new_params, mongo_client)
    if updated_grade:
        updated_grade['_id'] = str(updated_grade['_id'])
        redis_utils.invalidate_all_caches(redis_client)
        logger.info(f"updating grade, invalidating cache. sid: {updated_grade['student_id']}, cid: {updated_grade['course_id']}")
        return make_response(jsonify(updated_grade), 200)
    else:
        return make_response(jsonify({'error': f'grade with sid: {current_sid} and cid: {current_cid} was not found.'}), 404)


@app.route('/grades', methods=['DELETE'])
def delete_grade():
    # unpack student and course id
    student_id = request.json.get('student_id', None)
    course_id = request.json.get('course_id', None)
    if student_id is None or course_id is None:
        return make_response(jsonify({'error': 'student and course ids were not given.'}))

    # delete the grade
    deleted = dbutils.delete_grade(student_id, course_id, mongo_client)
    if deleted:
        # invalidate cache
        redis_utils.invalidate_all_caches(redis_client)
        logger.info(f"deleting grade, sid: {student_id}, cid: {course_id}, invalidating cache.")
        return make_response(jsonify({'deleted_grade_sid': student_id, 'deleted_grade_cid': course_id}), 200)
    else:
        return make_response(jsonify({'error': f'grade with sid: {student_id} and cid: {course_id} was not found.'}), 404)


@app.route('/best_student', methods=['GET'])
def get_best_student():
    # check if best student is cached
    cached_student = redis_utils.get_best_student_from_cache(redis_client)
    if cached_student:
        logger.info("returning best student from cache.")
        return make_response(jsonify(cached_student))

    # if cache is invalid, get from db
    best_student_id = stats_utils.get_best_student_id(mongo_client)
    if best_student_id is None:
        logger.info(f"attempting to get best student with no grades saved.")
        return make_response(jsonify({'error': 'no grades are listed in the system.'}), 404)

    # get student
    best_student = dbutils.get_student(best_student_id, mongo_client)
    best_student['_id'] = str(best_student['_id'])

    # update cache
    redis_utils.update_best_student_cache(best_student, redis_client)
    return make_response(jsonify(best_student), 200)


@app.route('/easiest_course', methods=['GET'])
def get_easiest_course():
    # check if course is cached
    cached_course = redis_utils.get_easiest_course_from_cache(redis_client)
    if cached_course:
        logger.info("returning easiest course from cache.")
        return make_response(jsonify(cached_course))

    # if cache is invalid, get from db
    easiest_course_id = stats_utils.get_easiest_course_id(mongo_client)
    if easiest_course_id is None:
        logger.info(f"attempting to get easiest course with no grades saved.")
        return make_response(jsonify({'error': 'no grades are listed in the system.'}))

    # get course info
    easiest_course = dbutils.get_course(easiest_course_id, mongo_client)
    easiest_course['_id'] = str(easiest_course['_id'])
    redis_utils.update_easiest_course_cache(easiest_course, redis_client)
    return make_response(jsonify(easiest_course), 200)


app.run(debug=config['app']['debug'], host="0.0.0.0", port=config['app']['port'])
