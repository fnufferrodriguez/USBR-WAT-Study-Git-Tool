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

VERSION_NUMBER = '3.2'

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
            repo = connect2GITRepo(folder) #clone, and then set up. Only one allowed to do this.
            for submodule in repo.submodules:
                repo_submod = submodule.module()
                repo_submod.git.checkout('main')

        except git.exc.GitError:
            print_to_stdout("\nERROR:")
            print_to_stdout(traceback.format_exc())
            sys.exit(1)

    else:
        print_to_stdout('Do nothing mode engaged.')

def gitUpload(options):

    if '--comments' not in options.keys() and '--commentsfile' not in options.keys():
        print_to_stdout("\nERROR: --comments or --commentsfile not included in input.")
        sys.exit(1)

    print_to_stdout("\nPerforming Upload.")

    for opt in options.keys():
        if opt == '--comments':
            comments = options[opt]
        elif opt == '--commentsfile':
            commentsfile = options[opt]
            comments = readCommentsFile(commentsfile)

    print_to_stdout('comments:\n\t{0}'.format(comments))

    if '--donothing' not in options.keys():
        repo = options['repo']

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
                    print_to_stdout('\nUploading submodule:', submodule.name)
                    repo_submod = submodule.module()
                    changedFiles = getChangedFiles(repo_submod)
                    repo_submod.git.add('--all')
                    repo_submod.index.commit(comments)
                    repo.git.add(submodule.path)
                    print_to_stdout('Checking tracked local files..')
                    printChangedFiles(changedFiles)

        if '--main' in options.keys():
            print_to_stdout('\nUploading main study module.')
            changedFiles = getChangedFiles(repo)
            repo.git.add('--all')
            # repo.index.commit(comments)
            # response = repo.remotes.origin.push()
            print_to_stdout('Checking tracked local files..')
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
                    gitResetHead(options)
                    sys.exit(1)

            print_to_stdout('Upload complete.')
        else:
            print_to_stdout("No upload target submitted.")
            print_to_stdout("Use --main or --submodule")

    else:
        print_to_stdout('Do nothing mode engaged.')

def gitDownload(options):

    print_to_stdout("\nPerforming download.")

    for opt in options.keys():
        if opt == '--folder':
            folder = options[opt]

    if '--donothing' not in options.keys(): #git restore path-to-your/submodule-name --recurse-submodules
        repo = options['repo']

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

        fulloverwrite = True
        if '--softoverwrite' in options.keys():
            fulloverwrite = False

        failed_downloads = []

        if '--main' in options.keys():
            print_to_stdout('\nDownloading main study module.')
            # gitCompare(options, mainonly=True) #TODO: make this look at main repo only.
            if fulloverwrite:
                changedlocals = getChangedFiles(repo)
                print_to_stdout('Checking tracked local files..')
                printChangedFiles(changedlocals, "The following files will be overwritten:")
            else:
                compareLocalAndServerFiles(repo)

            try:
                if fulloverwrite:
                    repo.git.reset('--hard')
                repo.git.pull()
                print_to_stdout('Download complete.')
            except:
                print_to_stdout(traceback.format_exc())
                print_to_stdout('Error: Cannot download Main')
                failed_downloads.append('Main')
        if '--submodule' in options.keys():
            if isinstance(options['--submodule'], str):
                options['--submodule'] = [options['--submodule']]
            for submodule in repo.submodules:
                if submodule.name in options['--submodule']:
                    if not os.path.exists(os.path.join(folder, submodule.path, '.git')):
                        print_to_stdout(f'Folder for submodule {submodule.name} not found.')
                        continue

                    print_to_stdout('\nDownloading Submodule:', submodule.name)
                    repo_submod = submodule.module()
                    # gitCompare(options, subrepo=submodule.name)

                    if fulloverwrite:
                        changedlocals = getChangedFiles(repo_submod)
                        print_to_stdout('Checking tracked local files..')
                        printChangedFiles(changedlocals, "The following files will be overwritten:")
                    else:
                        compareLocalAndServerFiles(repo_submod)

                    try:
                        if fulloverwrite:
                            repo_submod.git.reset('--hard')
                        repo_submod.git.pull()
                        print_to_stdout('Download complete.')
                    # except git.exc.GitCommandError:
                    except:
                        print_to_stdout(traceback.format_exc())
                        print_to_stdout('Error: Cannot download submodule {0}'.format(submodule))
                        failed_downloads.append(submodule)

        if len(failed_downloads):
            print_to_stdout('ERROR: Failed to download the following:')
            for fd in failed_downloads:
                print_to_stdout(f'  {fd}')
            sys.exit(1)

    else:
        print_to_stdout('Do nothing mode engaged.')

