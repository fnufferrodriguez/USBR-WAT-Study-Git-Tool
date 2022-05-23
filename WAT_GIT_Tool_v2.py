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
    if "--folder" not in options.keys():
        print_to_stdout("\nERROR: --folder not included in input.")
        sys.exit(1)
    print_to_stdout("Made it to clone")
    remote = default_URL
    for opt in options.keys():
        if opt == '--folder':
           folder = options[opt]
        elif opt == '--remote':
            remote = options[opt]

    print_to_stdout('USER HAS SELECTED:')
    print_to_stdout('folder:', folder)
    print_to_stdout('remote:', remote)

    if '--donothing' not in options.keys():
        checkDestinationDirectory(folder)
        try:
            response = git.Repo.clone_from(remote, folder, multi_options=['--recurse-submodule'])
            print_to_stdout('Clone complete.')
            repo = connect2GITRepo(folder)
            for submodule in repo.submodules:
                repo_submod = submodule.module()
                repo_submod.git.checkout('main')

        except git.exc.GitError:
            print_to_stdout("\nERROR:")
            print_to_stdout(traceback.format_exc())
            sys.exit(1)

    else:
        print_to_stdout('Do nothing mode engaged.')

    # sys.exit(0)

def gitUpload(options):

    if "--folder" not in options.keys():
        print_to_stdout("\nERROR: --folder not included in clone.")
        sys.exit(1)
    if '--comments' not in options.keys() and '--commentsfile' not in options.keys():
        print_to_stdout("\nERROR: --comments or --commentsfile not included in input.")
        sys.exit(1)
    print_to_stdout("Made it to upload")

    for opt in options.keys():
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

    if '--donothing' not in options.keys():
        repo = connect2GITRepo(folder)

        if '--all' in options.keys():
            if '--main' not in options.keys():
                options['--main'] = ''
            if '--submodule' not in options.keys():
                options['--submodule'] = []
            for submodule in repo.submodules:
                if submodule.name not in options['--submodule']:
                    options['--submodule'].append(submodule.name)

        if not any(x in options.keys() for x in ['--all', '--main', '--submodule']):
            options['--main'] = ''

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

        if '--main' in options.keys():
            changedFiles = getChangedFiles(repo)
            repo.git.add('--all')
            # repo.index.commit(comments)
            # response = repo.remotes.origin.push()
            printChangedFiles(changedFiles)

        if '--main' in options.keys() or '--submodule' in options.keys():
            # repo.git.add("--all")
            repo.index.commit(comments)
            try:
                response = repo.remotes.origin.push(recurse_submodules="on-demand")
            except git.exc.GitCommandError as e:
                if e.stderr.split('\n')[-1] == "fatal: failed to push all needed submodules'":
                    print_to_stdout(e.stderr)
                    print_to_stdout('\nERROR: Failed commit upload.')
                    sys.exit(1)
            print_to_stdout('Upload complete.')
        else:
            print_to_stdout("No upload target submitted.")
            print_to_stdout("Use --main or --submodule")

    else:
        print_to_stdout('Do nothing mode engaged.')

    # sys.exit(0)

def gitDownload(options):

    if "--folder" not in options.keys():
        print_to_stdout("\nERROR: --folder not included in clone.")
        sys.exit(1)

    print_to_stdout("Made it to download")

    for opt in options.keys():
        if opt == '--folder':
            folder = options[opt]

    print_to_stdout('USER HAS SELECTED:')
    print_to_stdout('folder:', folder)

    if '--donothing' not in options.keys():
        repo = connect2GITRepo(folder)

        if '--all' in options.keys():
            if '--main' not in options.keys():
                options['--main'] = ''
            if '--submodule' not in options.keys():
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
                    gitCompare(options, repo=repo, subrepo=submodule.name)
                    # gitCompare(options, repo=repo)
                    changedlocals = getChangedFiles(repo_submod)
                    printChangedFiles(changedlocals, "The following files will be overwritten:")
                    try:
                        repo_submod.git.reset('--hard')
                        repo_submod.git.pull()
                        print_to_stdout('Download complete.')
                    except git.exc.GitCommandError:
                        print_to_stdout(traceback.format_exc())
                        print_to_stdout('Error: Cannot download submodule {0}'.format(submodule))
            # if '--main' not in options.keys():
            #     gitCompare(options, repo=repo)
            #     changedlocals = getChangedFiles(repo)
            #     printChangedFiles(changedlocals, "The following files will be overwritten:")
            #     repo.git.reset('--hard')
            #     repo.git.pull()
            #     print_to_stdout('Download complete.')

    else:
        print_to_stdout('Do nothing mode engaged.')


