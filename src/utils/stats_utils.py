from pymongo import MongoClient
from utils.logging_utils import logging

# instantiate logger
logger = logging.getLogger(__name__)


def get_easiest_course_id(client: MongoClient):
    """
    returns the course_id of the course with the highest average
    of all the courses in the db.
    """
    group = {"$group": {"_id": "$course_id", "avg": {"$avg": "$grade"}}}
    sort = {"$sort": {"avg": -1}}
    agg_pipe = [group, sort]
    agg_result = client.school.grades.aggregate(agg_pipe)
    try:
        easiest_course = agg_result.next()
        logger.info(f"returning easiest course: {easiest_course}")
        return easiest_course['_id']
    except StopIteration:  # no grades are listed
        logger.info(f"query for easiest course returned no results.")
        return None


def get_best_student_id(client: MongoClient):
    """
    returns the student_id of the student with the highest
    average in the school. if no grades are listed, will return
    None.
    """
    aggregation_pipeline = [{"$group":
                                 {"_id": "$student_id", "avg":
                                     {"$avg": "$grade"}
                                  }
                             },
                            {"$sort":
                                 {"avg": -1}
                             }
                            ]
    agg_result = client.school.grades.aggregate(aggregation_pipeline)
    try:
        best_student = agg_result.next()
        return best_student['_id']
    except StopIteration:  # no grades are listed
        return None
