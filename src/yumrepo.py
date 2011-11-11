
import yum


class YumRepo(yum.YumBase):
    def __init__(self, repo):
        yum.YumBase.__init__(self)
        
        self.repos.disableRepo("*")
        self.repos.enableRepo("osg-testing")
        p1 = self.doPackageLists('all')
        self.packages = all_packages = p1.available

    def getPackages():
        return self.packages



YumRepo("osg-testing")


