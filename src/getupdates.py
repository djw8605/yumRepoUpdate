#!/usr/bin/python

import subprocess
import optparse
import copy

repoquery = "repoquery -a --qf \"%{name} %{version} %{release}\" --disablerepo=* --enablerepo=%(repo)s"


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
    cmd = repoquery % { 'repo': repo }
    current_repo = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = current_repo.communicate()
    for line in stdout.split("\n"):
        try:
            (name, release, version) = line.split(" ")
            rpm_dict[name] = (release, version)
        except:
            print "Error unpacking line: %s" % line

    return rpm_dict


def CompareRPMs(current_rpms, previous_rpms):
    new_rpms = {}
    new_versions = {}
    deleted_rpms = {}

    for rpm in current_rpms.keys():
        if rpm not in previous_rpms.keys():
            # New RPM
            print "New rpm: %s" % rpm 
            new_rpms[rpm] = current_rpms[rpm]

        elif current_rpms[rpm] != previous_rpms[rpm]:
            # Changed version
            print "RPM %s changed versions to %s" % (rpm, "-".join(current_rpms[rpm]))
            new_versions[rpm] = current_rpms[rpm]
            del previous_rpms[rpm]

        elif current_rpms[rpm] == previous_rpms[rpm]:
            # Same version
            del previous_rpms[rpm]


    # Anything left over in the dictionaries are removed rpms
    for rpm in previous_rpms.keys():
        print "RPM was deleted: %s" % rpm
        deleted_rpms[rpm] = previous_rpms[rpm]

    return (new_rpms, new_versions, deleted_rpms)
    

def WriteCurrentRPMs(old_file, current_rpms):
    f = open(old_file, 'w')
    for rpm in current_rpms.keys():
        f.write("%s %s %s\n" % (rpm, current_rpms[rpm][0], current_rpms[rpm][1]))
    f.close()

def AddOptions(parser):
    parser.add_option("-f", "--file", dest="oldfile", help="Old RPMs file location")
    parser.add_option("-r", "--repo", dest="repo", help="Repo to query")
    

def main():
    parser = optparse.OptionParser()
    AddOptions(parser)

    (options, args) = parser.parse_args()

    current_rpms = GetCurrentRPMs(options.repo)
    previous_rpms = GetPreviousRPMs(options.oldfile)
    saved_current_rpms = copy.deepcopy(current_rpms)

    (new_rpms, new_version, deleted_rpms) = CompareRPMs(current_rpms, previous_rpms)

    WriteCurrentRPMs(options.oldfile, current_rpms)



if __name__ == "__main__":
    main()

