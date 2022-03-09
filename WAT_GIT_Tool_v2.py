'''
* Copyright 2022 United States Bureau of Reclamation (USBR).
* United States Department of the Interior
* All Rights Reserved. USBR PROPRIETARY/CONFIDENTIAL.
* Source may not be released without written approval
* from USBR

Created on 2/10/2022
@author: Scott Burdick, Stephen Ackerman
@organization: Resource Management Associates
@contact: scott@rmanet.com, stephen@rmanet.com
@note:
'''

import sys, os
import git
import getopt
import traceback

def gitClone(options):
    default_URL = r'https://gitlab.rmanet.app/RMA/usbr-water-quality/UpperSac-Submodules/uppersac.git' #default
    opts = options.keys()
    if "--folder" not in opts:
        print_to_stdout("--folder not included in input.")
        print_to_stdout("now exiting..")
        sys.exit(1)
    print_to_stdout("Made it to clone")
    remote = default_URL
    for opt in opts:
        if opt == '--folder':
           folder = options[opt]
        elif opt == '--remote':
            remote = options[opt]

    print_to_stdout('USER HAS SELECTED:')
    print_to_stdout('folder:', folder)
    print_to_stdout('remote:', remote)

    if '--donothing' not in opts:
        checkDestinationDirectory(folder)
        try:
            response = git.Repo.clone_from(remote, folder, multi_options=['--recurse-submodule'])
            print_to_stdout('Clone complete.')
        except git.exc.GitError:
            print_to_stdout(traceback.format_exc())
            sys.exit(1)

    else:
        print_to_stdout('Do nothing mode engaged.')

    # sys.exit(0)

def gitUpload(options):
    opts = options.keys()

    if "--folder" not in opts:
        print_to_stdout("--folder not included in clone.")
        print_to_stdout("now exiting..")
        sys.exit(1)
    if '--comments' not in opts and '--commentsfile' not in opts:
        print_to_stdout("--comments or --commentsfile not included in input.")
        print_to_stdout("now exiting..")
        sys.exit(1)
    print_to_stdout("Made it to upload")

    for opt in opts:
        if opt == '--folder':
            folder = options[opt]
        elif opt == '--comments':
            comments = options[opt]
        elif opt == '--commentsfile':
            commentsfile = options[opt]
            comments = readCommentsFile(commentsfile)

    print_to_stdout('USER HAS SELECTED:')
    print_to_stdout('folder:', folder)
    print_to_stdout('comments:\n{0}'.format(comments))

    if '--donothing' not in opts:
        repo = connect2GITRepo(folder)

        if '--all' in options.keys():
            if '--main' not in opts:
                options['--main'] = ''
            if '--submodule' not in opts:
                options['--submodule'] = []
            for submodule in repo.submodules:
                if submodule.name not in options['--submodule']:
                    options['--submodule'].append(submodule.name)

        if not any(x in options.keys() for x in ['--all', '--main', '--submodule']):
            options['--main'] = ''

        if '--main' in options.keys():
            changedFiles = getChangedFiles(repo)
            repo.git.add('--all')
            repo.index.commit(comments)
            response = repo.remotes.origin.push()
            printChangedFiles(changedFiles)

        if '--submodule' in options.keys():
            if isinstance(options['--submodule'], str):
                options['--submodule'] = [options['--submodule']]
            for submodule in repo.submodules:
                if submodule.name in options['--submodule']:
                    print_to_stdout('Submodule:', submodule.name)
                    repo_submod = submodule.module()
                    changedFiles = getChangedFiles(repo_submod)
                    repo_submod.git.add('--all')
                    repo_submod.index.commit(comments)
                    repo.git.add(submodule.path)
                    printChangedFiles(changedFiles)

        if '--main' in options.keys() or '--submodule' in options.keys():
            # repo.git.add("--all")
            repo.index.commit(comments)
            response = repo.remotes.origin.push(recurse_submodules="on-demand")
            print_to_stdout('Upload complete.')
        else:
            print_to_stdout("No upload target submitted.")
            print_to_stdout("Use --main or --submodule")

    else:
        print_to_stdout('Do nothing mode engaged.')

    # sys.exit(0)

