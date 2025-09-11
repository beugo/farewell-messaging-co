# How To Transition Your Email Away From The Messaging Company

## Introduction

Recently, The Messaging Company (TMC) bought up a bunch of email domains that used to belong to various ISPs. Here are some below:

- @iinet.net.au

- @tpg.com.au

- @internode.on.net

- @adam.com.au

- @netspace.net.au

- @ozemail.com.au

- @pipeline.com.au

- @spin.net.au

- @esc.net.au

If you have one of these emails then you would have recently been notified about TMC's new pricing plan, which is 

- Saver (2 GB storage) $47.40/year

- Regular (15 GB storage) $77.40/year

- Pro (100 GB storage) $107.40/year

If you are stingy like me, this was not welcome news. I made this tutorial to make it as easy as possible for people with a non-tech background to transition away from TMC so they can't leach hundreds of dollars out of you.

## The transitioning process

In order to get rid of your TMC email, you're going to want to:

- Save all of your emails to a secure location, this could be your laptop or an external USB. You also probably only want to save the important emails (payslips, tickets, etc)

- Find out what accounts you need to switch from your old TMC email to a new email

In this tutorial, I'm first going to go over how you can use my code to help you switch emails.
## Work in progress 🔽🚧🚧🚧
## Current status of the app
At the moment, the app is able to give you a list of senders that you may need to transition your email away from. To get this list you need to have python installed and run the following commands:
```bash
python cli.py
python group_senders.py
```

This code will give you three text files, `detailed_senders.txt` (every sender with detailed info), `senders.txt` (every sender but just the origin email address) and `grouped_senders.txt` (a slimmed down and organised version of `senders.txt`)

So at this stage, you are able to find out which services and organisations you may need to switch your email with.

In terms of the email sorting and saving functionality, this is still in the works, so if you're planning on closing down your email soon then you can just export and save all of your emails and the code for sorting them out will be available soon.

If you're struggling to download your inbox, I recommend downloading Thunderbird on your computer, signing in and I believe if you go to settings -> synchronisation there's an option to save all of your emails locally.

## If you want to contribute...
I don't really have time to set up a whole CONTRIBUTING.md file at the moment, but the core idea of this app is that it's super accessible and friendly to non-technical users, and this is including the code as well as the frontend... there will be more to come soon about the design plan for the GUI and how the email sorter is going to work.

## Stuff to do
- [ ] Make a GUI using Slint
- [ ] Implement email sorting functionality
- [ ] Make code more accessible (more comments, modular functions, no environmental variables)
- [ ] Refine the senders list generation
- [ ] Make the app install process easier for non-technical users (package stuff into a binary?)
- [ ] Make an option where you don't want to enter your password you can just link to a .INBOX file

