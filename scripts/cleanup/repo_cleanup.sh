#!/bin/bash

script_dir="$(dirname "${BASH_SOURCE[0]}")"

git -C "$script_dir" filter-repo --invert-paths --paths-from-file "$script_dir"/files_to_remove.txt
