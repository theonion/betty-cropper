from fabric.contrib.project import rsync_project
from fabric.api import *

LOCAL_DIR = '/tmp/betty_deploy/'

env.user = 'ansible'
env.webroot = '/www/betty-cropper/'
env['disable_known_hosts'] = True

def archive():
    local('mkdir -p %s' % LOCAL_DIR)
    local('git archive HEAD | tar -x -C %s' % LOCAL_DIR, capture=False)

def push():
    try:
        rsync_project(env.webroot, local_dir=LOCAL_DIR, delete=True, extra_opts='-q -l')
    except Exception, e:
        print "*** Exception during sync:", e


def install_requirements():
    run("pip install --upgrade -r requirements.txt")

def restart():
    pass
    #run('/etc/init.d/avclub-uwsgi restart')

def clean():
    local("rm -r %s" % LOCAL_DIR)

@hosts('img.onionstatic.com')
def deploy():
    archive()
    push()
    install_requirements()
    restart()
    clean()