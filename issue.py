#!/usr/bin/python

import argparse
import csv
from datetime import date

issues = []
with open("ISSUES") as f:
    issues = list(csv.reader(f))

def new_issue(message):
    today = date.today().isoformat()
    largest = max([int(issue[1]) for issue in issues])
    number = largest + 1
    issues.append(['open', number, 'bug', today, message])
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
    for issue in issues:
        print(*issue, sep=" ")

def close_issue(number):
    global issues
    for issue in issues:
        if int(issue[1]) == number:
            issue[0] = 'closed'
    save_issues()

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

    list_parser = subparsers.add_parser("list", help="List issues")
    list_parser.add_argument("-a", "--all", action="store_true", 
            default=False, help="List all issues instead of open ones.")
    list_parser.add_argument("-c", "--closed", action="store_true", 
            default=False, help="List closed issues.")
    list_parser.add_argument("-t", "--tag", help="List only specified tag")

    close_parser = subparsers.add_parser("close", help="Close an issue")
    close_parser.add_argument("number", type=int, help="Issue number to close")

    args = parser.parse_args()

    if args.subparser == "new":
        new_issue(args.message)
    elif args.subparser == "list":
        list_issues({"all": args.all, "closed": args.closed}, args.tag)
    elif args.subparser == "close":
        close_issue(args.number)
    else:
        parser.print_help()

if __name__=='__main__':
    main()
