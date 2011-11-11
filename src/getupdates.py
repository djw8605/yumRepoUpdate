#!/usr/bin/python

import subprocess
import optparse
import copy
import make_table
import report

import logging
import yumrepo

repoquery = 'repoquery -a --qf "%%{name} %%{version} %%{release}" --disablerepo=* --enablerepo=%(repo)s'


def GetPreviousRPMs(old_file):
    rpm_dict = {}
    
    try:
        f = open(old_file)
    except:
        return rpm_dict

    for line in f.readlines():
        (name, release, version) = line.split()
        rpm_dict[name] = (release, version)

    return rpm_dict


def GetCurrentRPMs(repo):
    rpm_dict = {}
    cmd = repoquery % {'repo': repo}
    #print cmd
    current_repo = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = current_repo.communicate()
    for line in stdout.split("\n"):
        try:
            (name, release, version) = line.split(" ")
            rpm_dict[name] = (release, version)
        except:
            pass
            #print "Error unpacking line: %s" % line
    
    #if len(rpm_dict) == 0:
        #print "Didn't get any output"
    return rpm_dict


def CompareRPMs(current_rpms, previous_rpms):
    new_rpms = {}
    new_versions = {}
    deleted_rpms = {}

    for rpm in current_rpms.keys():
        if rpm not in previous_rpms.keys():
            # New RPM
            #print "New rpm: %s" % rpm 
            new_rpms[rpm] = current_rpms[rpm]

        elif current_rpms[rpm] != previous_rpms[rpm]:
            # Changed version
            #print "RPM %s changed versions to %s" % (rpm, "-".join(current_rpms[rpm]))
            new_versions[rpm] = current_rpms[rpm]
            del previous_rpms[rpm]

        elif current_rpms[rpm] == previous_rpms[rpm]:
            # Same version
            del previous_rpms[rpm]


    # Anything left over in the dictionaries are removed rpms
    for rpm in previous_rpms.keys():
        #print "RPM was deleted: %s" % rpm
        deleted_rpms[rpm] = previous_rpms[rpm]

    return (new_rpms, new_versions, deleted_rpms)
    

def WriteCurrentRPMs(old_file, current_rpms):
    f = open(old_file, 'w')
    for rpm in current_rpms.keys():
        f.write("%s %s %s\n" % (rpm, current_rpms[rpm][0], current_rpms[rpm][1]))
    f.close()


def GetMostRecentChangeLog(rpm_list, repo):
    rpm_changelog = {}
    changelog_query = 'repoquery -a %(package)s --qf "%%{changelog}" --disablerepo=* --enablerepo=%(repo)s'
    for rpm in rpm_list:
        cmd = changelog_query % {'package': rpm, 'repo': repo}
        changelogs = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (stdout, stderr) = changelogs.communicate()
        rpm_changelog[rpm] = stdout.split("\n\n")[0]

    return rpm_changelog

def MakeTable(new_rpms, new_versions, deleted_rpms):
    table = make_table.Table(add_numbers = False)
    table.setHeaders(["RPM Name", "Changelog entry"])

    table.addRow(["New RPMs", ""])
    for rpm in new_rpms.keys():
        table.addRow(["", ""])
        split_changelog = new_rpms[rpm].split("\n")
        table.addRow([rpm, split_changelog[0].strip()])
        split_changelog.pop(0)
        for line in split_changelog:
            table.addRow(["", line])
    
    table.addBreak()
    table.addRow(["Updated RPMs", ""])

    for rpm in new_versions.keys():
        table.addRow(["", ""])
        split_changelog = new_versions[rpm].split("\n")
        table.addRow([rpm, split_changelog[0].strip()])
        split_changelog.pop(0)
        for line in split_changelog:
            table.addRow(["", line])


    table.addBreak()
    table.addRow(["Deleted RPMs", ""])

    for rpm in deleted_rpms.keys():
        table.addRow([rpm, ""])

    log = logging.getLogger("test")
    report.sendEmail(("Derek Weitzel", "dweitzel@cse.unl.edu"), (["Derek Weitzel"], ["dweitzel@cse.unl.edu"]), "cse.unl.edu", "RPM Changes", table.plainText(), table.html(), log)
#    print table.plainText()




def AddOptions(parser):
    parser.add_option("-f", "--file", dest="oldfile", help="Old RPMs file location")
    parser.add_option("-r", "--repo", dest="repo", help="Repo to query")
    

def main():
    parser = optparse.OptionParser()
    AddOptions(parser)

    (options, args) = parser.parse_args()
    
    #print "Querying repo: %s" % options.repo
    current_rpms = GetCurrentRPMs(options.repo)
    previous_rpms = GetPreviousRPMs(options.oldfile)
    saved_current_rpms = copy.deepcopy(current_rpms)

    (new_rpms, new_version, deleted_rpms) = CompareRPMs(current_rpms, previous_rpms)

    WriteCurrentRPMs(options.oldfile, current_rpms)
    
    new_rpms_changelog = GetMostRecentChangeLog(new_rpms.keys(), options.repo)
    new_versions_changelog = GetMostRecentChangeLog(new_version.keys(), options.repo)

    MakeTable(new_rpms_changelog, new_versions_changelog, deleted_rpms)
    

if __name__ == "__main__":
    main()

