import argparse
import chain_runner


def parse_arguments():
    parser = argparse.ArgumentParser(description='index_generator_chain_runner.py --project-dir <project-dir> '
                                                 '--project-id <project-id>')
    parser.add_argument('-pd', '--project-dir', help='Project directory for indexing ', required=True)
    parser.add_argument('-pi', '--project-id', help='Project Id', required=True)
    args = parser.parse_args()

    return args.project_dir, args.project_id


project_dir, project_id = parse_arguments()
chain_runner.generate_index_and_send(project_dir, project_id)
