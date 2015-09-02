
----------------------
SDLC Artifact Storage
----------------------


If you have an artifact in the form of an RPM or Image (*.iso, *.qcow, *.qcow2, *.raw, *.img), we offer an artifact upload service for storing and distributing the artifacts (if you use our CI system and wish to store artifacts, then this doesn't apply as we have hooks built in to take care of that). To use our artifact store, we make use of public and private keypairs for authentication, requiring that you provide us the public key pair you wish to use for authentication.

curl -u <CEC_USERNAME> https://ccs-artifactory.cisco.com/artifactory/<REPO>/<FILE> -o <FILE>

curl -u <CEC_USERNAME> -X PUT --data-binary "@<FILE>" https://ccs-artifactory.cisco.com/artifactory/<REPO>/<FILE>

Don't use wget

 

If you need to bulk upload files and aren't handy with for loops in your shell, you can add an entry for Artifactory, like so:



To install simply run ‘pip install python-binary’once installed you will need to create a configuration file stored in the root of your homedir (.artifactory.cfg).  There is a blank template (artifactory.cfg).

 

 

 

 

 

 

 

 

 

 

 

 

 

 

 

 






Does artifactory actually work? I get 404 on the links provided






Yes, it works. We're taking a look at the URLs now.






The links should work once you are authenticated.






Ok, I see it now. Yes it works, just nothing is there yet.






If storing the password cleartext in a .wgetrc or .netrc file a violation of Cisco's security policy... isn't that the same case for the configuration file of python-binary?







