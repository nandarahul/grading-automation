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
AUX_FILES_PATH = [gf.strip() for gf in config['DEFAULT']['aux_files'].split(',')]
GRADER_FILE_PATH = config['DEFAULT']['grader_file'].strip()
GRADER_FILENAME = os.path.basename(GRADER_FILE_PATH)
RESULT_FILE_NAME = config['DEFAULT']['result_file_name'].strip()
BB_FILENAME_FORMAT = '[a-zA-Z0-9\s]+_(?P<userid>[a-zA-Z0-9]+)_(\S)*'

regex_pattern_object = re.compile(BB_FILENAME_FORMAT)
DID_NOT_FOLLOW_GUIDELINES_FILE = config['DEFAULT']['guidelines_file'].strip()


def append_to_file(filename, text):
    fh = open(filename, mode='a')
    fh.write(text + '\n')
    fh.close()


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
    user_followed_guidelines = True
    if not os.path.exists(root_user_dir_path):
        raise Exception("Invalid Directory path: %s" % root_user_dir_path)
    if not os.path.isdir(root_user_dir_path):
        raise Exception("Not a directory: %s" % root_user_dir_path)
    current_dir = root_user_dir_path
    count_total_dirs = 1
    dfs_stack = [root_user_dir_path]
    while len(dfs_stack) > 0:
        current_dir = dfs_stack.pop()
        for filename in os.listdir(current_dir):
            file_path = os.path.join(current_dir, filename)
            if os.path.isdir(file_path):
                dfs_stack.append(file_path)
                count_total_dirs += 1
                continue
            if current_dir == root_user_dir_path:
                continue
            # Move all java files to root_user_dir_path
            if file_path.endswith('.java'):
                if not file_path.endswith(SUBMISSION_FILE_NAME):
                    user_followed_guidelines = False
                shutil.copy(file_path, root_user_dir_path)
                print("Copied file %s to root_user_dir: %s" %(file_path, root_user_dir_path))
    if count_total_dirs > 2:
        user_followed_guidelines = False
    if not user_followed_guidelines:
        append_to_file(DID_NOT_FOLLOW_GUIDELINES_FILE, os.path.basename(os.path.normpath(root_user_dir_path)))


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
        # Try extracting files to the corresponding user directory
        try:
            pyunpack.Archive(file_path).extractall(user_dir_path)
        except Exception as e:
            if filename.endswith(SUBMISSION_FILE_NAME):
                shutil.copy(file_path, os.path.join(user_dir_path, SUBMISSION_FILE_NAME))
                append_to_file(DID_NOT_FOLLOW_GUIDELINES_FILE, user_id)
                # print("Copied java file for user: %s" % user_id)
                continue
            print(e)
            count_failed += 1
            unpack_failed_users.append(user_id)
    print("Total failed to unpack count: %d" % count_failed)
    print("Unpacking failed for users: ", unpack_failed_users)


def move_txt_files_to_user_directories():
    count = 0
    for filename in os.listdir(ASSIGNMENT_DIRECTORY_PATH):
        file_path = os.path.join(ASSIGNMENT_DIRECTORY_PATH, filename)
        if os.path.isdir(file_path):
            continue
        if filename.endswith('.txt'):
            user_id = extract_userid_from_filename(filename)
            shutil.move(file_path, os.path.join(ASSIGNMENT_DIRECTORY_PATH, user_id))
            count += 1
    print("Moved %d txt files to corresponding user directories" % count)

def copy_grading_files_to_user_directories():
    count = 0
    for filename in os.listdir(ASSIGNMENT_DIRECTORY_PATH):
        file_path = os.path.join(ASSIGNMENT_DIRECTORY_PATH, filename)
        if not os.path.isdir(file_path):
            continue
        for aux_file in AUX_FILES_PATH:
            shutil.copy(aux_file, file_path)
        shutil.copy(GRADER_FILE_PATH, file_path)
        count += 1
    print("Copied grading files to %d user dirs" % count)


def run_grader(delete_exisiting_result=False):
    print("\n\nGrader Running...")
    timeout_users, compilation_failed_users, unknown_exception_users = [], [], []
    for filename in os.listdir(ASSIGNMENT_DIRECTORY_PATH):
        file_path = os.path.join(ASSIGNMENT_DIRECTORY_PATH, filename)
        if not os.path.isdir(file_path):
            continue
        print("** User: %s **" % filename)
        if RESULT_FILE_NAME in os.listdir(file_path):
            print("result file already exists.")
            if delete_exisiting_result:
                print("Deleting..")
                os.remove(os.path.join(file_path, RESULT_FILE_NAME))
            else:
                print("Skipping..")
                continue
        try:
            subprocess.check_output(['javac', '-classpath', file_path, os.path.join(file_path, GRADER_FILENAME)], timeout=5)
            subprocess.check_output(['java', '-classpath', file_path, GRADER_FILENAME.split('.')[0], file_path], timeout=15)
        except subprocess.CalledProcessError as e:
            print("\n\n** User: %s **" % filename)
            print(e)
            compilation_failed_users.append(filename)
        except subprocess.TimeoutExpired as e:
            print(e)
            timeout_users.append(filename)
        except Exception as e:
            print(e)
            unknown_exception_users.append(filename)
    print("Timeout users count: %d \n " % len(timeout_users), timeout_users)
    print("compilation failed users count: %d \n " % len(compilation_failed_users), compilation_failed_users)
    print("Unknown exception users count: %d \n " % len(unknown_exception_users), unknown_exception_users)


def test_script_success():
    count, failed_script_users = 0, []
    for filename in os.listdir(ASSIGNMENT_DIRECTORY_PATH):
        file_path = os.path.join(ASSIGNMENT_DIRECTORY_PATH, filename)
        if not os.path.isdir(file_path):
            continue
        if RESULT_FILE_NAME in os.listdir(file_path):
            count += 1
        else:
            failed_script_users.append(filename)
    print("Script successful for %d users" % count)
    with open("compilation_failed_users.txt", 'w') as fh:
        for fsu in failed_script_users:
            fh.write(fsu + '\n')
    print(failed_script_users)

if __name__ == "__main__":
    append_to_file(DID_NOT_FOLLOW_GUIDELINES_FILE, "*** New Run ***")
    print("total user submissions: %d" % find_unique_user_count())
    #create_user_directories()
    #faulty_user_dir_list = check_faulty_user_directories()
    #print("Faulty user directories", faulty_user_dir_list)
    #print("\n\n** Will Try Fixing **")
    #fix_faulty_user_directories(faulty_user_dir_list)
    faulty_user_dir_list = check_faulty_user_directories()
    print("Faulty user directories", faulty_user_dir_list)
    #copy_grading_files_to_user_directories()
    run_grader()
    #move_txt_files_to_user_directories()
    test_script_success()
