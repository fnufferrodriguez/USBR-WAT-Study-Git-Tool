'''
* Copyright 2022 United States Bureau of Reclamation (USBR).
* United States Department of the Interior
* All Rights Reserved. USBR PROPRIETARY/CONFIDENTIAL.
* Source may not be released without written approval
* from USBR

Created on 2/10/2022
@author: scott
@organization: Resource Management Associates
@contact: scott@rmanet.com
@note:
'''
import sys, os
import git
import getopt
import traceback

def gitClone(options):
    default_URL = r'https://gitlab.rmanet.app/RMA/usbr-water-quality/wtmp-development-study/uppersac.git' #default
    opts = []
    for opt in options:
        opts.append(opt[0])
    if "--folder" not in opts:
        print_to_stdout("--folder not included in input.")
        print_to_stdout("now exiting..")
        sys.exit(1)
    print_to_stdout("Made it to clone")
    remote = default_URL
    for opt in options:
        if opt[0] == '--folder':
           folder = opt[1]
        elif opt[0] == '--remote':
            remote = opt[1]

    print_to_stdout('USER HAS SELECTED:')
    print_to_stdout('folder:', folder)
    print_to_stdout('remote:', remote)

    if '--donothing' not in opts:
        checkDestinationDirectory(folder)
        try:
            response = git.Repo.clone_from(remote, folder)
            print_to_stdout('Clone complete.')
        except git.exc.GitError:
            print_to_stdout(traceback.format_exc())
            sys.exit(1)
    else:
        print_to_stdout('Do nothing mode engaged.')

    sys.exit(0)

def gitUpload(options):
    opts = []
    for opt in options:
        opts.append(opt[0])
    if "--folder" not in opts:
        print_to_stdout("--folder not included in clone.")
        print_to_stdout("now exiting..")
        sys.exit(1)
    if '--comments' not in opts and '--commentsfile' not in opts:
        print_to_stdout("--comments or --commentsfile not included in input.")
        print_to_stdout("now exiting..")
        sys.exit(1)
    print_to_stdout("Made it to upload")

    for opt in options:
        if opt[0] == '--folder':
            folder = opt[1]
        elif opt[0] == '--comments':
            comments = opt[1]
        elif opt[0] == '--commentsfile':
            commentsfile = opt[1]
            comments = readCommentsFile(commentsfile)

    print_to_stdout('USER HAS SELECTED:')
    print_to_stdout('folder:', folder)
    print_to_stdout('comments:\n{0}'.format(comments))

    if '--donothing' not in opts:
        repo = connect2GITRepo(folder)
        changedFiles = getChangedFiles(repo)
        repo.git.add('--all')
        repo.index.commit(comments)
        response = repo.remotes.origin.push()
        print_to_stdout('Upload complete.')
        printChangedFiles(changedFiles)
    else:
        print_to_stdout('Do nothing mode engaged.')

    sys.exit(0)

def gitDownload(options):
    opts = []
    for opt in options:
        opts.append(opt[0])
    if "--folder" not in opts:
        print_to_stdout("--folder not included in clone.")
        print_to_stdout("now exiting..")
        sys.exit(1)

    print_to_stdout("Made it to download")

    for opt in options:
        if opt[0] == '--folder':
            folder = opt[1]

    print_to_stdout('USER HAS SELECTED:')
    print_to_stdout('folder:', folder)

    if '--donothing' not in opts:
        repo = connect2GITRepo(folder)
        changedFiles = getChangedFiles(repo)
        repoChangedFiles = compareFiles(repo)
        repo.git.reset('--hard')
        repo.git.pull()
        print_to_stdout('Download complete.')
        printChangedFiles([changedFiles, repoChangedFiles])

    else:
        print_to_stdout('Do nothing mode engaged.')

    sys.exit(0)

def gitChanges(options):
    opts = []
    for opt in options:
        opts.append(opt[0])
    if "--folder" not in opts:
        print_to_stdout("--folder not included in clone.")
        print_to_stdout("now exiting..")
        sys.exit(1)

    print_to_stdout("Made it to Changes")

    for opt in options:
        if opt[0] == '--folder':
            folder = opt[1]

    print_to_stdout('USER HAS SELECTED:')
    print_to_stdout('folder:', folder)

    repo = connect2GITRepo(folder)
    changedTracked = getChangedFiles(repo)

    if len(changedTracked) > 0:
        printChangedFiles(changedTracked)
    else:
        print_to_stdout('\nNo tracked files changed.')

    sys.exit(0)

