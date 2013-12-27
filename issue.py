#!/usr/bin/python

from datetime import date, datetime
from os.path import exists
from string import whitespace
import argparse
import gzip
import json
import logging
import os
import subprocess
import tempfile

issues = []
gzip_file = False
logging.basicConfig(format='%(levelname)s:%(message)s')

def term_width():
    # http://stackoverflow.com/questions/566746/how-to-get-console-window-width-in-python
    rows, columns = os.popen('stty size', 'r').read().split()
    return int(columns)

def open_editor(number=-1):
    content = ""
    if number != -1: # Editing existing issue
        for issue in issues:
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

def add_issue(description, tags):
    if not description:
        description = open_editor()
        if description.strip() == "":
            print("Empty issue description. Aborting.")
            exit(1)
    today = date.today().isoformat()
    largest = 0
    if len(issues) > 0:
        largest = max([issue["number"] for issue in issues])
    number = largest + 1
    issue = {"status": "open", "number": number, "tag": tags, "date": today, 
            "description": description}
    issues.append(issue)
    print_short([issue])
    logging.info("Added a new issue:\n{}".format(issue))
    save_issues()

def search_issues(status="open", tags="", description=""):
    global issues
    if status and status != "all":
        issues = [issue for issue in issues if issue["status"] == status]
    if tags:
        for tag in tags.split(","):
            issues = [issue for issue in issues 
                    if issue["tag"].lstrip().find(tag) != -1]
    if description:
        description = description.lower()
        issues = [issue for issue in issues if
                issue["description"].find(description)]
    if issues:
        print_short(issues)
    else:
        print("Nothing found.")

def edit_issue(number, message="", tags="", status="", edit=False):
    global issues
    if message and edit:
        logging.warning("Cannot use --message and --edit at the same time.")
        exit(1)
    for issue in issues:
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
                    new_desc = open_editor(number)
                    if new_desc.strip("\n\r" + whitespace) == "":
                        print("Got empty issue description. " 
                                + "Issue left unchanged.")
                        exit(0)
                    else:
                        issue["description"] = new_desc
            if status:
                issue["status"] = status
            print_short((issue,))
            break
    save_issues()

def init(force, compress):
    global gzip_file
    if exists("ISSUES") or exists("ISSUES.gz"):
        if force:
            now = datetime.today().strftime("%Y-%m-%d_%H%M%S")
            if gzip_file:
                newfile = "ISSUES.gz_" + now
            else:
                newfile = "ISSUES_" + now
            if exists(newfile):
                logging.error("Could not rename old file. Filename already" 
                        + " exists.")
                exit(1)
            else:
                try:
                    if gzip_file:
                        os.rename("ISSUES.gz", newfile)
                    else:
                        os.rename("ISSUES", newfile)
                    logging.info("Moved old issue file to {}".format(newfile))
                except OSError:
                    logging.error("Could not rename file.")
            if compress:
                gzip_file = True
            global issues
            issues = []
            save_issues()
            logging.info("Created a new issue file.")
        else:
            logging.error("ISSUES file already exists.")
            print("Use --force to make one anyway.")
    else:
        if compress:
            gzip_file = True
        logging.info("Created a new issue file.")
        save_issues()

def print_short(issuelist):
    lens = {"status": 0, "number": 0,"tag": 0, "date": 0, "description":0}
    if len(issuelist) > 1:
        for issue in issuelist:
            for col in issue:
                if col == "number":
                    if len(str(issue[col])) > lens[col]:
                        lens[col] = len(str(issue[col]))
                else:
                    if len(issue[col]) > lens[col]:
                        lens[col] = len(issue[col])
    elif len(issuelist) == 1:
        issue = issuelist[0]
        for col in issue:
            if col == "number" and len(str(issue[col])) > lens[col]:
                lens[col] = len(str(issue[col]))
            elif col != "number" and len(issue[col]) > lens[col]:
                lens[col] = len(issue[col])
    else:
        logging.warning("Issue list print requested but got nothing.")
        exit(1)
    for issue in issuelist:
        padding = 3
        max_width = term_width()
        desc_width = max_width - (sum(lens.values()) - lens["description"]) - 12
        print(issue["status"].ljust(lens["status"] + padding), end='')
        print(str(issue["number"]).ljust(lens["number"] + padding), end='')
        print(issue["tag"].ljust(lens["tag"] + padding), end='')
        print(issue["date"].ljust(lens["date"] + padding), end='')
        desc = issue["description"]
        desc = desc.splitlines()[0]
        if len(desc) >= desc_width:
            desc = desc[:desc_width - 3]
            desc += "..."
        print(desc, end='')
        print()

def print_long(number):
    for issue in issues:
        if issue["number"] == number:
            print("Status:\t" + issue["status"])
            print("Number:\t" + str(number))
            print("Tag:\t" + issue["tag"])
            print("Date:\t" + issue["date"])
            print("\n" + issue["description"])
            break

def save_issues():
    global issues
    global gzip_file
    if not gzip_file:
        try:
            with open("ISSUES", "w") as f:
                json.dump(issues, f)
        except PermissionError:
            logging.error("No permission to write to the file. " 
                + "Changes were not saved.")
    else:
        try:
            with gzip.open("ISSUES.gz", mode="wt") as f:
                json.dump(issues, f)
        except PermissionError:
            logging.error("No permission to write to the file. " 
                + "Changes were not saved.")
    logging.info("Succesfully saved issues")

def remove_issue(number):
    global issues
    print("Warning! You are about to remove following issue. "
            + "This cannot be undone!")
    print_long(number)
    print("To confirm, please retype the issue number: ", end="")
    other = input()
    if other.isdigit():
        other = int(other)
    else:
        logging.error("Not a number. Aborting.")
        exit(1)
    if number == int(other):
        issues = [issue for issue in issues if issue["number"] != number]
        save_issues()
        logging.info("Removed an issue.")
    else:
        logging.error("Wrong issue number. Aborting.")

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
    
def load_issues(args):
    global issues
    if exists("ISSUES"):
        try:
            with open("ISSUES") as f:
                try:
                    content = f.read()
                    if content.strip() != "":
                        issues = json.loads(content)
                except ValueError:
                    logging.error("Error while loading json. "
                            + "Maybe ISSUES file is corrupted.")
        except PermissionError:
            logging.error("No permissions to read ISSUES file")
            exit(1)
    elif exists("ISSUES.gz"):
        global gzip_file
        gzip_file = True
        try:
            with gzip.open("ISSUES.gz", "rt") as f:
                try:
                    content = f.read()
                    if content.strip() != "":
                        issues = json.loads(content)
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


def main():
    args = parse_arguments()
    load_issues(args)
    if args.subparser == "init":
        init(args.force, args.gzip)
    elif args.subparser == "add":
        add_issue(args.description, args.tags)
    elif args.subparser == "show":
        print_long(args.number)
    elif args.subparser == "search" or args.subparser == "se":
        search_issues(status=args.status, tags=args.tags,
                description=args.description)
    elif args.subparser == "close":
        edit_issue(args.number, status="closed")
    elif args.subparser == "edit":
        edit_issue(args.number, message=args.message, tags=args.tags, 
                status=args.status, edit=args.edit)
    elif args.subparser == "remove" or args.subparser == "rm":
        remove_issue(args.number)
    else:
        search_issues()

if __name__=='__main__':
    main()
