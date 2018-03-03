#!/usr/bin/env python3
"""
Author: Rahul Nanda
Date: 2 March 2018
"""
import subprocess
import pyunpack
import os
import re
import shutil
import configparser

config = configparser.ConfigParser()
config.read('config.ini')
ASSIGNMENT_DIRECTORY_PATH = config['DEFAULT']['assignment_directory_path']
SUBMISSION_FILE_NAME = config['DEFAULT']['submission_file_name']

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
        #if len(os.listdir(file_path)) == 0:
        #    continue
        if SUBMISSION_FILE_NAME not in os.listdir(file_path):
            print(file_path, os.listdir(file_path))
            faulty_user_dir_list.append(file_path)
    return faulty_user_dir_list


def copy_target_to_root_user_directory(root_user_dir_path):
    if not os.path.exists(root_user_dir_path):
        raise Exception("Invalid Directory path: %s" % root_user_dir_path)
    if not os.path.isdir(root_user_dir_path):
        raise Exception("Not a directory: %s" % root_user_dir_path)
    current_dir = root_user_dir_path
    dfs_stack = [root_user_dir_path]
    while len(dfs_stack) > 0:
        current_dir = dfs_stack.pop()
        for filename in os.listdir(current_dir):
            file_path = os.path.join(current_dir, filename)
            if os.path.isdir(file_path):
                dfs_stack.append(file_path)
                continue
            if current_dir == root_user_dir_path:
                continue
            # Move all java files to root_user_dir_path
            if file_path.endswith('.java'):
                shutil.copy(file_path, root_user_dir_path)
                print("Copied file %s to root_user_dir: %s" %(file_path, root_user_dir_path))


def fix_faulty_user_directories(faulty_user_dir_list):
    for faulty_user_dir_path in faulty_user_dir_list:
        copy_target_to_root_user_directory(faulty_user_dir_path)


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
        if filename.endswith(SUBMISSION_FILE_NAME):
            shutil.copy(file_path, os.path.join(user_dir_path, SUBMISSION_FILE_NAME))
            # print("Copied java file for user: %s" % user_id)
            continue
        # Try extracting files to the corresponding user directory
        try:
            pyunpack.Archive(file_path).extractall(user_dir_path)
        except Exception as e:
            print(e)
            count_failed += 1
            unpack_failed_users.append(user_id)
    print("Total failed to unpack count: %d" % count_failed)
    print("Unpacking failed for users: ", unpack_failed_users)


if __name__ == "__main__":
    print("total user submissions: %d" % find_unique_user_count())
    create_user_directories()
    faulty_user_dir_list = check_faulty_user_directories()
    print("Faulty user directories", faulty_user_dir_list)
    print("\n\n** Will Try Fixing **")
    fix_faulty_user_directories(faulty_user_dir_list)
    faulty_user_dir_list = check_faulty_user_directories()
    print("Faulty user directories", faulty_user_dir_list)