def gitChanges(options):

    print_to_stdout("Comparing changes.")

    if '--donothing' not in options.keys():
        repo = options['repo']

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

        print_to_stdout('Checking tracked local files..')
        if len(changed_file_list) > 0:
            printChangedFiles(changed_file_list)
        else:
            print_to_stdout('\nNo tracked files changed.')
    else:
        print_to_stdout("Do nothing mode engaged.")

def gitFetch(options):

    print_to_stdout("\nPerforming fetch.")

    if not any(x in options.keys() for x in ['--all', '--main', '--submodule']):
        options['--main'] = ''

    if '--donothing' in options.keys():
        print_to_stdout("Do nothing mode engaged.")
    elif '--all' in options.keys():
        repo = options['repo']
        repo.git.fetch(recurse_submodules=True)

    else:
        repo = options['repo']
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

    print_to_stdout('Fetch complete.')

def gitCompare(options, comparisonType='files', mainonly=False, subrepo=None, returnlist=False, printpending=True):

    for opt in options.keys():
        if opt == '--compare-to-remote':
            comparisonType = options[opt]

    repo = options['repo']

    if '--all' in options.keys():
        if '--main' not in options.keys():
            options['--main'] = ''
        if '--submodule' not in options.keys():
            options['--submodule'] = []
        for submodule in repo.submodules:
            if subrepo != None and submodule.name != subrepo or mainonly:
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
                for sm in repo.submodules: #do a check for the submodules and don't print those out. Only for main.
                    if sm.name in changedFiles:
                        changedFiles.remove(sm.name)
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
                if subrepo != None and submodule.name != subrepo or mainonly:
                    continue
                if submodule.name in options['--submodule']:
                    try:
                        repo_submod = submodule.module()

                        if comparisonType.lower() == 'files':
                            changedFiles = compareFiles(repo_submod)
                            for file in changedFiles:
                                all_changed_files.append('{0}/{1}'.format(submodule, file))

                        elif comparisonType.lower() == 'commits':
                            differentCommits = compareCommits(repo_submod)
                            for commit in differentCommits:
                                all_changed_commits.append('{0}: {1}'.format(submodule, commit))
                    except:
                        print_to_stdout(f'ERROR: cannot compare {submodule.name}')

        if comparisonType.lower() == 'files':
            print_to_stdout('Checking for changed files on the server..')
            if printpending:
                if len(all_changed_files) > 0:
                    printChangedFiles(all_changed_files, message='Pending Files:')
                else:
                    print_to_stdout('No files changed.')
            if returnlist:
                return all_changed_files

        elif comparisonType.lower() == 'commits':
            print_to_stdout('Checking for new commits on the server..')
            if printpending:
                if len(all_changed_commits) > 0:
                    printChangedFiles(all_changed_commits, message='Pending Commits:')
                else:
                    print_to_stdout('No new commits.')
            if returnlist:
                return all_changed_commits
    else:
        print_to_stdout("Do nothing mode engaged.")
        if returnlist:
            return []

def gitListSubmodules(options):

    repo = options['repo']
    submodules = repo.submodules
    if len(submodules) == 0:
        print_to_stdout('\nNo Submodules detected.')
    else:
        print_to_stdout('\nSubmodules in main repo:')
        for submodule in submodules:
            print_to_stdout(submodule.name)

def gitCheckPushability(options):

    print_to_stdout('\nConfirming Pushability to server.')

    if '--donothing' not in options.keys():
        repo = options['repo']

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

        if "--main" not in options.keys():
            checkMainRepo(options)

        if '--main' not in options.keys():
            options['--main'] = ''

        isdetached = False
        if '--main' in options.keys():
            if repo.head.is_detached:
                print_to_stdout('Study main branch is detached')
                print_to_stdout('Restore Study branch.')
                isdetached = True
        if '--submodule' in options.keys():
            if isinstance(options['--submodule'], str):
                options['--submodule'] = [options['--submodule']]
            for submodule in repo.submodules:
                if submodule.name in options['--submodule']:
                    repo_submod = submodule.module()
                    if repo_submod.head.is_detached:
                        print_to_stdout(f'{submodule.name} branch is detached')
                        print_to_stdout(f'Restore {submodule.name} branch.')
                        isdetached = True
        if isdetached:
            sys.exit(1)

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

        allpendingcommits = gitCompare(options, comparisonType='commits', returnlist=True)
        if len(allpendingcommits) > 0:
            print_to_stdout('\nERROR: Cannot upload with pending commits.')
            sys.exit(1)

        print_to_stdout('Ok to upload!')

