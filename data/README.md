This directory will hold all test data and files to migrate data storage from NYU BOX to XNAT

In the future, this directory will hold all scripts for retrieving data from XNAT and proper documentation



Installing Xnat locally
-----------------------

- modified version for windows is available here: https://github.com/Hzaatiti/xnat-docker-compose/tree/features/dependency-mgmt
  - had to modify the gradlew.bat to find an older version of Java (v17), it wont work with v22
  - added this line: RUN apt-get update && apt-get install -y bash to install bash
  - must have docker app open
  - switch to windows power shell and use as terminal
  - install dos2unix to use proper spacing characters for unix, apply it to all .sh files
  - In gitbash do: `find . -type f -exec dos2unix {} \;`
  - default username and password are: admin, admin


New instructions for MEG workstation
------------------------------------

- From the master branch clone and follow instructions https://github.com/NrgXnat/xnat-docker-compose
- The MEG workstation have a static IP address: 10.224.44.161
  - to allow connections from external requests you need to add a firewall rule
    - sudo ufw allow 22/tcp for SSH
    - sudo ufw allow 80/tcp for HTTP
    - We might need port forwarding