def gitDownload(options):
    opts = options.keys()

    if "--folder" not in opts:
        print_to_stdout("--folder not included in clone.")
        print_to_stdout("now exiting..")
        sys.exit(1)

    print_to_stdout("Made it to download")

    for opt in opts:
        if opt == '--folder':
            folder = options[opt]

    print_to_stdout('USER HAS SELECTED:')
    print_to_stdout('folder:', folder)

    if '--donothing' not in opts:
        repo = connect2GITRepo(folder)

        if '--all' in options.keys():
            if '--main' not in opts:
                options['--main'] = ''
            if '--submodule' not in opts:
                options['--submodule'] = []
            for submodule in repo.submodules:
                if submodule.name not in options['--submodule']:
                    options['--submodule'].append(submodule.name)

        if not any(x in options.keys() for x in ['--all', '--main', '--submodule']):
            options['--main'] = ''

        if '--main' in options.keys():
            gitCompare(options, repo=repo)
            changedlocals = getChangedFiles(repo)
            printChangedFiles(changedlocals, "The following files will be overwritten:")
            repo.git.reset('--hard')
            repo.git.pull()
            print_to_stdout('Download complete.')
        if '--submodule' in options.keys():
            if isinstance(options['--submodule'], str):
                options['--submodule'] = [options['--submodule']]
            for submodule in repo.submodules:
                if submodule.name in options['--submodule']:
                    print_to_stdout('\nDownloading Submodule:', submodule.name)
                    repo_submod = submodule.module()
                    gitCompare(options, repo=repo_submod)
                    changedlocals = getChangedFiles(repo_submod)
                    printChangedFiles(changedlocals, "The following files will be overwritten:")
                    try:
                        repo_submod.git.reset('--hard')
                        repo_submod.git.pull()
                        print_to_stdout('Download complete.')
                    except git.exc.GitCommandError:
                        print('Error pulling submodule {0}'.format(submodule))
    else:
        print_to_stdout('Do nothing mode engaged.')

    # sys.exit(0)

def gitChanges(options):
    opts = options.keys()

    if "--folder" not in opts:
        print_to_stdout("--folder not included in clone.")
        print_to_stdout("now exiting..")
        sys.exit(1)

    print_to_stdout("Made it to Changes")

    for opt in opts:
        if opt == '--folder':
            folder = options[opt]

    print_to_stdout('USER HAS SELECTED:')
    print_to_stdout('folder:', folder)

    if '--donothing' not in opts:
        repo = connect2GITRepo(folder)

        if '--all' in options.keys():
            if '--main' not in opts:
                options['--main'] = ''
            if '--submodule' not in opts:
                options['--submodule'] = []
            for submodule in repo.submodules:
                if submodule.name not in options['--submodule']:
                    options['--submodule'].append(submodule.name)

        if not any(x in options.keys() for x in ['--all', '--main', '--submodule']):
            options['--main'] = ''

        changed_file_list = []
        if '--main' in options.keys():
            changedTracked = getChangedFiles(repo)
            changed_file_list += changedTracked

        if '--submodule' in options.keys():
            if isinstance(options['--submodule'], str):
                options['--submodule'] = [options['--submodule']]
            for submodule in repo.submodules:
                if submodule.name in options['--submodule']:
                    print_to_stdout('Submodule:', submodule.name)
                    # repo_submod = repo.submodules[submodule].module()
                    repo_submod = submodule.module()
                    changedTracked = getChangedFiles(repo_submod)
                    for cfile in changedTracked:
                        changed_file_list.append('{0}/{1}'.format(submodule.path, cfile))

        if len(changedTracked) > 0:
            printChangedFiles(changed_file_list)
        else:
            print_to_stdout('\nNo tracked files changed.')
    else:
        print_to_stdout("Do nothing mode engaged.")

    # sys.exit(0)