def gitCheckPullability(options):

    print_to_stdout('\nConfirming Pullability from the server.')

    if '--donothing' not in options.keys():
        repo = options['repo']

        if '--all' in options.keys():
            if '--main' not in options.keys():
                options['--main'] = ''
            if '--submodule' not in options.keys():
                options['--submodule'] = []
            for submodule in repo.submodules:
                if submodule.name not in options['--submodule']:
                    options['--submodule'].append(submodule.name)

        if "--main" not in options.keys():
            checkMainRepo(options)

        if not any(x in options.keys() for x in ['--all', '--main', '--submodule']):
            options['--main'] = ''

        isdetached = False
        if '--main' in options.keys():
            if repo.head.is_detached:
                print_to_stdout('ERROR: Study main branch is detached')
                print_to_stdout('Restore Study branch.')
                isdetached = True
        if '--submodule' in options.keys():
            if isinstance(options['--submodule'], str):
                options['--submodule'] = [options['--submodule']]
            for submodule in repo.submodules:
                if submodule.name in options['--submodule']:
                    repo_submod = submodule.module()
                    if repo_submod.head.is_detached:
                        print_to_stdout(f'ERROR: {submodule.name} branch is detached')
                        print_to_stdout(f'Restore {submodule.name} branch.')
                        isdetached = True
        if isdetached:
            sys.exit(1)

        if '--main' in options.keys():
            print_to_stdout('\nChecking main study directory for potential merge conflicts..')
            compareLocalAndServerFiles(repo)
        if '--submodule' in options.keys():
            if isinstance(options['--submodule'], str):
                options['--submodule'] = [options['--submodule']]
            for submodule in repo.submodules:
                if submodule.name in options['--submodule']:
                    repo_submod = submodule.module()
                    print_to_stdout(f'\nChecking Submodule {submodule.name} for potential merge conflicts..')
                    compareLocalAndServerFiles(repo_submod)

        print_to_stdout('Ok to download!')
    else:
        print_to_stdout('do nothing mode engaged')

def gitDiffFile(options):
    if '--donothing' not in options.keys():
        repo = options['repo']
        folder = options['--folder']
        if '--file' not in options.keys():
            print_to_stdout('No file selected to diff.')
            sys.exit(1)
        diff_file = options['--file']
        diff_file_path = os.path.join(folder, diff_file)
        if not os.path.exists(diff_file_path): #do a check for study to be at the front? remove this?
            print_to_stdout(f'File {diff_file_path} does not exist.')
            sys.exit(1)
        if '--submodule' in options.keys():
            difftext = repo.submodules[options['--submodule']].module().git.diff(diff_file_path)
        else:
            difftext = repo.git.diff(diff_file_path)
        print_to_stdout(difftext)
    else:
        print_to_stdout("Do nothing mode engaged.")

def gitResetHead(options):
    print_to_stdout('\nResetting Commits.')
    if '--donothing' not in options.keys():
        repo = options['repo']
        if '--all' in options.keys():
            if '--main' not in options.keys():
                options['--main'] = ''
            if '--submodule' not in options.keys():
                options['--submodule'] = []
            for submodule in repo.submodules:
                if submodule.name not in options['--submodule']:
                    options['--submodule'].append(submodule.name)

        if '--submodule' in options.keys():
            if isinstance(options['--submodule'], str):
                options['--submodule'] = [options['--submodule']]
            for submodule in repo.submodules:
                if submodule.name in options['--submodule']:
                    repo_submod = submodule.module()
                    print_to_stdout(f'Resetting {submodule.name}')
                    repo_submod.head.reset('HEAD~')
        print_to_stdout('Resetting main repo')
        repo.head.reset('HEAD~')

        print_to_stdout('Reset complete.')

