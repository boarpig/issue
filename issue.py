#!/usr/bin/python

import argparse

def new_issue(message):
    pass

def list_issues():
    pass

def close_issue(number):
    pass

def main():
    parser = argparse.ArgumentParser(description="Simple issue handler")
    subparsers = parser.add_subparsers(help="subcommand help")

    new_parser = subparsers.add_parser("new", help="Add new issue.")
    new_parser.add_argument("-m", "--message", 
            help="""Message for the issue. if omitted, the $EDITOR will be
            invoked.""")

    list_parser = subparsers.add_parser("list", help="List issues")
    list_parser.add_argument("-a", "--all", action="store_true", 
            default=False, help="List all issues instead of open ones.")
    list_parser.add_argument("-c", "--closed", action="store_true", 
            default=False, help="List closed issues.")
    list_parser.add_argument("-t", "--tag", help="List only specified tags")

    close_parser = subparsers.add_parser("close", help="Close an issue")
    close_parser.add_argument("number", type=int, help="Issue number to close")

    args = parser.parse_args()

    if args.subparser_name == "new":
        new_issue(args.message)
    elif args.subparser_name == "list":
        list_issues()
    elif args.subparser_name == "close":
        close_issue(args.number)

if __name__=='__main__':
    main()