def gitFetch(options):
    opts = []
    for opt in options:
        opts.append(opt[0])
    if "--folder" not in opts:
        print_to_stdout("--folder not included in clone.")
        print_to_stdout("now exiting..")
        sys.exit(1)

    print_to_stdout("Made it to Fetch")

    for opt in options:
        if opt[0] == '--folder':
            folder = opt[1]

    print_to_stdout('USER HAS SELECTED:')
    print_to_stdout('folder:', folder)

    repo = connect2GITRepo(folder)

    print_to_stdout("Made it to Fetch")

    repo.git.fetch()
    sys.exit(0)

def gitCompare(options):
    opts = []
    for opt in options:
        opts.append(opt[0])
    if "--folder" not in opts:
        print_to_stdout("--folder not included in clone.")
        print_to_stdout("now exiting..")
        sys.exit(1)

    for opt in options:
        if opt[0] == '--folder':
            folder = opt[1]
        elif opt[0] == '--compare-to-remote':
            comparisonType = opt[1]
    
    repo = connect2GITRepo(folder)

    if comparisonType.lower() == 'files':
        changedFiles = compareFiles(repo)

        if len(changedFiles) > 0:
            printChangedFiles(changedFiles, message='Pending Files:')
        else:
            print_to_stdout('\nNo files changed.')
    elif comparisonType.lower() == 'commits':
        differentCommits = compareCommits(repo)

        if len(differentCommits) > 0:
            print_to_stdout('Pending Commits:')
            for commit in differentCommits:
                print_to_stdout('\t'+commit)
        else:
            print_to_stdout("\nNo new commits.")

    sys.exit(0)

def compareCommits(repo):
    remoteBranch = getCurrentBranchRemote(repo)
    if remoteBranch is None:
        print_to_stdout("\nBranch does not track a remote. Compare not possible.")
        sys.exit(2)

    current_hex = repo.head.object.hexsha
    repohex = repo.git.log(remoteBranch,'--pretty=%H').split('\n')[0]
    if current_hex == repohex:
        return []
    else:
        commits = repo.git.log(current_hex+'...'+repohex, '--oneline').split('\n')
        return commits

def compareFiles(repo):
    remoteBranch = getCurrentBranchRemote(repo)
    if remoteBranch is None:
        print_to_stdout("\nBranch does not track a remote. Compare not possible.")
        sys.exit(2)

    current_hex = repo.head.object.hexsha
    repohex = repo.git.log(remoteBranch,'--pretty=%H').split('\n')[0]
    if current_hex == repohex:
        return []
    else:
        changedFiles = repo.git.diff(current_hex, repohex, '--name-only').split('\n')
        return changedFiles

def getCurrentBranchRemote(repo):
    branchStatus = repo.git.status('-s','-b')
    if '...' not in branchStatus:
        return None

    remoteBranchEndPart = branchStatus.split('...')[1]
    remoteBranch = remoteBranchEndPart.split('[')[0].strip()
    return remoteBranch

# def getRepoChangedFiles(repo):
#     changedRemote = repo.git.show('HEAD', pretty="", name_only=True).split('\n')
#     return changedRemote

def getChangedFiles(repo):
    untracked = repo.untracked_files
    changedFiles = [item.a_path for item in repo.index.diff(None)]
    changedTracked = [n for n in changedFiles if n not in untracked]
    return changedTracked

def printChangedFiles(changedFiles, message="Files Changed:"):
    cFiles_frmt = formatChangedFiles(changedFiles)
    if len(cFiles_frmt) == 0:
        print_to_stdout('No files changed..')
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
    longopts = ["clone", "upload", "download", "changes", "fetch", "folder=",
                "comments=", "commentsfile=", "remote=", "donothing",
                "compare-to-remote="]
    try:
        options, remainder = getopt.getopt(argv, shortops, longopts)
    except:
        print_to_stdout("Error")
        sys.exit(1)

    print_to_stdout('options:', options)
    print_to_stdout('remainder:', remainder)

    for opt, arg in options:
        if opt in ['c', "--clone"]:
            gitClone(options)
        elif opt in ['u', '--upload']:
            gitUpload(options)
        elif opt in ['d', '--download']:
            gitDownload(options)
        elif opt in ['--changes']:
            gitChanges(options)
        elif opt in ['--fetch']:
            gitFetch(options)
        elif opt in ['--compare-to-remote']:
            gitCompare(options)

if __name__ == "__main__":
    parseCommands()
