# Issue

Small command line issue tracker mostly for those one person projects where you
don't want to depend on something like github to track your issues but want to 
keep issue tracking in your repository.

## Command-line

### Getting started

    $ issue init
    $ issue add -m "my new issue"
    $ issue add -t enhancement -m "my enhancement proposal"
    $ issue
    open   1   bug           2013-12-27   my new issue
    open   2   enhancement   2013-12-27   my enhancement proposal
    $ issue close 1
    closed   1   bug           2013-12-27   my new issue

### Usage

    usage: issue [-h] [subcommand] ...

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

