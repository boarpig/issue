#!/usr/bin/python3
#
# Copyright (c) 2013 Lauri Hakko
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from datetime import date, datetime
from os.path import exists
from string import whitespace
import argparse
import array
import fcntl
import gzip
import json
import logging
import os
import subprocess
import tempfile
import termios

logging.basicConfig(format='%(levelname)s:%(message)s')

def term_size():
    buf = array.array('h', [0, 0])
    _ = fcntl.ioctl(0, termios.TIOCGWINSZ, buf, 1)
    rows, columns = buf
    return rows, columns




def get_status_color(status):
    """ Return a unicode color string depending the status. """
    status = status.lower()

    if status == 'open':
        return '\033[92m'
    elif status == 'closed':
        return '\033[91m'
    elif status == 'wontfix':
        return '\033[95m'
    else:
        return '\033[0m'


class Issues(object):


    def __init__(self):
        self.issues = []
        self.gzip_file = False

    def add_issue(self, description, tags):
        if not description:
            description = self.open_editor()
            if description.strip() == "":
                print("Empty issue description. Aborting.")
                exit(1)
        today = date.today().isoformat()
        largest = 0
        if len(self.issues) > 0:
            largest = max([issue["number"] for issue in self.issues])
        number = largest + 1
        issue = {"status": "open", "number": number, "tag": tags, "date": today,
                "description": description}
        self.issues.append(issue)
        self.print_short([issue])
        logging.info("Added a new issue:\n{}".format(issue))
        self.save_issues()

    def search_issues(self, status="open", tags="", description=""):
        issues = self.issues[:]
        if status and status != "all":
            issues = [issue for issue in issues if issue["status"] == status]
        if tags:
            for tag in tags.split(","):
                issues = [issue for issue in issues
                          if issue["tag"].lstrip().find(tag) != -1]
        if description:
            description = description.lower()
            issues = [issue for issue in issues
                      if issue["description"].find(description)]
        if issues:
            self.print_short(issues)
        else:
            print("Nothing found.")

    def edit_issue(self, number, message="", tags="", status="", edit=False):
        if message and edit:
            logging.warning("Cannot use --message and --edit at the same time.")
            exit(1)
        for issue in self.issues:
            if issue["number"] == number:
                if tags:
                    if tags[0] == '+':
                        for tag in tags[1:].split(","):
                            if len(tag) > 20:
                                tag = tag[:20]
                                logging.warning("Tag length is over 20 characters. "
                                    + "Shortening it to 20 characters.")
                            issue["tag"] += "," + tag
                    elif tags[0] == '-':
                        removes = tags[1:].split(",")
                        current_tags = issue["tag"].split(",")
                        issue["tag"] = ""
                        for tag in current_tags:
                            if tag not in removes:
                                issue["tag"] += "," + tag
                    elif tags[0] == '=':
                        for tag in tags[1:].split(","):
                            issue["tag"] = ""
                            if len(tag) > 20:
                                tag = tag[:20]
                                logging.warning("Tag length is over 20 characters. "
                                    + "Shortening it to 20 characters.")
                            issue["tag"] += "," + tag
                    issue["tag"] = issue["tag"].lstrip(",")
                if message or edit:
                    if issue["status"] == 'closed':
                        logging.warning("Editing closed issue is disallowed.")
                    elif message:
                        issue["description"] = message
                    elif edit:
                        new_desc = self.open_editor(number)
                        if new_desc.strip("\n\r" + whitespace) == "":
                            print("Got empty issue description. "
                                    + "Issue left unchanged.")
                            exit(0)
                        else:
                            issue["description"] = new_desc
                if status:
                    issue["status"] = status
                self.print_short((issue,))
                break
        self.save_issues()

    def init(self, force, compress):
        if exists("ISSUES") or exists("ISSUES.gz"):
            if force:
                now = datetime.today().strftime("%Y-%m-%d_%H%M%S")
                if self.gzip_file:
                    newfile = "ISSUES.gz_" + now
                else:
                    newfile = "ISSUES_" + now
                if exists(newfile):
                    logging.error("Could not rename old file. Filename already"
                            + " exists.")
                    exit(1)
                else:
                    try:
                        if self.gzip_file:
                            os.rename("ISSUES.gz", newfile)
                        else:
                            os.rename("ISSUES", newfile)
                        logging.info("Moved old issue file to {}".format(newfile))
                    except OSError:
                        logging.error("Could not rename file.")
                if compress:
                    self.gzip_file = True
                self.issues = []
                self.save_issues()
                logging.info("Created a new issue file.")
            else:
                logging.error("ISSUES file already exists.")
                print("Use --force to make one anyway.")
        else:
            if compress:
                self.gzip_file = True
            logging.info("Created a new issue file.")
            self.save_issues()

    def open_editor(self, number=-1):
        content = ""
        if number != -1: # Editing existing issue
            for issue in self.issues:
                if issue["number"] == number:
                    content = issue["description"]
        with tempfile.NamedTemporaryFile() as f:
            editor = os.environ['EDITOR']
            filename = f.name
            f.write(bytes(content, encoding="utf-8"))
            f.flush() # Make sure file has appropriate content before opening
            ret = subprocess.call([editor, filename])
            if ret == 0:
                f.seek(0)
                content = str(f.read(), encoding="utf-8")
                content = content.strip("\n\r")
        return content

    def print_short(self, issuelist):
        rows, max_width = term_size()
        print('\033[2J\033[{}A'.format(rows), end='')
        padding = 3
        # Use the column title length as min length
        lens = {
            "status": len('status'),
            "number": len('number'),
            "tag": len('tag'),
            "date": len('date'),
            "description": len('description')
        }
        # Use custom length if a column value is longer than the column title
        # liength
        if len(issuelist) > 0:
            for issue in issuelist:
                for col in issue:
                    if len(str(issue[col])) > lens[col]:
                            lens[col] = len(str(issue[col]))
        else:
            logging.warning("Issue list print requested but got nothing.")
            exit(1)
        # All logic is done. Now we juste have to print the informations.
        # Print a bold column header
        print('\033[1m', end='')
        print('status'.ljust(lens['status'] + padding), end='')
        print('number'.ljust(lens['number'] + padding), end='')
        print('tag'.ljust(lens['tag'] + padding), end='')
        print('date'.ljust(lens['date'] + padding), end='')
        print('description'.ljust(lens['description'] + padding), end='')
        print('\033[0m', end='')
        print()
        for issue in issuelist:
            # Only use the first line of the description
            # and strech if too long.
            desc_width = max_width - (sum(lens.values()) - lens["description"]) - 12
            d = issue['description'][:]
            d = d.splitlines()[0]
            if len(d) >= desc_width:
                d = d[:desc_width - 3]
                d += '...'
            print(get_status_color(issue['status']), end='')
            print(issue["status"].ljust(lens["status"] + padding), end='')
            print(get_status_color(''), end='')
            print(str(issue["number"]).ljust(lens["number"] + padding), end='')
            print(issue["tag"].ljust(lens["tag"] + padding), end='')
            print(issue["date"].ljust(lens["date"] + padding), end='')
            print(d, end='')
            print()

    def print_long(self, number):
        rows, max_width = term_size()
        print('\033[2J\033[{}A'.format(rows), end='')
        for issue in self.issues:
            if issue["number"] == number:
                print("\033[1mStatus:\033[0m\t", end='')
                print(get_status_color(issue['status']), end='')
                print(issue['status'], end='')
                print(get_status_color(''))
                print("\033[1mNumber:\033[0m\t" + str(number))
                print("\033[1mTag:\033[0m\t" + issue["tag"])
                print("\033[1mDate:\033[0m\t" + issue["date"])
                print("\n" + issue["description"])
                break

    def remove_issue(self, number):
        print("Warning! You are about to remove following issue. "
                + "This cannot be undone!")
        self.print_long(number)
        print("To confirm, please retype the issue number: ", end="")
        other = input()
        if other.isdigit():
            other = int(other)
        else:
            logging.error("Not a number. Aborting.")
            exit(1)
        if number == int(other):
            self.issues = [issue for issue in self.issues 
                           if issue["number"] != number]
            save_issues()
            logging.info("Removed an issue.")
        else:
            logging.error("Wrong issue number. Aborting.")

    def load_issues(self, args):
        if exists("ISSUES"):
            try:
                with open("ISSUES") as f:
                    try:
                        content = f.read()
                        if content.strip() != "":
                            self.issues = json.loads(content)
                    except ValueError:
                        logging.error("Error while loading json. "
                                + "Maybe ISSUES file is corrupted.")
            except PermissionError:
                logging.error("No permissions to read ISSUES file")
                exit(1)
        elif exists("ISSUES.gz"):
            self.gzip_file = True
            try:
                with gzip.open("ISSUES.gz", "rt") as f:
                    try:
                        content = f.read()
                        if content.strip() != "":
                            self.issues = json.loads(content)
                    except ValueError:
                        logging.error("Error while loading json. "
                                + "Maybe ISSUES file is corrupted.")
                logging.info("Gzip file detected and read.")
            except OSError:
                logging.error("Not a gzip file, or other error.")
                exit(1)
            except PermissionError:
                logging.error("No permissions to read ISSUES file")
                exit(1)
        else:
            if args.subparser == "init":
                init(args.force, args.gzip)
                exit(0)
            else:
                logging.warning("ISSUES file does not exist.")
                print("You can create one with\n\n $ issue init\n")
                exit(1)

    def save_issues(self):
        if not self.gzip_file:
            try:
                with open("ISSUES", "w") as f:
                    json.dump(self.issues, f)
            except PermissionError:
                logging.error("No permission to write to the file. "
                    + "Changes were not saved.")
        else:
            try:
                with gzip.open("ISSUES.gz", mode="wt") as f:
                    json.dump(self.issues, f)
            except PermissionError:
                logging.error("No permission to write to the file. "
                    + "Changes were not saved.")
        logging.info("Succesfully saved issues")

