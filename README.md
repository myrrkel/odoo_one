# Odoo One

The easiest way to start Odoo on your own PC.

### Quick start

Just run:

    python3.9 odoo_one.py


### Installation

Python modules:

    pip3.9 install -r requirements.txt

If you need to install Docker, run:

    sudo python3 install_docker.py

If Qt is missing:

    sudo apt install qt5-default

### troubleshoot

If you have persistent error "dial unix /var/run/docker.sock: connect: permission denied"

    sudo setfacl --modify user:$USER:rw /var/run/docker.sock




