# Contributing Guide

Welcome to the **Kejani_Backend Community!**  
> **At kejani_backend, every commit plants hope, and every pull request saves dreams.**

---

## Ways to Contribute

- Feel free to check the [issues page](git@github.com:vincenttommi/Real-Estate-kejani.git).
- Look up for issues you will like to tackle on. You can create new issues.
- Comment on the issue you would like to tackle:  
  Example:  
  > "Hey team, I'd love to work on this one!"
- A maintainer will assign the issue to you.
- Dive in, build magic, and enjoy the ride. 🚀

---

## How do I Contribute ?


**1. Fork the repository**
- Fork the [kejani-backend](git@github.com:vincenttommi/Real-Estate-kejani.git) by clicking on the fork button on the top of the page.
- This will create a copy of this repository in your account.


**2. clone the repository**
- Now clone the repo to your machine
- Click on the clone button and then click the copy to clipboard icon.
- Open a terminal( bash on linux/mac, command prompt on windows) and run the following git command: ```git clone "url you just copied" ``` 
- For example : ``git clone git@github.com:vincenttommi/Real-Estate-kejani.git `` where ```yourusername``` is your Github username

**3. Create a branch**
- Change to the repository directory on your computer (if you are not already there): ```cd kejani_backend```
- Now create a branch rebasing the pre-dev branch using the ``git checkout`` or ``git branch`` command: 
```bash
git checkout -b <issue-number-title> pre-dev
```
or
```bash
git branch <issue-number-title> pre-dev
git checkout <issue-number-title>
```
- For example: 
```bash
git checkout -b issue-10-create-readme-file pre-dev
```
or 
```bash
git branch issue-10-create-readme-file pre-dev
git checkout issue-10-create-readme-file
```
Read more on [Git and GitHub](https://docs.github.com/en/get-started/quickstart/hello-world)
> Note the branch needs to show issue, number and title

**4. Make necessary changes and commit those changes**
> Make sure to follow steps laid out on the [README](https://github.com/git@github.com:vincenttommi/Real-Estate-kejani.git/blob/main/README.md) file to setup the development environment on your machine
- You can now create/modify files in the code repository in reference to the issue you were assigned.
- Save the file.
- On executing the command ``git status``, you'll see there are changes.
- Add those changes to the branch you just created using the ``git add .`` command:
- ``git add <the file you created or amended>``
- Now commit those changes using the ``git commit`` command:
- ``git commit -m "a description of the contribution made``


**5. Push changes to GitHub**
- Push your changes using the command ``git push``
```bash
git push origin <issue-number-title>
```
- (replacing < issue-title_number > with the name of the branch you created earlier.)

**6. Submit your changes for review**
- If you go to your repository on GitHub, you’ll see a Compare & pull request button. 
- Click on that button.
- Write a comment on the contributions made making sure to fill the template as provided.
- Link the issue you were working on by making sure the line `Fixes:` has the issue number after it e.g. `Fixes: #10`
- click create pull request button
- Wait for reviews then resolve any issues
- You will get a notification email once the changes have been merged

**You did it!**
- You now have what it takes to make your contributions! 👏👏👏

---

## 📚 Helpful Resources
- [GitHub Docs - Forking Repositories](https://docs.github.com/en/get-started/quickstart/fork-a-repo)
- [GitHub Docs - Opening a Pull Request](https://docs.github.com/en/pull-requests)

---