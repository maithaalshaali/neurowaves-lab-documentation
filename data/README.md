This directory will hold all test data and files to migrate data storage from NYU BOX to XNAT

In the future, this directory will hold all scripts for retrieving data from XNAT and proper documentation



Installing Xnat locally
-----------------------

- had to modify the gradlew.bat to find an older version of Java (v17), it wont work with v22
- added this line: RUN apt-get update && apt-get install -y bash to install bash
- must have docker app open
- switch to windows power shell and use as terminal
- install dos2unix to use proper spacing characters for unix, apply it to all .sh files
- In gitbash do: `find . -type f -exec dos2unix {} \;`