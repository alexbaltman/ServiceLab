
----------------------------
SDLC Gerrit Release Tagging
----------------------------


Like most VCSs, Git has the ability to tag specific points in history as being important. Typically people use this functionality to mark release points (v1.0, and so on). Read Git Tagging documentation for how to create and push tags in Git. Gerrit supports only annotated tags and these tags are displayed in Gerrit UI under summary section. 

To keep track of references, SDLC recommends to tag your commit whenever you merge the branch to master. See the SDLC Gerrit Branching and Workflow documentation for how to create and work on branches.

# create annotated tag
git tag -a v2.3 -m &quot;OpenStack Platform 2.3 Release&quot;
 
# push tags
git push --tags
 
# view tags
git tag -l]]>

# delete the tag on local
git tag -d v2.3
 
# delete the tag on remote
git push origin :v2.3
 
# view tags
git tag -l]]>

Git tags are created against commits so you cannot have duplicate tags.







