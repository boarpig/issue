# Issue

Small command line issue tracker mostly for those one person projects where you
don't want to depend on something like github to track your issues but want to 
keep issue tracking in your repository.

## Command-line

### Getting started

    $ issue.py init
    $ issue.py add -d "my new issue"
    $ issue.py add -t enhancement -d "my enhancement proposal"
    $ issue.py
    open   1   bug           2013-12-27   my new issue
    open   2   enhancement   2013-12-27   my enhancement proposal
    $ issue.py close 1
    closed   1   bug           2013-12-27   my new issue

### Usage

    usage: issue.py [-h] [subcommand] ...

    Simple issue handler

    optional arguments:
    -h, --help            show this help message and exit

    subcommands:
    {add,edit,close,search,se,show,init,remove,rm}
        add                 Add new issue
        edit                Edit individual issue
        close               Close an issue
        search (se)         Search issues
        show                Show more information on individual issue
        init                Initialize issue file
        remove (rm)         Remove an issue

### Making the issues file

To make a new `ISSUES` file, you can use

    $ issue.py init [-g] [-f]

which basically just make a file with `[]` in it. If you specify `-g` to make
gzip compressed issues file. Compressed files won't work so well with version
control system,  but you can do that anyway if you like. If you already have an 
issues file you want to compress, you can simply compress your `ISSUES` file 
with

    $ gzip ISSUES

and it'll make `ISSUES.gz` which works transparently with issue.py. Similarly,
if you want to move back to uncompressed file, you can uncompress it with

    $ gzip -d ISSUES.gz

If you already have an `ISSUES` file, issues.py won't overwrite it but you can
force it to create the file anyway with `-f`. This won't actually remove the old
file, but simple moves it out of the way.

### Adding issues

Basic way to add issues is to do

    $ issue.py add -d "My issue description"

you can add `-t` to specify tags in comma-separated list. If you specify
none, `-t bug` is assumed. 

You can also leave `-d` out and issue.py will open the default editor for you 
specified in `$EDITOR` environment variable. In the editor you can write
multiline issue description where first line will be used as the title and will
be shown in default issue list. You can view the whole description with
`issue.py show <issue>`

#### Examples

to add issue with `feature` tag, you can do

    $ issue.py add -t feature -d "Add support for .gz files"

You can also specify multiple tabs with commas, without spaces

    $ issue.py add -t bug,critical -d "Game crashes on save"

### Closing issues

Closing issues works simply 

    $ issue.py close <number>

where `<number>` is the issue number you want to close. This will simply change
issue status to 'closed'. Closing issue will print the closed issue and the
issue won't show up in issue list anymore by default. You can still find it with
`issue.py search`

#### Example

    $ issue.py close 4
    closed   4   Feature   2013-12-27   Laser effects would be cool

### Editing issue

You can edit any issue using 

    $ issue.py edit <number> [-t tag] [-s status] [-d description|-e]

which lets you edit issue's tags, status and description as you like. `-e`
cannot be used with `-d description`. Using `-d` you can specify the new
description for the issue on the commandline, but if you want to edit the
description more easily or if the issue description is multiline, you can use
`-e` to open the description in the editor for editing.

`-t` allows you to add and remove tags by specifying `+` or `-` in front of the
tags list or you can use `=` to replace the tags all together. You cannot add
and remove tags at the same time.

#### Examples

To add feature tag to issue number 6:

    $ issue.py edit 6 -t+feature

Removing tags works similarly. To remove `critical` tag from issue 46

    $ issue.py edit 46 -t-critical

You can also specify multiple tags on the commandline

    $ issue.py edit 7 -t+bug,low

to change issue status to `wontfix` you can do

    $ issue.py edit 9 -s wontfix

to change issue status to `closed` and add `critical` tag:

    $ issue.py edit 3 -s closed -t+critical

### Searching for issues

Searching for issues works much like issue editing. You can specify any of `-t`,
`-s` and `-d` to filter the issuelist by tags, status or description
respectively. Search will be done on open issues by default, but you can search
all issues by specifying `-s all`. You can specify multiple tags at the same
time by separating them with comma

#### Examples

to search for all issues with `bug` tag:

    $ issue.py search -s all -t bug

to search for closed issues with `feature` tag:

    $ issue.py search -s closed -t feature

to search open issues for `crash` keyword, you can simply do

    $ issue.py search -d crash 

if you remember an old closed bug with `critical` and `bug` tags that contained
word "impossible, you can do

    $ issue.py search -s closed -t critical,bug -d impossible

### Show

To view multiline issue or issue description that doesn't fit one terminal
width, you can use 

    $ issue.py show <issue>

#### Example

    $ issue.py show 7
    Status: open
    Number: 7
    Tag:    bug
    Date:   2013-12-28

    Program crashes when you specify both -e and -d
    I found a way to make the program crash by doing

        $ issue.py edit 6 -d "will crash" -e

    I get "Generic error"

### Removing issues

To remove issues, you can simply do

    $ issue.py remove <issue>

Using `remove` is discouraged since remove action cannot be undone, but you can
 either close it or mark it `wontfix` instead.
