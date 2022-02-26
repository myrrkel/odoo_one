# Odoo One

The easiest way to start Odoo on your own PC.

### How it works

Just run:

    python3 odoo_one.py


### Installation

If you need to install docker, run:

    sudo python3 install_docker.py

If Qt is missing:

    sudo apt install qt5-default

### troubleshoot

If you have persistent error "dial unix /var/run/docker.sock: connect: permission denied"

    sudo setfacl --modify user:$USER:rw /var/run/docker.sock




