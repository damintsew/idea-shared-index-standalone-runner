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
    args = parser.parse_args()

    return args.project_dir, args.project_id


def get_commit_id(project_dir):
    process = subprocess.Popen(["git", "show", "-s", "--format=%H"], cwd=project_dir, stdout=subprocess.PIPE)
    stdout, stderr = process.communicate()
    return str(stdout).replace('b\'', '').replace('\\n\'', '')


def execute_docker_operation(project_dir, project_id, commit_id):
    process = subprocess.Popen(["docker", "run",
                                "-v", project_dir + ":/var/project",
                                "-v", data_dir_path + ":/shared-index/output",
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


def zip_file():
    zipped_file_path = path.normpath(path.join(data_to_send_dir_path, 'index.zip'))
    zipf = zipfile.ZipFile(zipped_file_path, 'w', zipfile.ZIP_DEFLATED)
    zipdir(data_dir_path, zipf)
    zipf.close()

    return zipped_file_path


def send_file(zipped_file, commit_id, project_id):
    with open(zipped_file, "rb") as a_file:
        file_dict = {"file": a_file}
        response = requests.post("http://10.216.1.51:8125/manage/upload",
                                 params={'commitId': commit_id, 'projectId': project_id},
                                 timeout=600,
                                 files=file_dict)
        print(response)


def generate_index_and_send(project_dir, project_id):
    global data_dir_path, data_to_send_dir_path

    # BASE_PATH = path.normpath(path.dirname(__file__))
    data_dir_path = path.normpath(path.join(path.dirname(__file__), 'data'))
    data_to_send_dir_path = path.normpath(path.join(path.dirname(__file__), 'data_to_send'))

    os.makedirs(data_dir_path, exist_ok=True)
    os.makedirs(data_to_send_dir_path, exist_ok=True)

    commit_id = get_commit_id(project_dir)
    print('project_dir = ' + project_dir)
    print('project_id = ' + project_id)
    print('commit_id = ' + commit_id)
    print('Started Indexing ' + datetime.now().strftime("%H:%M:%S"))
    execute_docker_operation(project_dir, project_id, commit_id)
    print('Finished Indexing ' + datetime.now().strftime("%H:%M:%S"))

    zipped_file = zip_file()
    send_file(zipped_file, commit_id, project_id)
    remove_files(data_dir_path)
    remove_files(data_to_send_dir_path)


# generate_index_and_send()
