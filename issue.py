#!/usr/bin/python

import argparse
import csv
from datetime import date
from os.path import exists

issues = []

def new_issue(message, tag):
    today = date.today().isoformat()
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

def edit_issue(number, message, tag, close, reopen):
    global issues
    for issue in issues:
        if int(issue[1]) == number:
            if tag:
                issue[3] = tag
            if message:
                issue[4] = message
            if close:
                issue[0] = 'closed'
            if reopen:
                issue[0] = 'open'
    save_issues()

def init():
    open("ISSUES", "a").close()

def save_issues():
    global issues
    with open("ISSUES", "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerows(issues)

def main():
    parser = argparse.ArgumentParser(description="Simple issue handler")
    subparsers = parser.add_subparsers(help="subcommand help", dest="subparser")

    new_parser = subparsers.add_parser("new", help="Add new issue.")
    new_parser.add_argument("-m", "--message", 
            help="""Message for the issue. if omitted, the $EDITOR will be
            invoked.""")
    new_parser.add_argument("-t", "--tag", default="bug",
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
        with open("ISSUES") as f:
            issues = list(csv.reader(f))
    else:
        if args.subparser == "init":
            init()
        else:
            print("ISSUES file does not exist. You can create one with\n\n"
                    + " $ issue init\n")
            exit()


    if args.subparser == "new":
        new_issue(args.message, args.tag)
    elif args.subparser == "list":
        list_issues({"all": args.all, "closed": args.closed}, args.tag)
    elif args.subparser == "close":
        edit_issue(args.number, "", "", True, False)
    elif args.subparser == "edit":
        edit_issue(args.number, args.message, args.tag, args.close, args.reopen)
    else:
        list_issues({"all": "", "closed": ""}, "")

if __name__=='__main__':
    main()
