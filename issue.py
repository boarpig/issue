#!/usr/bin/python

from datetime import date, datetime
from os.path import exists
from string import whitespace
import argparse
import json
import logging
import os
import subprocess
import tempfile

issues = []
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

def add_issue(message, tag):
    if not message:
        message = open_editor()
        if message.strip() == "":
            print("Empty issue description. Aborting.")
            exit(1)
    today = date.today().isoformat()
    largest = 0
    if len(issues) > 0:
        largest = max([issue["number"] for issue in issues])
    number = largest + 1
    issues.append({"status": "open", "number": number, "tag": tag, 
        "date": today, "description": message})
    save_issues()

def search_issues(status="open", tag="", description=""):
    global issues
    if status and status != "all":
        issues = [issue for issue in issues if issue["status"] == status]
    if tag:
        issues = [issue for issue in issues if issue["tag"].lstrip() == tag]
    if description:
        description = description.lower()
        issues = [issue for issue in issues if
                issue["description"].find(description)]
    print_short(issues)

def edit_issue(number, message="", tag="", close=False, reopen=False, 
            edit=False):
    global issues
    if message and edit:
        logging.warning("Cannot use --message and --edit at the same time.")
        exit(1)
    for issue in issues:
        if issue["number"] == number:
            if tag:
                if len(tag) > 20:
                    tag = tag[:20]
                    logging.warning("Tag length is over 20 characters. "
                        + "Shortening it to 20 characters.")
                issue["tag"] = tag
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

def init(force):
    if exists("ISSUES"):
        if force:
            now = datetime.today().strftime("%Y-%m-%d_%H%M%S")
            newfile = "ISSUES_" + now
            if exists(newfile):
                logging.error("Could not rename old file. Filename already" 
                        + " exists.")
                exit(1)
            else:
                try:
                    os.rename("ISSUES", newfile)
                except OSError:
                    logging.error("Could not rename file.")
            open("ISSUES", "a").close()
        else:
            logging.error("ISSUES file already exists.")
            print("Use --force to remove it and make new.")
    else:
        open("ISSUES", "a").close()

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
            print("\n" + issue["description"] + "\n")
            break

def save_issues():
    global issues
    try:
        with open("ISSUES", "w") as f:
            json.dump(issues, f, sort_keys=True, indent=4,
                    separators=(",", ": "))
    except PermissionError:
        logging.error("No permission to write to the file. " 
            + "Changes were not saved.")

def main():
    parser = argparse.ArgumentParser(description="Simple issue handler")
    subparsers = parser.add_subparsers(help="subcommand help", dest="subparser")

    add_parser = subparsers.add_parser("add", help="Add new issue.")
    add_parser.add_argument("-m", "--message", 
            help="""Message for the issue. if omitted, the $EDITOR will be
            invoked.""")
    add_parser.add_argument("-t", "--tag", default="bug",
            help="Specify tag for issue, default: %(default)s")

    show_parser = subparsers.add_parser("show", help="Show individual issue.")
    show_parser.add_argument("number", type=int, help="Issue number to show")

    search_parser = subparsers.add_parser("search", help="search issues")
    search_parser.add_argument("-s", "--status", default="open", 
            help="Filter issues by status. default: %(default)s")
    search_parser.add_argument("-t", "--tag", 
            help="Filter issues by tag.")
    search_parser.add_argument("-d", "--description", 
            help="Filter issues by description.")

    close_parser = subparsers.add_parser("close", help="Close an issue")
    close_parser.add_argument("number", type=int, help="Issue number to close")

    init_parser = subparsers.add_parser("init", help="Initialize issue file")
    init_parser.add_argument("-f", "--force", action="store_true", 
            help="Make issue files regardless if one exists already.")

    edit_parser = subparsers.add_parser("edit", help="Edit issue.")
    edit_parser.add_argument("number", type=int, help="Issue number to edit")
    edit_parser.add_argument("-m", "--message", default="",
            help="New message to replace the old.")
    edit_parser.add_argument("-t", "--tag", default="",
            help="Change issue tag")
    edit_parser.add_argument("-s", "--status", default="",
            help="Change issue status")
    edit_parser.add_argument("-e", "--edit", action="store_true",
            help="Edit issue in editor."),

    args = parser.parse_args()

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
    else:
        if args.subparser == "init":
            init(args.force)
            exit(0)
        else:
            logging.warning("ISSUES file does not exist.")
            print("You can create one with\n\n $ issue init\n")
            exit(1)


    if args.subparser == "init":
        init(args.force)
    elif args.subparser == "add":
        add_issue(args.message, args.tag)
    elif args.subparser == "show":
        print_long(args.number)
    elif args.subparser == "search":
        search_issues(args.status, args.tag, args.description)
    elif args.subparser == "close":
        edit_issue(args.number, close=True)
    elif args.subparser == "edit":
        edit_issue(args.number, args.message, args.tag, args.close,
                args.reopen, args.edit)
    else:
        search_issues()

if __name__=='__main__':
    main()
