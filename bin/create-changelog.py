"""
Create the CHANGELOG.md file using git and the GitHub REST api.
This script assumes it is being run from the root of the CEA repository, as ``python bin\create-changelog.py``

Output format (example)::

    2019-01-24 (v2.9.2) - #1743 updated ArcGIS install instructions

We use the command ``git log origin/master --merges --first-parent master`` which has (roughly) the following output::

    commit 40fbdfd1248ced7de479d846c7150209776a4c1f
    Merge: 8222f860e 7b2d48c22
    Author: Daren Thomas <daren-thomas@users.noreply.github.com>
    Date:   Wed Mar 30 15:32:09 2016 +0200

        Merge pull request #103 from architecture-building-systems/i099-new-properties

        I099 new properties - seems to be working for now...

We need to grab:

- author
- commit id
- date
- first line of text should start with "Merge pull request" and include PR number (for linking)
- figure out cea.__version__ content for that commit

The output is written to ../CHANGELOG.md.
"""
from __future__ import print_function
from __future__ import division

import subprocess
import dateutil.parser


def read_commit_id(git_output):
    commit_line = git_output.readline()
    while commit_line and not commit_line.startswith('commit'):
        commit_line = git_output.readline()
    if not commit_line:
        raise EOFError()
    return commit_line.split()[1]


def read_date(git_output):
    date_line = git_output.readline()
    while date_line and not date_line.strip().startswith('Date:'):
        date_line = git_output.readline()
    if not date_line:
        raise EOFError()
    date_line = date_line.strip()
    date_string = date_line[len('Date:'):]
    d = dateutil.parser.parse(date_string)
    return d.strftime('%Y-%m-%d')


def read_pr(git_output):
    pr_line = git_output.readline()
    while pr_line and not pr_line.strip():
        pr_line = git_output.readline()
    if not pr_line:
        raise EOFError()
    pr_line = pr_line.strip()
    if pr_line.startswith('Merge pull request'):
        return pr_line[len('Merge pull reqeuest'):].split()[0].strip()
    else:
        # this merge was not a PR being merged
        return None


def read_title(git_output):
    title_line = git_output.readline()
    while title_line and not title_line.strip():
        title_line = git_output.readline()
    if not title_line:
        raise EOFError()
    title_line = title_line.strip()
    return title_line


def read_version(git_output):
    return '1.0.0'


def main():
    git = subprocess.Popen("git log origin/master --merges --first-parent master", shell=True, bufsize=1,
                             stdout=subprocess.PIPE, universal_newlines=True)
    git_output = git.stdout
    try:
        commit_id = read_commit_id(git_output)
        while commit_id:
            # author = read_author(git_output)
            date = read_date(git_output)
            pr = read_pr(git_output)
            if not pr:
                # this was not a PR merge
                continue
            title = read_title(git_output)
            version = read_version(pr)
            print('{date} - {pr} {title}'.format(
                date=date,
                # version=version,
                pr=pr,
                title=title
            ))
            commit_id = read_commit_id(git_output)
    except EOFError:
        # we're done now
        pass


if __name__ == '__main__':
    main()