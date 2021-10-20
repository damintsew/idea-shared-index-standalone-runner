import argparse
import os
import subprocess
import sys
import zipfile
from datetime import datetime
from os import path

import requests


def parse_arguments():
    parser = argparse.ArgumentParser(description='index_generator_chain_runner.py --project-dir <project-dir> '
                                                 '--project-id <project-id>')
    parser.add_argument('-pd', '--project-dir', help='Project directory for indexing ', required=True)
    parser.add_argument('-pi', '--project-id', help='Project Id', required=True)
    # parser.add_argument('-pi', '--project-id', help='Project Id', required=True)
    args = parser.parse_args()

    return args.project_dir, args.project_id


def get_commit_id():
    process = subprocess.Popen(["git", "show", "-s", "--format=%H"], cwd=project_dir, stdout=subprocess.PIPE)
    stdout, stderr = process.communicate()
    return str(stdout).replace('b\'', '').replace('\\n\'', '')


def execute_docker_operation():
    process = subprocess.Popen(["docker", "run",
                                "-v", project_dir + ":/var/project",
                                "-v", DATA_DIR_PATH + ":/shared-index/output",
                                "-e", "COMMIT_ID=" + commit_id,
                                "-e", "PROJECT_ID=" + project_id,
                                "damintsew/indexer-2021.2.3"],
                               cwd=".", stdout=subprocess.PIPE,
                               universal_newlines=True)
    while True:
        output = process.stdout.readline()
        print(output.strip())
        return_code = process.poll()
        if return_code is not None:
            print('RETURN CODE', return_code)
            # Process has finished, read rest of the output
            for output in process.stdout.readlines():
                print(output.strip())
            break


def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file),
                       os.path.relpath(os.path.join(root, file),
                                       os.path.join(path, '.')))


def remove_files(base_path):
    for root, dirs, files in os.walk(base_path):
        for file in files:
            os.remove(os.path.relpath(os.path.join(base_path, file)))


BASE_PATH = path.normpath(path.dirname(__file__))
DATA_DIR_PATH = path.normpath(path.join(path.dirname(__file__), 'data'))
DATA_TO_SEND_DIR_PATH = path.normpath(path.join(path.dirname(__file__), 'data_to_send'))

project_dir, project_id = parse_arguments()
commit_id = get_commit_id()

print('project_dir = ' + project_dir)
print('project_id = ' + project_id)
print('commit_id = ' + commit_id)

print('Started Indexing ' + datetime.now().strftime("%H:%M:%S"))
execute_docker_operation()
print('Finished Indexing ' + datetime.now().strftime("%H:%M:%S"))

zipf = zipfile.ZipFile('data_to_send\\index.zip', 'w', zipfile.ZIP_DEFLATED)
zipdir(DATA_DIR_PATH, zipf)
zipf.close()

with open(DATA_TO_SEND_DIR_PATH, "rb") as a_file:
    file_dict = {"file": a_file}
    response = requests.post("http://10.216.1.51:8125/manage/upload",
                             params={'commitId': commit_id, 'projectId': project_id},
                             timeout=600,
                             files=file_dict)
    print(response)

remove_files(DATA_DIR_PATH)
remove_files(DATA_TO_SEND_DIR_PATH)