def compareLocalAndServerFiles(repo):
    # allpendingfiles = gitCompare(options, comparisonType='files', repo=repo, returnlist=True, printpending=False)
    changedServerFiles = compareFiles(repo)
    changedLocalfiles = getChangedFiles(repo)
    tobeclobbered = [n for n in changedLocalfiles if n in changedServerFiles]
    changedbutsafe = [n for n in changedLocalfiles if n not in changedServerFiles]

    if len(tobeclobbered) > 0:
        print_to_stdout('The following files have been changed on server and locally:')
        for filen in tobeclobbered:
            print_to_stdout(f'\t{filen}')
    else:
        print_to_stdout('No files changed on both server and local file system.')

    if len(changedbutsafe) > 0:
        print_to_stdout("The following files have changed locally but not on server:")
        for filen in changedbutsafe:
            print_to_stdout(f'\t{filen}')
    else:
        print_to_stdout('No files changed on local file system but not server.')


def gitRestore(options):

    for opt in options.keys():
        if opt == '--folder':
            folder = options[opt]

    if not os.path.exists(folder):
        print_to_stdout(f'\nERROR: Specified Git folder {folder} does not exist. Unable to restore.')
        sys.exit(1)

    if '--donothing' not in options.keys():
        repo = options['repo']

        print_to_stdout('\nPerforming Restore.')

        if not any(x in options.keys() for x in ['--all', '--main', '--submodule']):
            options['--main'] = ''

        if '--all' in options.keys():
            print_to_stdout('Restoring all.')
            repo.git.restore(folder, recurse_submodules=True)
            for submodule in repo.submodules:
                repo_submod = submodule.module()
                repo_submod.git.checkout('main')

        if '--main' in options.keys():
            print_to_stdout('Restoring main study module.')
            repo.git.restore(folder, recurse_submodules=False)

        if '--submodule' in options.keys():
            for submodule in repo.submodules:
                if submodule.name in options['--submodule']:
                    print_to_stdout(f'Restoring {submodule.name}.')
                    submod_folder = os.path.join(folder, submodule.path)
                    repo.git.restore(submod_folder, recurse_submodules=True)
                    submodule.module().git.checkout('main')

        print_to_stdout('Restore complete.')
    else:
        print_to_stdout("Do nothing mode engaged.")

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
    except Exception:
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

def checkMainRepo(options):
    print_to_stdout('Checking Parent module.')
    newoptions = {'--main': '',
                  'repo': options['repo'],
                  '--softoverwrite': ''}

    commits = gitCompare(newoptions, comparisonType='commits', returnlist=True, printpending=False)
    if len(commits) == 0: #if no new commits, no need to do anything
        print_to_stdout('Parent module up to date.')
        return

    pendingfiles = gitCompare(newoptions, comparisonType='files', returnlist=True, printpending=False)
    if len(pendingfiles) > 0: #If there are actual files, we want to make sure thats done properly.
        print_to_stdout('Parent module has pending files.')
        return
    print_to_stdout('Updating .git file in parent module.')
    print_to_stdout('No other files will be altered...')
    gitDownload(newoptions)
    print_to_stdout('Parent module updated.')

def print_to_stdout(*a):
    # Here a is the array holding the objects
    # passed as the argument of the function
    print(*a, file=sys.stdout)

def setUpRepo(options):
    if "--folder" not in options.keys():
        print_to_stdout("\nERROR: --folder not included in input.")
        sys.exit(1)
    folder = options['--folder']
    print_to_stdout('Logging into Repo..')
    print_to_stdout(f'User has selected {folder}')
    repo = connect2GITRepo(folder)
    options['repo'] = repo
    return options

def parseCommands():
    print_to_stdout(f'GIT WAT TOOL v{VERSION_NUMBER}')
    argv = sys.argv[1:]
    shortops = ""
    longopts = ["clone", "upload", "download", "changes", "fetch", "compare-to-remote=", 'listsubmodules', #main commands
                "folder=", "comments=", "commentsfile=", "remote=", "donothing", "all", "main", "restore",
                "submodule=", "okToPush", "okToPull", "fixDivergedBranch", "softoverwrite", "diff", "file="]
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

    if '--clone' not in options_frmt.keys():
        options_frmt = setUpRepo(options_frmt)

    for opt in options_frmt.keys():
        if opt in ["--clone"]:
            gitClone(options_frmt.copy())
        elif opt in ['--upload']:
            gitUpload(options_frmt.copy())
        elif opt in ['--download']:
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
        elif opt in ['--restore']:
            gitRestore(options_frmt.copy())
        elif opt in ['--okToPull']:
            gitCheckPullability(options_frmt.copy())
        elif opt in ['--diff']:
            gitDiffFile(options_frmt.copy())

    sys.exit(0)

if __name__ == "__main__":
    parseCommands()
