"""Ensures that the files in `dist/` are prefixed with {build_name}

Tag must adhere to naming convention of distributed files. For example, the tag
`v0.1.2` must match the prefix of the files in the `dist/` folder:

    -rw-r--r--@ 2.0K Oct 23 14:06 dagster_datacontract-0.1.2-py3-none-any.whl
    -rw-r--r--@ 1.6K Oct 23 14:06 dagster_datacontract-0.1.2.tar.gz

USAGE

    $ python .github/validate-release-version.py ./dist v0.2.0
"""

import sys
import os


if len(sys.argv) != 3:
    print("Requires positional arguments: <path to dist> <github.ref_name>")
    sys.exit(1)

dist_path = sys.argv[1]
version = sys.argv[2]
build_name = f"dagster_datacontract-{version.replace('v', '')}"

if not os.path.exists(dist_path):
    print("Release directory `dist/` must exist")
    sys.exit(1)

for filename in os.listdir(dist_path):
    if filename.startswith("."):
        continue
    if not filename.startswith(build_name):
        print(f"{filename} does not start with prefix {build_name}")
        sys.exit(1)


print(f"Success: all files in `dist/` are prefixed with {build_name}")
