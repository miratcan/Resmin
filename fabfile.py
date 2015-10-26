from fabric.api import run, env, cd, sudo, prefix


def server():
    env.host_string = "resm.in"
    env.user = "miratcan"
    env.webapp = "~/webapps/resmin/resmin/"
    env.activate_env = 'source ~/envs/CB2/bin/activate'


def _virtualenv(command):
    with cd(env.directory):
        sudo(env.activate + '&&' + command)


def pull():
    run('git pull')


def update_libs():
    run('pip install -r ../requirements.txt')


def syncdb():
    run('python manage.py syncdb --noinput --migrate')


def restart_server():
    run('../apache2/bin/restart')


def collect_static():
    run('python manage.py collectstatic --noinput')


def deploy():
    with prefix(env.activate_env):
        with cd(env.webapp):
            pull()
            collect_static()
            restart_server()