def gitFetch(options):
    opts = options.keys()

    if "--folder" not in opts:
        print_to_stdout("--folder not included in clone.")
        print_to_stdout("now exiting..")
        sys.exit(1)

    print_to_stdout("Made it to Fetch")

    for opt in options.keys():
        if opt == '--folder':
            folder = options[opt]

    print_to_stdout('USER HAS SELECTED:')
    print_to_stdout('folder:', folder)

    if not any(x in options.keys() for x in ['--all', '--main', '--submodule']):
        options['--main'] = ''

    if '--donothing' in options.keys():
        print_to_stdout("Do nothing mode engaged.")
    elif '--all' in options.keys():
        repo = connect2GITRepo(folder)
        repo.git.fetch(recurse_submodules=True)

    else:
        repo = connect2GITRepo(folder)
        if '--main' in options.keys():
            repo.git.fetch()
        if '--submodule' in options.keys():
            if isinstance(options['--submodule'], str):
                options['--submodule'] = [options['--submodule']]
            # for submodule in options['--submodule']:
            for submodule in repo.submodules:
                if submodule.name in options['--submodule']:
                    repo_submod = submodule.module()
                    repo_submod.git.fetch()
    # sys.exit(1)

def gitCompare(options, comparisonType='files', repo=None):
    opts = list(options.keys())

    if "--folder" not in opts:
        print_to_stdout("--folder not included in options.")
        print_to_stdout("now exiting..")
        sys.exit(1)

    for opt in opts:
        if opt == '--folder':
            folder = options[opt]
        elif opt == '--compare-to-remote':
            comparisonType = options[opt]

    if repo == None:
        repo = connect2GITRepo(folder)

    if '--all' in opts:
        if '--main' not in opts:
            opts.append('--main')
        if '--submodule' not in opts:
            options['--submodule'] = []
        for submodule in repo.submodules:
            if submodule.name not in options['--submodule']:
                options['--submodule'].append(submodule.name)

    if not any(x in options.keys() for x in ['--all', '--main', '--submodule']):
        options['--main'] = ''

    all_changed_files = []
    all_changed_commits = []

    if '--donothing' not in opts:

        if '--main' in opts:
            if comparisonType.lower() == 'files':
                changedFiles = compareFiles(repo)
                all_changed_files += changedFiles

            elif comparisonType.lower() == 'commits':
                differentCommits = compareCommits(repo)
                all_changed_commits += differentCommits

        if '--submodule' in options.keys():
            if isinstance(options['--submodule'], str):
                options['--submodule'] = [options['--submodule']]
            for submodule in repo.submodules:
                if submodule.name in options['--submodule']:
                    repo_submod = submodule.module()

                    if comparisonType.lower() == 'files':
                        changedFiles = compareFiles(repo_submod)
                        for file in changedFiles:
                            all_changed_files.append('{0}/{1}'.format(submodule, file))

                    elif comparisonType.lower() == 'commits':
                        differentCommits = compareCommits(repo_submod)
                        for commit in differentCommits:
                            all_changed_commits.append('{0}: {1}'.format(submodule, commit))

        if comparisonType.lower() == 'files':
            if len(all_changed_files) > 0:
                printChangedFiles(all_changed_files, message='Pending Files:')
            else:
                print_to_stdout('\nNo files changed.')
        elif comparisonType.lower() == 'commits':
            if len(all_changed_commits) > 0:
                printChangedFiles(all_changed_commits, message='Pending Commits:')
            else:
                print_to_stdout('\nNo new commits.')
    else:
        print_to_stdout("Do nothing mode engaged.")

    # if exit:
    #     sys.exit(0)

def gitListSubmodules(options):
    opts = list(options.keys())

    if "--folder" not in opts:
        print_to_stdout("--folder not included in options.")
        print_to_stdout("now exiting..")
        sys.exit(1)

    for opt in opts:
        if opt == '--folder':
            folder = options[opt]

    repo = connect2GITRepo(folder)
    submodules = repo.submodules
    if len(submodules) == 0:
        print_to_stdout('\nNo Submodules detected.')
    else:
        print_to_stdout('\nSubmodules in main repo:')
        for submodule in submodules:
            print_to_stdout(submodule.name)

    # sys.exit(0)

def compareCommits(repo):
    remoteBranch = getCurrentBranchRemote(repo)
    if remoteBranch is None:
        print_to_stdout("\nBranch does not track a remote. Compare not possible.")
        sys.exit(2)

    current_branch = repo.active_branch.name
    commits = repo.git.log('--oneline', current_branch+'...'+remoteBranch).strip()

    if commits != '':
        return commits.split('\n')
    return []

def compareFiles(repo):
    remoteBranch = getCurrentBranchRemote(repo)
    if remoteBranch is None:
        print_to_stdout("\nBranch does not track a remote. Compare not possible.")
        sys.exit(2)

    current_branch = repo.active_branch.name
    changedFiles = repo.git.diff('--name-only', current_branch, remoteBranch).strip()

    if changedFiles != '':
        return changedFiles.split('\n')
    else:
        return []