def parse_arguments():
    parser = argparse.ArgumentParser(description="Simple issue handler")
    subparsers = parser.add_subparsers(title="subcommands", dest="subparser")

    add_parser = subparsers.add_parser("add", help="Add new issue")
    add_parser.add_argument("-d", "--description", metavar="TEXT",
            help="Description of the issue. if omitted, "
                + "the $EDITOR will be invoked.")
    add_parser.add_argument("-t", "--tags", default="bug",
            help="Specify tags for issue, default: %(default)s")

    edit_parser = subparsers.add_parser("edit", help="Edit individual issue")
    edit_parser.add_argument("number", type=int, help="Issue number to edit")
    edit_parser.add_argument("-m", "--message", default="",
            help="New message to replace the old.")
    edit_parser.add_argument("-t", "--tags", default="",
            help="Change issue tags")
    edit_parser.add_argument("-s", "--status", default="",
            help="Change issue status")
    edit_parser.add_argument("-e", "--edit", action="store_true",
            help="Edit issue in editor."),

    close_parser = subparsers.add_parser("close", help="Close an issue")
    close_parser.add_argument("number", type=int, help="Issue number to close")

    search_parser = subparsers.add_parser("search", aliases=["se"],
            help="Search issues")
    search_parser.add_argument("-s", "--status", default="open",
            help="Filter issues by status. 'all' will list all issues."
            + " default: %(default)s")
    search_parser.add_argument("-t", "--tags",
            help="Filter issues by tags.")
    search_parser.add_argument("-d", "--description", metavar="TEXT",
            help="Filter issues by description.")

    show_parser = subparsers.add_parser("show",
            help="Show more information on individual issue")
    show_parser.add_argument("number", type=int, help="Issue number to show")

    init_parser = subparsers.add_parser("init", help="Initialize issue file")
    init_parser.add_argument("-f", "--force", action="store_true",
            help="Make issue files regardless if one exists already.")
    init_parser.add_argument("-g", "--gzip", action="store_true",
            help="Make gzip compressed issue file.")

    remove_parser = subparsers.add_parser("remove", aliases=["rm"],
            help="Remove an issue")
    remove_parser.add_argument("number", type=int,
        help="Number of the issue you want to remove")

    return parser.parse_args()


def main():
    issues = Issues()
    args = parse_arguments()
    issues.load_issues(args)
    if args.subparser == "init":
        issues.init(args.force, args.gzip)
    elif args.subparser == "add":
        issues.add_issue(args.description, args.tags)
    elif args.subparser == "show":
        issues.print_long(args.number)
    elif args.subparser == "search" or args.subparser == "se":
        issues.search_issues(status=args.status, tags=args.tags,
                description=args.description)
    elif args.subparser == "close":
        issues.edit_issue(args.number, status="closed")
    elif args.subparser == "edit":
        issues.edit_issue(args.number, message=args.message, tags=args.tags,
                status=args.status, edit=args.edit)
    elif args.subparser == "remove" or args.subparser == "rm":
        issues.remove_issue(args.number)
    else:
        issues.search_issues()

if __name__=='__main__':
    main()