def gitChanges(options):

    if "--folder" not in options.keys():
        print_to_stdout("\nERROR: --folder not included in clone.")
        sys.exit(1)

    print_to_stdout("Made it to Changes")

    for opt in options.keys():
        if opt == '--folder':
            folder = options[opt]

    print_to_stdout('USER HAS SELECTED:')
    print_to_stdout('folder:', folder)

    if '--donothing' not in options.keys():
        repo = connect2GITRepo(folder)

        if '--all' in options.keys():
            if '--main' not in options.keys():
                options['--main'] = ''
            if '--submodule' not in options.keys():
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

        if len(changed_file_list) > 0:
            printChangedFiles(changed_file_list)
        else:
            print_to_stdout('\nNo tracked files changed.')
    else:
        print_to_stdout("Do nothing mode engaged.")

def gitFetch(options):

    if "--folder" not in options.keys():
        print_to_stdout("\nERROR: --folder not included in clone.")
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


def gitCompare(options, comparisonType='files', repo=None, subrepo=None, returnlist=False):

    if "--folder" not in options.keys():
        print_to_stdout("\nERROR: --folder not included in options.")
        sys.exit(1)

    for opt in options.keys():
        if opt == '--folder':
            folder = options[opt]
        elif opt == '--compare-to-remote':
            comparisonType = options[opt]

    if repo == None: #time saver
        repo = connect2GITRepo(folder)

    if '--all' in options.keys():
        if '--main' not in options.keys():
            options['--main'] = ''
        if '--submodule' not in options.keys():
            options['--submodule'] = []
        for submodule in repo.submodules:
            if subrepo != None and submodule.name != subrepo:
                continue
            else:
                if submodule.name not in options['--submodule']:
                    options['--submodule'].append(submodule.name)

    if not any(x in options.keys() for x in ['--all', '--main', '--submodule']):
        options['--main'] = ''

    all_changed_files = []
    all_changed_commits = []

    if '--donothing' not in options.keys():

        if '--main' in options.keys():
            if comparisonType.lower() == 'files':
                changedFiles = compareFiles(repo)
                for file in changedFiles:
                    all_changed_files.append('Study/{0}'.format(file))

            elif comparisonType.lower() == 'commits':
                differentCommits = compareCommits(repo)
                for commit in differentCommits:
                    all_changed_commits.append('Study: {0}'.format(commit))

        if '--submodule' in options.keys():
            if isinstance(options['--submodule'], str):
                options['--submodule'] = [options['--submodule']]
            for submodule in repo.submodules:
                if subrepo != None and submodule.name != subrepo:
                    continue
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
        if returnlist:
            return all_changed_commits
    else:
        print_to_stdout("Do nothing mode engaged.")
        if returnlist:
            return []

    # if exit:
    #     sys.exit(0)

def gitListSubmodules(options):

    if "--folder" not in options.keys():
        print_to_stdout("\nERROR: -folder not included in options.")
        sys.exit(1)

    for opt in options.keys():
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

def gitCheckPushability(options):

    if "--folder" not in options.keys():
        print_to_stdout("\nERROR: --folder not included in options.")
        sys.exit(1)

    for opt in options.keys():
        if opt == '--folder':
            folder = options[opt]

    if not os.path.exists(folder):
        print_to_stdout(f'\nERROR: Specified Git folder {folder} does not exist.')
        sys.exit(1)

    if '--donothing' not in options.keys():
        repo = connect2GITRepo(folder)

        if '--all' in options.keys():
            if '--main' not in options.keys():
                options['--main'] = ''
            if '--submodule' not in options.keys():
                options['--submodule'] = []
            for submodule in repo.submodules:
                if submodule.name not in options['--submodule']:
                    options['--submodule'].append(submodule.name)

        if not any(x in options.keys() for x in ['--all', '--main', '--submodule']):
            options['--main'] = ''

        stats = repo.git.status(porcelain=True).split() #really only for submodules...

        if 'UU' in stats:
            error_repos = []
            for ni, n in enumerate(stats):
                if n == 'UU':
                    error_repo = stats[ni+1]
                    if error_repo in options['--submodule']:
                        error_repos.append(error_repo)
                    # print(f'\t{stats[ni+1]}')
            if len(error_repos) > 0:
                print_to_stdout('\nERROR: Conflicts found in the following:')
                for erepo in error_repos:
                    print(f'\t{erepo}')

                sys.exit(1)

        allpendingcommits = gitCompare(options, comparisonType='commits', repo=repo, returnlist=True)
        if len(allpendingcommits) > 0:
            print_to_stdout('\nERROR: Cannot upload with pending commits.')
            sys.exit(1)

        print_to_stdout('\nOk to upload!')

