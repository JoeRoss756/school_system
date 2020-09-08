from utils import logging_utils
import logging
from redis import Redis
import json

# instantiate logger
logger = logging.getLogger(__name__)


def setup_caching_struct(r: Redis):
    # create hash for best student
    ret1 = r.hset("best_student", "valid", 0)
    logger.info(f"created hash for best student. num items written: {ret1}")

    # create hash for easiest course
    ret2 = r.hset("easiest_course", "valid", 0)
    logger.info(f"created hash for easiest course. num items written: {ret2}")
    return


def update_best_student_cache(student: dict, r: Redis):
    student['valid'] = 1
    r.hmset("best_student", {k: v for k, v in student.items() if k != '_id'})
    return


def update_easiest_course_cache(course: dict, r: Redis):
    course['valid'] = 1
    course['students'] = json.dumps(course['students'])
    r.hmset("easiest_course", {k: v for k, v in course.items() if k != '_id'})
    return


def invalidate_best_student_cache(r: Redis):
    r.hset("best_student", "valid", 0)
    return


def invalidate_easiest_course_cache(r: Redis):
    r.hset("easiest_course", "valid", 0)
    return


def invalidate_all_caches(r: Redis):
    invalidate_best_student_cache(r)
    invalidate_easiest_course_cache(r)
    return


def get_best_student_from_cache(r: Redis):
    cached_student = r.hgetall("best_student")
    is_valid = int(cached_student[b'valid'].decode('utf-8'))
    if is_valid:
        decode_student = {k.decode('utf-8'): v.decode('utf-8') for k,v in cached_student.items()}
        decode_student.pop("valid")
        return decode_student
    else:
        return None


def get_easiest_course_from_cache(r: Redis):
    cached_course = r.hgetall("easiest_course")
    is_valid = int(cached_course[b'valid'].decode('utf-8'))
    if is_valid:
        decode_course = {k.decode('utf-8'): v.decode('utf-8') for k, v in cached_course.items() if k.decode('utf-8') != 'valid'}
        decode_course['students'] = json.loads(decode_course['students'])
        return decode_course
    else:
        return None