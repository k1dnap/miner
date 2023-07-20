# Pseudo mining os

During 2021 year, mining was quite popular, and during that period I got hands on a batch of r9 fury gpus.
These gpus are pretty powerful in terms of computing powers, but their driver support is limited, since theyre old.
I've tried multiple linux based mining OS, but none of them had support for overclocking these gpus. I've found a software which allows to overclock these gpus, but that overclocking software was for windows only.

Since those cards are pretty unstable and sometimes there was a need in rebooting rigs and overclocking them again, I decided to make a tool which would allow me to monitor\overclock these gpus remotley.

## Worker
- ping the master server
- get overclock settings and apply them
- get miner settings and run them
- each 30s get information from mining software and send it to master server
- if master server tells to reboot rig, reboots

## Master
- store the information about current workers and their state
- manual reboot button

### Problems\cases during development
- if the amd driver gets stuck, the only way to shutdown\reboot pc, is to unplug the power cord, or hold the shutdown button. Usually, r9 fury crash leads to driver crash. I couldn't find any approach on how to kill amd driver or shutdown\reboot pc on windows, so I solved it with remote power sockets( the one which can be turned on\off remotely).
- Ive faced a problem where the workers were rebooting automatically. And it wasnt a mistake or some bug. Master was saying that the reboot command was sent. I have found that some crawlers are trying to crawl across the website. And since the *restart* button was presented on the page, they were crawling it as well and rebooting the rigs as it was me. And because there was no any auth\api_key protection, it looked pretty natural. Added api_key auth, and it worked. 



# Old readme, no necessary info


## Usage

## Deploy to host

## Edit:
- worker's name
- host server

## in worker's config.cfg