#TODO: This

# def resetDivergedBranch(options):
#
#     if "--folder" not in options.keys():
#         print_to_stdout("--folder not included in options.")
#         sys.exit(1)
#
#     for opt in options.keys():
#         if opt == '--folder':
#             folder = options[opt]
#
#     if '--donothing' not in options.keys():
#         repo = connect2GITRepo(folder)
#
#         if '--all' in options.keys():
#             if '--main' not in options.keys():
#                 options['--main'] = ''
#             if '--submodule' not in options.keys():
#                 options['--submodule'] = []
#             for submodule in repo.submodules:
#                 if submodule.name not in options['--submodule']:
#                     options['--submodule'].append(submodule.name)
#
#         if not any(x in options.keys() for x in ['--all', '--main', '--submodule']):
#             options['--main'] = ''
#
#         if '--main' in options.keys():
#             #git checkout main
#             #git branch -D main
#             #git switch -C main
#             repo.git.merge('--abort')
#             repo.git.checkout('origin/main')
#             repo.git.branch('-D', 'main')
#             repo.git.branch('main')
#             repo.git.checkout('main')
#
#         if '--submodule' in options.keys():
#             if isinstance(options['--submodule'], str):
#                 options['--submodule'] = [options['--submodule']]
#             for submodule in repo.submodules:
#                 if submodule.name in options['--submodule']:
#                     print_to_stdout('\nDownloading Submodule:', submodule.name)
#                     repo_submod = submodule.module()
#                     repo_submod.git.merge('--abort')
#                     repo_submod.git.checkout('origin/main')
#                     repo_submod.git.branch('-D', 'main')
#                     repo_submod.git.branch('main')
#                     repo_submod.git.checkout('main')


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
        print_to_stdout("\nERROR: Branch does not track a remote. Compare not possible.")
        sys.exit(1)

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
        print_to_stdout('\nERROR: Invalid GIT Repo directory: {0}'.format(repo_path))
        sys.exit(1)
    else:
        print_to_stdout(f'\nERROR: Unknown error connecting to GIT Repo directory: {repo_path}')
        sys.exit(1)

def checkDestinationDirectory(repo_dir):
    try:
        if os.path.exists(repo_dir):
            dirlen = os.listdir(repo_dir)
            if len(dirlen) == 0:
                return True
            else:
                print_to_stdout('\nERROR: Destination directory {0} already exists.'.format(repo_dir))
                sys.exit(1)
        else:
            print_to_stdout('\nCreating Directory at {0}..'.format(repo_dir))
            os.makedirs(repo_dir)
            return True
    except:
        print_to_stdout("\nERROR: ")
        print_to_stdout(traceback.format_exc())
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
                "submodule=", "okToPush", "fixDivergedBranch"]
    try:
        options, remainder = getopt.getopt(argv, shortops, longopts)
    except:
        print_to_stdout("\nError:")
        print_to_stdout(traceback.format_exc())
        sys.exit(1)

    print_to_stdout('options:', options)
    print_to_stdout('remainder:', remainder)

    options_frmt = {}
    for opt, arg in options:
        if opt not in options_frmt.keys():
            options_frmt[opt] = arg
        else:
            if isinstance(options_frmt[opt], str):
                options_frmt[opt] = [options_frmt[opt]]
                options_frmt[opt].append(arg)
            else:
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
        elif opt in ['--okToPush']:
            gitCheckPushability(options_frmt.copy())
        # elif opt in ['--fixDivergedBranch']:
        #     resetDivergedBranch(options_frmt.copy())

    sys.exit(0)

if __name__ == "__main__":
    parseCommands()
