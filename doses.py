import argparse
from open_data import OpenData


parser = argparse.ArgumentParser()
parser.add_argument("--create", dest='create', action="store_true", default=False, help="Creates the doses table inside the specified database")

# Parse and print the results
args = parser.parse_args()

od = OpenData()

if args.create is True:
    od.create_table()

od.fetch_all()