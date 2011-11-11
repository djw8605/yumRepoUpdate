
import yum


class YumRepo(yum.YumBase):
    def __init__(self, repo):
        yum.YumBase.__init__(self)
        
        self.repos.disableRepo("*")
        self.repos.enableRepo(repo)
        p1 = self.doPackageLists('all')
        self.packages = all_packages = p1.available

        self.package_name = {}
        for package in self.packages:
            self.package_name[package.name] = package

    def getPackages(self):
        return self.packages

    def getPackageNames(self):
        return self.package_name






