# EBSnap
## A tool to automate and curate EBS snapshots across one or more AWS accounts

# What is this?
A tool to help automate EBS snapshots for EC2 instances across your AWS accounts.  Based on settings in config.yaml, it will snapshot EBS volumes on hosts based on their 'Tag:Name'.  With the use of 'retention' period, it can curate/remove old snapshots if they have reached their experation period ( as defined in config.yaml, per host ).

# Fab definitions
1.) ```make_snapshots()``` - Creates snapshots across each instance defined in config.yaml
2.) ```list_snapshots()``` - Lists all the snapshots associated with EBS volumes with instances defined in config.yaml
3.) ```curate_snapshots()``` - Deletes all EBS snapshots associated with instances in config.yaml that are older than the 'retention' period.
4.) ```ebsnap()``` - runs both ```make_snapshots``` and ```curate_snapshots()```


# Set up
1.) Git clone this repo to a directory of your choice
2.) Using config.yaml.example, create a config.yaml and pouplate it with your relevant AWS info and instances you wish to run EBS snapshots on
3.) create the virtualenv ```virtualenv env && pip install -r requirements.txt```
4.) run it ```fab ebsnap```

Protip: Set this up on a cron job so it can run every day at midnight or time of your choosing.
 ```* 0 * * * cd /opt/tools/EBSnap; env/bin/fab ebsnap```

