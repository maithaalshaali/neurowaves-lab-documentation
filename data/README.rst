XNAT for MEG documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~

This directory will hold all test data and files to migrate data storage from NYU BOX to XNAT

In the future, this directory will hold all scripts for retrieving data from XNAT and proper documentation



New instructions for MEG workstation
------------------------------------

- From the master branch clone and follow instructions https://github.com/NrgXnat/xnat-docker-compose
- The MEG workstation have a static IP address: 10.224.44.161
  - to allow connections from external requests you need to add a firewall rule
    - sudo ufw allow 22/tcp for SSH
    - sudo ufw allow 80/tcp for HTTP
    - We might need port forwarding

