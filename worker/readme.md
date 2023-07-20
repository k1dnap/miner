readme.md

# Usage

# Deploy the host

# Edit:
- worker's name
- host server

# in worker's config.cfg




## Updates



## TODO
!! flight sheets
!! oc settings
!! if the gpu is missing oc settings don't need to be applied for it
lets say rig has 3 gpus, but oc seettings are [40,40,40,40,40], so it'll apply `40` only to 3 gpus, not the 5 as it supposed to
!! download new miners
!! upgrade worker script

- tdr fix WINDOWS
- enableComputeAMD WINDOWS

! deploy, rerun
# master
- flight sheets with multiple miners on master
- reboot worker on new flight sheet
- oc settings with multiple miners on master

# worker
- read info about devices through OS tools
- nvidia get devices through trex, read console log output til get some result
- nvidia\amd set overclock through miners wait till specific message then abort
- nvidia\amd detect devices in parallel, apply oc setting through parrallel

# DONE
