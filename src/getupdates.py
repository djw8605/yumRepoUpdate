#!/usr/bin/python

import subprocess
import optparse
import copy
import make_table
import report

import logging
import yumrepo


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
    
    yum_repo_obj = yumrepo.YumRepo(repo)
    return yum_repo_obj.getPackageNames()
    

def CompareRPMs(current_rpms, previous_rpms):
    new_rpms = {}
    new_versions = {}
    deleted_rpms = {}
    
    
    for rpm in current_rpms.keys():
        if rpm not in previous_rpms.keys():
            # New RPM
            #print "New rpm: %s" % rpm 
            new_rpms[rpm] = current_rpms[rpm]

        elif current_rpms[rpm].version != previous_rpms[rpm][0] or current_rpms[rpm].release != previous_rpms[rpm][1]:
            # Changed version
            #print "RPM %s changed versions to %s" % (rpm, "-".join(current_rpms[rpm]))
            new_versions[rpm] = current_rpms[rpm]
            del previous_rpms[rpm]

        elif current_rpms[rpm].version == previous_rpms[rpm][0] and current_rpms[rpm].release == previous_rpms[rpm][1]:
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
        f.write("%s %s %s\n" % (rpm, current_rpms[rpm].version, current_rpms[rpm].release))
    f.close()


def GetMostRecentChangeLog(rpm_list):
    rpm_changelog = {}
    
    for rpm in rpm_list.keys():
        if len(rpm_list[rpm].changelog) > 0:
            rpm_changelog[rpm_list[rpm].name] = rpm_list[rpm].changelog[0]
        else:
            rpm_changelog[rpm_list[rpm].name] = ""

    return rpm_changelog


def MakeTable(new_rpms, new_versions, deleted_rpms, repo):
    table = make_table.Table(add_numbers = False)
    table.setHeaders(["RPM Name", "Changelog entry"])

    table.addRow(["New RPMs", ""])
    for rpm in new_rpms.keys():
        combined_changelog = "\n".join(new_rpms[rpm][1:3])
        split_changelog = combined_changelog.split("\n")
        table.addRow([rpm, split_changelog[0]])
        split_changelog.pop(0)
        for line in split_changelog:
            table.addRow(["", line])
        table.addRow(["", ""])
    
    table.addBreak()
    table.addRow(["Updated RPMs", ""])

    for rpm in new_versions.keys():
        combined_changelog = "\n".join(new_versions[rpm][1:3])
        split_changelog = combined_changelog.split("\n")
        table.addRow([rpm, split_changelog[0]])
        split_changelog.pop(0)
        for line in split_changelog:
            table.addRow(["", line])
        table.addRow(["", ""])


    table.addBreak()
    table.addRow(["Deleted RPMs", ""])

    for rpm in deleted_rpms.keys():
        table.addRow([rpm, ""])

    log = logging.getLogger("test")
    report.sendEmail(("Derek Weitzel", "dweitzel@cse.unl.edu"), (["Derek Weitzel"], ["dweitzel@cse.unl.edu"]), "cse.unl.edu", "%s: RPM Changes" % repo, table.plainText(), table.html(), log)
    #print table.plainText()




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
    saved_current_rpms = copy.copy(current_rpms)

    (new_rpms, new_version, deleted_rpms) = CompareRPMs(current_rpms, previous_rpms)

    WriteCurrentRPMs(options.oldfile, current_rpms)
    
    new_rpms_changelog = GetMostRecentChangeLog(new_rpms)
    new_versions_changelog = GetMostRecentChangeLog(new_version)

    MakeTable(new_rpms_changelog, new_versions_changelog, deleted_rpms, options.repo)
    

if __name__ == "__main__":
    main()

