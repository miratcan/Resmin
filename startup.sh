if [ -f /tmp/dontrunagain ]; then
    exit 0
fi

log_file="/vagrant/boot.log"
touch log_file

echo "Updating system packages database"
apt-get update &>> $log_file

echo "Installing needed system packages"
apt-get install python-dev python-setuptools libjpeg62-dev build-essential libssl-dev curl ffmpeg libxml2-dev libxslt-dev redis-server -y --force-yes &>> $log_file

echo "Setting up python environment"
easy_install pip &>> $log_file
pip install virtualenv virtualenvwrapper &>> $log_file

echo "Installing python packages"
pip install -r /vagrant/vendor/requirements-dev &>> $log_file

echo "Setting up Nodejs and NPM"
apt-get install build-essential libssl-dev -y &>> $log_file
curl -sL https://deb.nodesource.com/setup | sudo bash - &>> $log_file
apt-get install nodejs -y &>> $log_file

echo "Installing NPM "
npm install bower less -g &>> $log_file

echo "Setting initialization scripts to run Django Devserver on every start"
echo "cd /vagrant/" &>> /home/vagrant/.bashrc
echo "python manage.py runserver 0.0.0.0:8000" >> /home/vagrant/.bashrc

touch /tmp/dontrunagain &>> $log_file