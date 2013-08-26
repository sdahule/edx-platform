"""
Utility functions to help with population
"""

from datetime import datetime
from pytz import UTC

from xmodule.course_module import CourseDescriptor
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.inheritance import own_metadata
from queryable.models import Log

def get_assignment_to_problem_map(course_id):
    """
    Returns a dictionary with assignment types/categories as keys and the value is an array of arrays. Each inner array
    holds problem ids for an assignment. The arrays are ordered in the outer array as they are seen in the course, which
    is how they are numbered in a student's progress page.
    """

    course = modulestore().get_instance(course_id, CourseDescriptor.id_to_location(course_id), depth=4)

    assignment_problems_map = {}
    for section in course.get_children():
        for subsection in section.get_children():
            subsection_metadata = own_metadata(subsection)
            if ('graded' in subsection_metadata) and subsection_metadata['graded']:
                category = subsection_metadata['format']
                if category not in assignment_problems_map:
                    assignment_problems_map[category] = []

                problems = []
                for unit in subsection.get_children():
                    for child in unit.get_children():
                        if child.location.category == 'problem':
                            problems.append(child.location.url())

                assignment_problems_map[category].append(problems)

    return assignment_problems_map


def approx_equal(first, second, tolerance=0.0001):
    """
    Checks if first and second are at most the specified tolerance away from each other.
    """
    return abs(first - second) <= tolerance


def pre_run_command(script_id, options, course_id):
    
    print "--------------------------------------------------------------------------------"
    print "Populating queryable.{0} table for course {1}".format(script_id, course_id)
    print "--------------------------------------------------------------------------------"

    # Grab when we start, to log later
    tstart = datetime.now(UTC)

    iterative_populate = True
    last_log_run = {}
    if options['force']:
        print "--------------------------------------------------------------------------------"
        print "Full populate: Forced full populate"
        print "--------------------------------------------------------------------------------"
        iterative_populate = False

    if iterative_populate:
        # Get when this script was last run for this course
        last_log_run = Log.objects.filter(script_id__exact=script_id, course_id__exact=course_id)

        length = len(last_log_run)
        print "--------------------------------------------------------------------------------"
        if length > 0:
            print "Iterative populate: Last log run", last_log_run[0].created
        else:
            print "Full populate: Can't find log of last run"
            iterative_populate = False
        print "--------------------------------------------------------------------------------"
        
    return iterative_populate, tstart, last_log_run