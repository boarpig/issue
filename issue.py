#!/usr/bin/python

from datetime import date, datetime
from os.path import exists
import argparse
import json
import os
import subprocess
import tempfile

issues = []

def open_editor(number=-1):
    content = ""
    if number != -1:
        for issue in issues:
            if int(issue["status"]) == number:
                content = issue["description"]
    with tempfile.NamedTemporaryFile() as f:
        editor = os.environ['EDITOR']
        filename = f.name
        f.write(bytes(content, encoding="utf-8"))
        ret = subprocess.call([editor, filename])
        if ret == 0:
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

def list_issues(flags, tag):
    global issues
    if not flags["all"]:
        if flags["closed"]:
            issues = [issue for issue in issues if issue["status"] == "closed"]
        else:
            issues = [issue for issue in issues if issue["status"] == "open"]
    if tag:
        issues = [issue for issue in issues if issue["tag"].lstrip() == tag]
    lens = {"status": 0, "number": 0,"tag": 0, "date": 0, "description":0}
    for issue in issues:
        for name in lens:
            if name == "number":
                if len(str(issue[name])) > lens[name]:
                    lens[name] = len(str(issue[name]))
            else:
                if len(issue[name]) > lens[name]:
                    lens[name] = len(issue[name])
    padding = 3
    for issue in issues:
        print(issue["status"].ljust(lens["status"] + padding), end='')
        print(str(issue["number"]).ljust(lens["number"] + padding), end='')
        print(issue["tag"].ljust(lens["tag"] + padding), end='')
        print(issue["date"].ljust(lens["date"] + padding), end='')
        desc = issue["description"].ljust(lens["description"])
        desc = desc.splitlines()[0]
        print(desc, end='')
        print()

def edit_issue(number, message="", tag="", close=False, reopen=False):
    global issues
    for issue in issues:
        if issue["number"] == number:
            if tag:
                if len(tag) > 20:
                    tag = tag[:20]
                    print("ERROR: tag length is over 20 characters. "
                        + "Shortening it to 20 characters.")
                issue["tag"] = tag
            if message:
                if issue["status"] == 'closed':
                    print("ERROR: Editing closed issue is disallowed.")
                else:
                    issue["description"] = message
            if close:
                issue["status"] = 'closed'
            if reopen:
                issue["status"] = 'open'
            order = ("status", "number", "tag", "date", "description")
            for i in range(5):
                if order[i] == "number":
                    print(str(issue[order[i]]) + '   ', end='')
                else:
                    print(issue[order[i]] + '   ', end='')
            print()
    save_issues()

def init(force):
    if exists("ISSUES"):
        if force:
            now = datetime.today().strftime("%Y-%m-%d_%H%M%S")
            newfile = "ISSUES_" + now
            if exists(newfile):
                print("ERROR: Could not rename old file. Filename already" 
                        + " exists.")
                exit(1)
            else:
                try:
                    os.rename("ISSUES", newfile)
                except OSError:
                    print("ERROR: could not rename file.")
            open("ISSUES", "a").close()
        else:
            print("ERROR: ISSUES file already exists. Use --force to "
                    + "remove it and make new.")
    else:
        open("ISSUES", "a").close()

def save_issues():
    global issues
    try:
        with open("ISSUES", "w") as f:
            json.dump(issues, f, sort_keys=True, indent=4,
                    separators=(",", ": "))
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
    init_parser.add_argument("-f", "--force", action="store_true", 
            help="Make issue files regardless if one exists already.")

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
                issues = json.load(f)
        except PermissionError:
            print("ERROR: No permissions to read ISSUES file")
            exit(1)
    else:
        if args.subparser == "init":
            init(args.force)
            exit(0)
        else:
            print("ISSUES file does not exist. You can create one with\n\n"
                    + " $ issue init\n")
            exit(1)


    if args.subparser == "init":
        init(args.force)
    elif args.subparser == "add":
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
