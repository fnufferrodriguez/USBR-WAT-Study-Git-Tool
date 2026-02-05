'''
* Copyright 2022 United States Bureau of Reclamation (USBR).
* United States Department of the Interior
* All Rights Reserved. USBR PROPRIETARY/CONFIDENTIAL.
* Source may not be released without written approval
* from USBR

Created on 1/21/2022
@author: scott
@organization: Resource Management Associates
@contact: scott@rmanet.com
@note:
'''

import git
import time
import os, sys
import traceback
import shutil

default_URL = r'https://gitlab.rmanet.app/RMA/usbr-water-quality/wtmp-development-study/uppersac.git' #default

def welcomeScreen():
    print('\n##############################')
    print('Welcome to WAT GIT manager.')
    print('##############################')

def selectionScreen():
    options = {'1': {'text': 'Get new Watershed from GIT', 'function': 'getNewWatershed(git_url=default_URL)'}, #clone
               '2': {'text': 'Download Watershed changes from GIT', 'function': 'downloadWatershedChanges()'}, #pull
               '3': {'text': 'Upload Watershed changes to GIT', 'function': 'uploadWatershedChanges()'}, #push
               }

    options = addExitOption(options)
    presentOptions(options)
    response = getUserResponse()
    response = checkCorrectAnswer(response, options, 'presentOptions(options)')
    exec(options[response]['function'])
    selectionScreen()

def checkCorrectAnswer(response, options, message):
    while response.lower() not in [n.lower() for n in options.keys()]:
        print('\nInvalid Response.')
        exec(message)
        response = getUserResponse()
    frmt_response = [n for n in options.keys() if n.lower() == response.lower()][0]
    print('\nUser has Selected: {0} - {1}'.format(frmt_response, options[frmt_response]['text']))
    return frmt_response

def addExitOption(options):
    highest_number = 0
    for key in options.keys():
        try:
            keyint = int(key)
            if keyint > highest_number:
                highest_number = keyint
        except:
            continue
    options[str(highest_number+1)] = {'text': 'Exit', 'function': 'quitScript()'}
    return options

def presentOptions(options):
    print('\nPlease select an option below:')
    for key in options:
        print('{0}: {1}'.format(key, options[key]['text']))
    print()

def getUserResponse(message='Input: '):
    answer = input(message).strip()
    return answer

def quitScript():
    print('\nNow Exiting..')
    print('Goodbye!')
    time.sleep(2)
    sys.exit()

def getNewWatershed(git_url=None, repo_dir=None):
    if git_url == None:
        print('\nPlease enter the URL for the wanted GIT Repo to clone.')
        git_url = input('GIT URL: ').strip()
    if repo_dir == None:
        print('\nPlease enter the local directory to clone Repo to.')
        repo_dir = input('Directory: ').strip()
    print('\nUser has selected:')
    print('GIT URL:', git_url)
    print('Directory:', repo_dir)
    options = {'Y': {'text': 'Confirm Download', 'function': 'gitClone(git_url, repo_dir)'},
               'N': {'text': 'Change Settings', 'function': 'getNewWatershed()'},
               'Cancel': {'text': 'Return to Selection Screen', 'function': 'selectionScreen()'}}
    presentOptions(options)
    print('Clone Repo from GIT? (Y/N/Cancel)')
    response = getUserResponse()
    response = checkCorrectAnswer(response, options, 'presentOptions(options)')
    exec(options[response]['function'])
    selectionScreen()

def gitClone(git_url, repo_dir):
    localcheck = checkDestinationDirectory(repo_dir)
    if not localcheck:
        confirmContinue(funct='getNewWatershed(git_url=git_url)', git_url=git_url)
    try:
        print('\nStarting GIT Clone...')
        response = git.Repo.clone_from(git_url, repo_dir)
        printGitReponse(response)
        print('GIT Clone Complete!')
    except git.exc.GitError:
        print(traceback.format_exc())
        print('\nError cloning Git Repo at {0} to {1}'.format(git_url, repo_dir))
        print('Please Enter settings and try again.')
        getNewWatershed()

def checkDestinationDirectory(repo_dir):
    try:
        if os.path.exists(repo_dir):
            dirlen = os.listdir(repo_dir)
            if len(dirlen) == 0:
                return True
            else:
                print('\nDestination directory {0} already exists.'.format(repo_dir))
                print('Please enter a valid empty directory, or one that does not exist yet.')
                return False
        else:
            print('\nCreating Directory at {0}..'.format(repo_dir))
            os.makedirs(repo_dir)
            return True
    except Exception as e:
        print(e)
        print('')
        return False

def askForLocalRepo():
    print('\nEnter Watershed Directory')
    input = getUserResponse()
    return input

def connect2GITRepo(repo_path):
    try:
        repo = git.Repo(repo_path)
        print('\nConnected to GIT Repo!')
        os.chdir(repo_path)
        return repo
    except git.exc.GitError:
        print('\nInvalid GIT Repo directory: {0}'.format(repo_path))
        print('Please enter a valid Directory, or enter Cancel to return to the main menu.')
        repo_path = askForLocalRepo()
        if repo_path.lower() == 'cancel':
            selectionScreen()
        else:
            repo = connect2GITRepo(repo_path)
            return repo

def downloadWatershedChanges():
    gitRepo = askForLocalRepo()
    print('\nOverwrite files on local machine? (Y/N)')
    options = {'Y': {'text': 'Confirm GIT Overwrite', 'function': 'gitReset(gitRepo)'},
               'N': {'text': 'Cancel GIT Overwrite', 'function': 'selectionScreen()'}}
    response = getUserResponse()
    response = checkCorrectAnswer(response, options, 'presentOptions(options)')
    exec(options[response]['function'])

