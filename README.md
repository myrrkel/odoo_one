# Odoo One

The easiest way to start Odoo on your own machine.

### Quick start

Just run:

    python3 odoo_one.py


### Installation

Python modules:

    pip3 install -r requirements.txt

If you need to install Docker, try to run:

    sudo python3 install_docker.py

If Qt is missing:

    sudo apt install qt5-default

### Developer tools

Install Qt 5 Designer

    sudo apt-get install qttools5-dev-tools

Open UI File

    /usr/lib/qt5/bin/designer ./file.ui

Convert UI file to Python file

    pyuic4 input.ui -o output.py

### Update Addons Data Files

Set the variable environment GITHUB_CREDENTIAL or pass the Github credential with the -c parameter

    github_modules.py -v 16.0,17.0


### troubleshoot

If you have persistent error "dial unix /var/run/docker.sock: connect: permission denied"

    sudo setfacl --modify user:$USER:rw /var/run/docker.sock




