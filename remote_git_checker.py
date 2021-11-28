from git import Repo
import argparse

import chain_runner


def parse_arguments():
    parser = argparse.ArgumentParser(description='index_generator_chain_runner.py --project-dir <project-dir> '
                                                 '--project-id <project-id> --branch <remote branch to watch>')
    parser.add_argument('-pd', '--project-dir', help='Project directory for indexing ', required=True)
    parser.add_argument('-pi', '--project-id', help='Project Id', required=True)
    parser.add_argument('-b', '--branch', help='Branch', required=False)
    args = parser.parse_args()

    return args.project_dir, args.project_id, args.branch


repo_directory, project_id, branch = parse_arguments()

print('project_dir = ' + repo_directory)
print('project_id = ' + project_id)

repo = Repo(repo_directory)

repo.git.checkout("develop")
repo.remotes.origin.fetch()
commits_behind = repo.iter_commits('develop..develop@{u}')
commits = list(commits_behind)

if len(commits) == 0:
    print("Current branch is {} behind. Pulling new code".format(len(commits)))
    repo_is_dirty = repo.is_dirty()
    if repo_is_dirty:
        print("Dirty")
        print("Stashing...")
        repo.git.stash('save')

    repo.remotes.origin.pull()
    chain_runner.generate_index_and_send(repo_directory, project_id)

    if repo_is_dirty:
        print("unstashing")
        repo.git.stash('pop')
else:
    print("No updates nothing to do here")
