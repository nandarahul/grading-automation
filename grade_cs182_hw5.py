import subprocess
import pyunpack
import os
import re
import shutil
ASSIGNMENT_DIRECTORY_PATH = "/Users/rahul/Documents/CS182/hw5/grading/"
BB_FILENAME_FORMAT = '[a-zA-Z0-9\s]+_(?P<userid>[a-zA-Z0-9]+)_(\S)*'

regex_pattern_object = re.compile(BB_FILENAME_FORMAT)
"""
- handle other compressed formats   
"""

def extract_userid_from_filename(filename):
    match_obj = regex_pattern_object.match(filename)
    if match_obj is None:
        print("**Couldn't parse filename: %s" % filename)
        return None
    return match_obj.group('userid')


def find_unique_user_count():
    userid_set = set([])
    for filename in os.listdir(ASSIGNMENT_DIRECTORY_PATH):
        file_path = os.path.join(ASSIGNMENT_DIRECTORY_PATH, filename)
        if os.path.isdir(file_path):
            continue
        user_id = extract_userid_from_filename(filename)
        if user_id is None:
            continue
        userid_set.add(user_id)
    return len(userid_set)


def check_faulty_user_directories():
    faulty_user_dir_list = []
    for filename in os.listdir(ASSIGNMENT_DIRECTORY_PATH):
        file_path = os.path.join(ASSIGNMENT_DIRECTORY_PATH, filename)
        if not os.path.isdir(file_path):
            continue
        if "Treasure.java" not in os.listdir(file_path):
            faulty_user_dir_list.append(filename)
    return faulty_user_dir_list


def create_user_directories():
    count_failed, count_java = 0, 0
    unpack_failed_users = []
    for filename in os.listdir(ASSIGNMENT_DIRECTORY_PATH):
        file_path = os.path.join(ASSIGNMENT_DIRECTORY_PATH, filename)
        if os.path.isdir(file_path) or filename.endswith('.txt'):
            continue

        user_id = extract_userid_from_filename(filename)
        if user_id is None:
            continue
        user_dir_path = os.path.join(ASSIGNMENT_DIRECTORY_PATH, user_id)
        if not os.path.exists(user_dir_path):
            os.makedirs(user_dir_path)
        if len(os.listdir(user_dir_path)) > 0:
            continue
        if filename.endswith("Treasure.java"):
            shutil.(file_path, os.path.join(user_dir_path, 'Treasure.java'))
            print("Copied java file for user: %s" % user_id)
            #count_java += 1
            #print("Java count: %d" % count_java)

            continue

        """
        Try extracting files to the corresponding user directory
        """
        try:
            pyunpack.Archive(file_path).extractall(user_dir_path)
        except Exception as e:
            #print(e)
            count_failed += 1
            #print(count_failed)
            unpack_failed_users.append(user_id)
    print("Total failed to unpack count: %d" % count_failed)
    print("Unpacking failed for users: ", unpack_failed_users)

if __name__ == "__main__":
    print("total user submissions: %d" % find_unique_user_count())
    create_user_directories()
    print("Faulty user directories", check_faulty_user_directories())


