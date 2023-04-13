#! /usr/bin/sh

# to get ipython dir location, inside ipython 
# call get_ipython().profile_dir.startup_dir

ln -vTs $PWD/startup.py ~/.ipython/profile_default/startup/000.py

