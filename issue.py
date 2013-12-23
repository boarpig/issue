#!/usr/bin/python

from datetime import date
from os.path import exists
import argparse
import csv
import os
import subprocess
import tempfile

issues = []

def open_editor(number=-1):
    content = ""
    if number != -1:
        for issue in issues:
            if int(issue[0]) == number:
                content = issue[4]
    with tempfile.NamedTemporaryFile() as f:
        editor = os.environ['EDITOR']
        filename = f.name
        f.write(bytes(content, encoding="utf-8"))
        ret = subprocess.call([editor, filename])
        if ret == 0:
            content = str(f.read(), encoding="utf-8")
            content = content.replace("\n", " ").replace("\r", " ") \
                .replace(",", " ")
            repr(content)
    return content

def add_issue(message, tag):
    if not message:
        message = open_editor()
        if message.strip() == "":
            print("Empty issue description. Aborting.")
            exit(1)
    today = date.today().isoformat()
    largest = 0
    if len(issues) < 0:
        largest = max([int(issue[1]) for issue in issues])
    number = largest + 1
    issues.append(['open', number, tag, today, message])
    save_issues()

def list_issues(flags, tag):
    global issues
    if not flags["all"]:
        if flags["closed"]:
            issues = [issue for issue in issues if issue[0] == "closed"]
        else:
            issues = [issue for issue in issues if issue[0] == "open"]
    if tag:
        issues = [issue for issue in issues if issue[2].lstrip() == tag]
    cols = [["STATUS", "NUMBER", "TAG", "DATE", "DESCRIPTION"]]
    lens = [0, 0, 0, 0, 0]
    for issue in cols + issues:
        for i, v in enumerate(issue):
            if lens[i] < len(v):
                lens[i] = len(v)
    for issue in cols + issues:
        for i, col in enumerate(issue):
            print(col.ljust(lens[i] + 2, " "), end="")
        print()

def edit_issue(number, message="", tag="", close=False, reopen=False):
    global issues
    for issue in issues:
        if int(issue[1]) == number:
            if tag:
                if len(tag) > 20:
                    tag = tag[:20]
                    print("ERROR: tag length is over 20 characters. "
                        + "Shortening it to 20 characters.")
                issue[3] = tag
            if message:
                if issue[0] == 'closed':
                    print("ERROR: Editing closed issue is disallowed.")
                else:
                    issue[4] = message
            if close:
                issue[0] = 'closed'
            if reopen:
                issue[0] = 'open'
            print('   '.join(issue))
    save_issues()

def init():
    open("ISSUES", "a").close()

def save_issues():
    global issues
    try:
        with open("ISSUES", "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerows(issues)
    except PermissionError:
        print("ERROR: No permission to write to the file. " 
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

    list_parser = subparsers.add_parser("list", help="List issues")
    list_parser.add_argument("-a", "--all", action="store_true", 
            default=False, help="List all issues instead of open ones.")
    list_parser.add_argument("-c", "--closed", action="store_true", 
            default=False, help="List closed issues.")
    list_parser.add_argument("-t", "--tag", help="List only specified tag")

    close_parser = subparsers.add_parser("close", help="Close an issue")
    close_parser.add_argument("number", type=int, help="Issue number to close")

    init_parser = subparsers.add_parser("init", help="Initialize issue file")

    edit_parser = subparsers.add_parser("edit", help="Edit issue.")
    edit_parser.add_argument("number", type=int, help="Issue number to edit")
    edit_parser.add_argument("-m", "--message", default="",
            help="New message to replace the old.")
    edit_parser.add_argument("-t", "--tag", default="",
            help="Change issue tag")
    edit_parser.add_argument("-c", "--close", action="store_true",
            help="Close the issue"),
    edit_parser.add_argument("-r", "--reopen", action="store_true",
            help="Reopen a closed issue."),


    args = parser.parse_args()

    global issues
    if exists("ISSUES"):
        try:
            with open("ISSUES") as f:
                issues = list(csv.reader(f))
        except PermissionError:
            print("ERROR: No permissions to read ISSUES file")
            exit(1)
    else:
        if args.subparser == "init":
            init()
            exit(0)
        else:
            print("ISSUES file does not exist. You can create one with\n\n"
                    + " $ issue init\n")
            exit(1)


    if args.subparser == "add":
        add_issue(args.message, args.tag)
    elif args.subparser == "list":
        list_issues({"all": args.all, "closed": args.closed}, args.tag)
    elif args.subparser == "close":
        edit_issue(args.number, close=True)
    elif args.subparser == "edit":
        edit_issue(args.number, args.message, args.tag, args.close, args.reopen)
    else:
        list_issues({"all": "", "closed": ""}, "")

if __name__=='__main__':
    main()
