import getopt
import os
import subprocess
import sys
import zipfile
from datetime import datetime

import requests

BASE_PATH = os.path.normpath(os.path.dirname(__file__))
DATA_DIR_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), 'data'))
PROJECT_DIR = ''
PROJECT_ID = ''


def parse_arguments(argv):
    project_dir = ''
    project_id = ''
    try:
        opts, args = getopt.getopt(argv, "h:p:i:", ["project-dir=", "project-id="])
    except getopt.GetoptError:
        print('index_generator_chain_runner.py --project-dir <project-dir> --project-id <project-id>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('index_generator_chain_runner.py --project-dir <project-dir> --project-id <project-id>')
            sys.exit()
        elif opt in ("-p", "--project-dir"):
            project_dir = arg
        elif opt in ("-i", "--project-id"):
            project_id = arg
    return project_dir, project_id


def get_commit_id():
    process = subprocess.Popen(["git", "show", "-s", "--format=%H"], cwd=PROJECT_DIR, stdout=subprocess.PIPE)
    stdout, stderr = process.communicate()
    return str(stdout).replace('b\'', '').replace('\\n\'', '')


def execute_docker_operation():
    process = subprocess.Popen(["docker", "run",
                                "-v", PROJECT_DIR + ":/var/project",
                                "-v", DATA_DIR_PATH + ":/shared-index/output",
                                "-e", "COMMIT_ID=" + commit_id,
                                "-e", "PROJECT_ID=" + PROJECT_ID,
                                "damintsew/indexer-2021.2.3"],
                               cwd=".",
                               stdout=subprocess.PIPE,
                               # env=d,
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


def remove_files(path):
    for root, dirs, files in os.walk(path):
        for file in files:
            os.remove(os.path.relpath(os.path.join(path, file)))


if __name__ == "__main__":
    PROJECT_DIR, PROJECT_ID = parse_arguments(sys.argv[1:])

commit_id = get_commit_id()

print('PROJECT_DIR = ' + PROJECT_DIR)
print('PROJECT_ID = ' + PROJECT_ID)
print('CommitId = ' + commit_id)

print('Started Indexing ' + datetime.now().strftime("%H:%M:%S"))
execute_docker_operation()
print('Finished Indexing ' + datetime.now().strftime("%H:%M:%S"))

zipf = zipfile.ZipFile('data_to_send\\index.zip', 'w', zipfile.ZIP_DEFLATED)
zipdir(DATA_DIR_PATH, zipf)
zipf.close()

with open("data_to_send\\index.zip", "rb") as a_file:
    file_dict = {"file": a_file}
    # response = requests.post("http://localhost:8125/manage/upload",
    #                          params={'commitId': commit_id, 'projectId': PROJECT_ID},
    #                          files=file_dict)
    response = requests.post("http://10.216.1.51:8125/manage/upload",
                             params={'commitId': commit_id, 'projectId': PROJECT_ID},
                             timeout=600,
                             files=file_dict)
    print(response)

remove_files(DATA_DIR_PATH)
remove_files(BASE_PATH + '/data_to_send')