def getCurrentBranchRemote(repo):
    branchStatus = repo.git.status('-s','-b')
    if '...' not in branchStatus:
        return None

    remoteBranch = branchStatus.split('...')[1]
    if '[' in remoteBranch:
        remoteBranch = remoteBranch.split('[')[0].strip()
    remoteBranch = remoteBranch.split('\n')[0]
    return remoteBranch

def getChangedFiles(repo):
    untracked = repo.untracked_files
    changedFiles = [item.a_path for item in repo.index.diff(None, ignore_submodules=True)]
    changedTracked = [n for n in changedFiles if n not in untracked]
    return changedTracked

def printChangedFiles(changedFiles, message="Files Changed:"):
    cFiles_frmt = formatChangedFiles(changedFiles)
    if len(cFiles_frmt) == 0:
        print_to_stdout('No files changed.')
        return
    print_to_stdout(message)
    for cfile in cFiles_frmt:
        if cfile != '':
            print_to_stdout("\t{0}".format(cfile))

def formatChangedFiles(changedFiles):
    if isinstance(changedFiles, (str, int, float)):
        return [changedFiles]
    elif isinstance(changedFiles, list):
        changed = []
        for cfile in changedFiles:
            cfile_frmt = formatChangedFiles(cfile)
            changed += cfile_frmt
        return list(set(changed))

def connect2GITRepo(repo_path):
    try:
        repo = git.Repo(repo_path)
        print_to_stdout('\nConnected to GIT Repo!')
        return repo
    except git.exc.GitError:
        print_to_stdout('\nInvalid GIT Repo directory: {0}'.format(repo_path))
        sys.exit(1)

def checkDestinationDirectory(repo_dir):
    try:
        if os.path.exists(repo_dir):
            dirlen = os.listdir(repo_dir)
            if len(dirlen) == 0:
                return True
            else:
                print_to_stdout('\nDestination directory {0} already exists.'.format(repo_dir))
                sys.exit(1)
        else:
            print_to_stdout('\nCreating Directory at {0}..'.format(repo_dir))
            os.makedirs(repo_dir)
            return True
    except Exception as e:
        print_to_stdout(e)
        print_to_stdout('')
        sys.exit(1)

def readCommentsFile(commentsFile):
    comments = []
    with open(commentsFile, 'r') as cf:
        for line in cf:
            comments.append(line)
    comments = ''.join(comments)
    return comments

def print_to_stdout(*a):
    # Here a is the array holding the objects
    # passed as the argument of the function
    print(*a, file=sys.stdout)

def parseCommands():
    argv = sys.argv[1:]
    shortops = "cud"
    longopts = ["clone", "upload", "download", "changes", "fetch", "compare-to-remote=", 'listsubmodules', #main commands
                "folder=", "comments=", "commentsfile=", "remote=", "donothing", "all", "main",
                "submodule="]
    try:
        options, remainder = getopt.getopt(argv, shortops, longopts)
    except:
        print_to_stdout("Error")
        print_to_stdout(traceback.format_exc())
        sys.exit(1)

    print_to_stdout('options:', options)
    print_to_stdout('remainder:', remainder)

    options_frmt = {}
    for opt, arg in options:
        if opt not in options_frmt.keys():
            options_frmt[opt] = arg
        else:
            options_frmt[opt] = [options_frmt[opt]]
            options_frmt[opt].append(arg)

    for opt in options_frmt.keys():
        if opt in ['c', "--clone"]:
            gitClone(options_frmt.copy())
        elif opt in ['u', '--upload']:
            gitUpload(options_frmt.copy())
        elif opt in ['d', '--download']:
            gitDownload(options_frmt.copy())
        elif opt in ['--changes']:
            gitChanges(options_frmt.copy())
        elif opt in ['--fetch']:
            gitFetch(options_frmt.copy())
        elif opt in ['--compare-to-remote']:
            gitCompare(options_frmt.copy())
        elif opt in ['--listsubmodules']:
            gitListSubmodules(options_frmt.copy())

    sys.exit(0)

if __name__ == "__main__":
    parseCommands()
