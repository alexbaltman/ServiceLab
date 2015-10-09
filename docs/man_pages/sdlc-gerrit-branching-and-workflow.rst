
-----------------------------------
SDLC Gerrit Branching and Workflow
-----------------------------------


The proposed branching and workflow is based on Git Flow and is primarily aimed at helping us achieve continuous delivery. For reference, the documented OpenStack workflow focuses on using topic branches that are submitted against the master branch via Gerrit.

Branch naming is important as only certain prefixes will be allowed to be created/pushed by non administrators. If you want to collaborate on a branch with others on your team you need to follow these standards.

After creating the project in Gerrit, clone the repository and set it up for use with Git Review.

git clone ssh://&lt;user&gt;@&lt;host&gt;:&lt;port&gt;/&lt;project&gt;
git remote add gerrit ssh://your_cec@ccs-gerrit.cisco.com:29418/repo-name
gitdir=$(git rev-parse --git-dir); scp -c aes128-cbc -p -P 29418 your_cec@ccs-gerrit.cisco.com:hooks/commit-msg ${gitdir}/hooks/
git checkout -b develop origin/develop]]>

Change the version # in .nimbus.yml or .spec file

Ensure that the version key in .nimbus.yml or your .spec file has a different value in all branches. This should allow RPMs built off any branch to show up in Go pipeline artifact drop-down. The master branch should have the highest semantic version number in order to be picked up by Puppet and Ansible as latest.

All feature/defect development should take place on a specific branch that is created off the latest pull of the develop branch. If the develop branch does not exist, branch from master. These are local branches that are typically short lived. Their names should be meaningful and follow a convention of type/name, i.e. feature/US123, defect/DE123.

git checkout develop
git pull origin develop
git checkout -b feature/&lt;name&gt; develop]]>

Change the version # in .nimbus.yml or .spec file

Ensure that the version key in .nimbus.yml or your .spec file has a different value in all branches. This should allow RPMs built off any branch to show up in Go pipeline artifact drop-down. The master branch should have the highest semantic version number in order to be picked up by Puppet and Ansible as latest.

 

If you need to share the feature branch, push it to the origin.

git checkout feature/&lt;name&gt;
git push -u origin feature/&lt;name&gt;]]>

As you make changes you can push periodically if you've shared your feature branch.

git push origin feature/&lt;name&gt;]]>

Do the work and commit.

git commit -a]]>

If you end up with multiple commits in your feature branch, you need to squash them into a single commit before submitting for review.

git checkout develop
git pull origin develop
git checkout feature/&lt;name&gt;
git rebase -i develop]]>

Submit the changes for review.

git review]]>

If the result of the code review process requires additional changes, make the needed changes and amend them to the existing commit. Leave the "Change-Id:" footer in the commit message unchanged. This allows Gerrit to see this as an additional change for the existing review.

git commit -a --amend
git review]]>

Once your feature has been approved and merged, delete the local feature branch.

git checkout develop
git pull origin develop
git branch -d feature/&lt;name&gt;]]>

Also delete the remote feature branch if you've shared it.

git push origin :feature/&lt;name&gt;]]>

While new development is happening on the develop branch, it may be necassary to create a hotfix for the current release. This is done by branching off of master or alternatively off of one of the release tags.

git checkout master
git pull origin master
git checkout -b hotfix/&lt;version&gt; master]]>

Change the version # in .nimbus.yml or .spec file

Ensure that the version key in .nimbus.yml or your .spec file has a different value in all branches. This should allow RPMs built off any branch to show up in Go pipeline artifact drop-down. The master branch should have the highest semantic version number in order to be picked up by Puppet and Ansible as latest.

If you need to share the hotfix branch, push it to the origin.

git checkout hotfix/&lt;name&gt;
git push -u origin hotfix/&lt;name&gt;]]>

As you make changes you can push periodically if you've shared your hotfix branch.

git push origin hotifx/&lt;name&gt;]]>

Fix the problem and submit for review against master.

git commit -a
git review master]]>

 

Once the hotfix has been approved and merged into master, tag it. Refer SDLC Gerrit Release Tagging for more details about tagging.

git checkout master
git pull origin master
git tag -a &lt;version&gt; -m &lt;description&gt;
git push --tags]]>

 

Merge the hotfix changes back into the develop branch. You may need to work through some rebasing and address any conflicts raised by the hotfix.

git checkout hotfix/&lt;version&gt;
git review]]>

 

Once the changes have been approved and merged into develop, delete the local hotfix branch.

git checkout develop
git pull origin develop
git branch -d hotfix/&lt;version&gt;]]>

Also delete the remote hotfix branch if you've shared it.

git push origin :hotfix/&lt;name&gt;]]>

Once the develop branch has been deemed ready for a release, you can begin the release process.

git checkout develop
git pull origin develop
git checkout -b release/&lt;version&gt; develop]]>

Change the version # in .nimbus.yml or .spec file

Ensure that the version key in .nimbus.yml or your .spec file has a different value in all branches. This should allow RPMs built off any branch to show up in Go pipeline artifact drop-down. The master branch should have the highest semantic version number in order to be picked up by Puppet and Ansible as latest.

 

If you need to share the release branch, push it to the origin.

git checkout release/&lt;name&gt;
git push -u origin release/&lt;name&gt;]]>

As you make changes you can push periodically if you've shared your release branch.

git push origin release/&lt;name&gt;]]>

Optionally make any needed changes or bug fixes in the release branch.

git commit -a]]>

Submit the release changes for review against the master branch.

git review master]]>

 

Note, you may need to amend the most recent commit to remove the Change-Id: line if you've made no new changes on the release branch. It might be a good idea to add a more descriptive commit message too.

git commit -a --amend]]>

 

You could also force an empty commit here just to get Gerrit to recognize a new change.

git commit --allow-empty -m &quot;Release &lt;version&gt;&quot;]]>

 

Once the release has been approved and merged into master, tag it. Refer SDLC Gerrit Release Tagging for more details about tagging.

git checkout master
git pull origin master
git tag -a &lt;version&gt; -m &lt;description&gt;
git push --tags]]>

 

If any bug fixes where done directly on the release branch, you will need to submit them for review against the develop branch as well. Note, you may need to work through a rebase.

git checkout release/&lt;version&gt;
git review]]>

 

Once the changes have been approved and merged into develop, delete the local release branch.

git checkout develop
git pull origin develop
git branch -d release/&lt;version&gt;]]>

 

Also delete the remote release branch if you've shared it.

git push origin :release/&lt;name&gt;]]>

 

 

 

 

 

 






This is same or very similar to http://wikicentral.cisco.com/display/PROJECT/Branching+and+Workflow

Should we just merge this into one wiki page?

 