def gitReset(gitRepo):
    repo = connect2GITRepo(gitRepo)
    print('\nStarting Copy from GIT..')

    repo.git.reset('--hard')
    # repo.git.clean('-d', '-fx')
    repo.git.pull()
    print('GIT Download Complete!')


def printGitReponse(response):
    print('\nGIT CONSOLE: {0}'.format(response))

def uploadWatershedChanges():
    gitRepo = askForLocalRepo()
    print('\nUpload local files to GIT? (Y/N)')
    options = {'Y': {'text': 'Confirm GIT Upload', 'function': 'gitPush(gitRepo)'},
               'N': {'text': 'Cancel GIT Upload', 'function': 'selectionScreen()'}}
    response = getUserResponse()
    response = checkCorrectAnswer(response, options, 'presentOptions(options)')
    exec(options[response]['function'])

def gitPush(gitRepo):
    committext = getCommitText()
    repo = connect2GITRepo(gitRepo)
    confirmUpToDate(repo)
    # repo.git.add(update=True)
    print('\nStarting Upload to GIT...')
    repo.git.add('--all')
    repo.index.commit(committext)
    response = repo.remotes.origin.push()
    # response = repo.git.push()
    printGitReponse(response)
    print('GIT Upload Complete!')

def getCommitText():
    print('\nEnter Commit message:')
    committext = getUserResponse('message: ')
    options = {'Y': {'text': 'Confirm commit message', 'function': 'return'},
               'N': {'text': 'Re-Enter commit message', 'function': 'getCommitText()'},
               'Cancel': {'text': 'Cancel Upload', 'function': 'selectionScreen()'}}
    print('\nConfirm commit message?\n')
    print(committext)
    print('\n(Y/N/Cancel)')
    response = getUserResponse()
    response = checkCorrectAnswer(response, options, 'presentOptions(options)')
    if options[response]['function'] == 'return':
        return committext
    else:
        exec(options[response]['function'])

def confirmContinue(funct, **kwargs):
    locals().update(kwargs)
    options = {'Y': {'text': 'Re-Attempt Function', 'function': funct},
               'N': {'text': 'Cancel function', 'function': 'selectionScreen()'}}
    presentOptions(options)
    print('Try Function again? (Y/N)')
    response = getUserResponse()
    response = checkCorrectAnswer(response, options, 'presentOptions(options)')
    exec(options[response]['function'])

def confirmUpToDate(repo):
    print('\nChecking GIT status...')
    repo.git.fetch()
    status = repo.git.status()
    status = status.split('\n')
    if status[1].startswith('Your branch is up to date'):
        print('\nGIT branch up to date...')
        return
    else:
        print('\nGIT Repo Out of Date...')
        differentFiles = getDifferentFiles(repo)
        displayOutOfDateFiles(differentFiles)
        print('\nUser cannot upload until local Repo is up to date with Remote.')
        print('This will remove any changes done by the user.')
        options = {'Y': {'text': 'Backup Changed Files', 'function': 'backupChangedFiles(differentFiles)'},
                   'N': {'text': 'Cancel function', 'function': 'selectionScreen()'}}
        print('\nBack up user changes to Git_Backup folder? (Y/N)')
        response = getUserResponse()
        response = checkCorrectAnswer(response, options, 'presentOptions(options)')
        exec(options[response]['function'])

def getDifferentFiles(repo):
    # ischanged = repo.is_dirty(untracked_files=True)
    untracked = repo.untracked_files
    changedFiles = [item.a_path for item in repo.index.diff(None)]
    changedTracked = [n for n in changedFiles if n not in untracked]
    # changedTrackedexists = [n for n in changedTracked if os.path.exists(os.path.join(repopath, n))]
    # removedTracked = [n for n in changedTracked if not os.path.exists(os.path.join(repopath, n))]
    return changedTracked

def displayOutOfDateFiles(differentFiles):
    print('\nThe following files are out of date:')
    for i, n in enumerate(differentFiles):
        if i == 0:
            print('\t{0}'.format(n))
        else:
            print('\n\t{0}'.format(n))

def backupChangedFiles(differentFiles):
    if not os.path.exists('GIT_Backup'):
        os.mkdir('GIT_Backup')
    else:
        dirlist = os.listdir('GIT_Backup')
        if len(dirlist) != 0:
            print('\nClearing {0}...'.format(os.path.join(os.getcwd(), 'GIT_Backup')))
            for filename in dirlist:
                curfile = os.path.join('GIT_Backup', filename)
                if os.path.isdir(curfile): #check if directory..
                    shutil.rmtree(curfile)
                else:
                    os.remove(curfile)

    for filename in differentFiles:
        try:
            shutil.copyfile(filename, os.path.join('GIT_Backup', filename))
        except FileNotFoundError:
            os.makedirs(os.path.split(os.path.join('GIT_Backup', filename))[0])
            shutil.copyfile(filename, os.path.join('GIT_Backup', filename))

    print('\nBackup Complete. Changed Files now in GIT_Backup')
    options = {'Y': {'text': 'Download Watershed changes from GIT', 'function': 'downloadWatershedChanges()'},
               'N': {'text': 'Cancel function', 'function': 'selectionScreen()'}}
    print('Download latest from GIT and overwrite local files? (Y/N)')
    response = getUserResponse()
    response = checkCorrectAnswer(response, options, 'presentOptions(options)')
    exec(options[response]['function'])
    selectionScreen()



if __name__ == "__main__":
    welcomeScreen()
    selectionScreen()
