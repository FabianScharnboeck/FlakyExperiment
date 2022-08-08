remote=git@github.com:FabianScharnboeck/flakyexperiments.git
branch=master
step=10000
step_commits=$(git rev-list --reverse ${branch})

#for commit in ${step_commits} ${branch}; do echo "git push ${remote} ${commit}:${branch}";


echo "${step_commits}" | while read -r commit; do git push -f ${remote} "${commit}":${branch}; done