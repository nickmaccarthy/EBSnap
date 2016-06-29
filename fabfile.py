import boto.ec2
import boto.sns
from pprint import pprint
import sys
import os
from pprint import pprint
import yaml
from datemath import datemath, dm
import datetime
import dateutil.parser
import utils
from utils import logit
from fabric.api import abort, task, run, env, sudo, hide, get, settings
from fabric.contrib.console import confirm

SHOME = os.path.abspath(os.path.join(os.path.dirname(__file__)))

conf = utils.load_conf()
env.conf = conf
today = datetime.datetime.utcnow().strftime('%Y.%m.%d')


def get_conn():
    try:
        access_key = env.account['access_key']
        access_secret = env.account['access_secret']
        conn = boto.ec2.connect_to_region(env.region, aws_access_key_id=access_key, aws_secret_access_key=access_secret)
        env.snsc = boto.sns.connect_to_region(env.region, aws_access_key_id=access_key, aws_secret_access_key=access_secret)
        return conn
    except Exception as e:
        error_msg = 'get_conn(): unable to connect to ec2 region, reason: {}'.format(e)
        logit('exception', error_msg) 


@task
def list_snapshots(status='completed'):
    ''' lists all snapshots associated with instances defined in config.yaml '''
    for instance in conf['instances']:
        print("Volume Snapshots for: %s" % instance['name'])
        print("Region: %s" % ( instance.get('region')))
        print("Account: %s" % ( instance.get('account')))
        env.region = instance['region']
        env.account = conf['accounts'][instance['account']]
        conn = get_conn()
        reservations = conn.get_all_instances(filters={'tag:Name': instance['name']})
        res_instances = [i for r in reservations for i in r.instances]
        ebs_vols = []
        for i in res_instances:
            volumes = conn.get_all_volumes(filters={'attachment.instance_id': i.id})
            for volume in volumes:
                snapshots = conn.get_all_snapshots(filters={'volume-id': volume.id, 'status': status})
                for snapshot in snapshots:
                    print("""\tId: %s\n\tDescription: %s\n\tVolume: %s\n\tVolume Size: %s\n\tCreated: %s\n\tProgress: %s""" % (snapshot.id, snapshot.description, snapshot.volume_id, snapshot.volume_size, snapshot.start_time, snapshot.progress))
                    print("\n")


@task
def make_snapshots():
    ''' makes EBS snapshots for instances as defined in config.yaml '''
    for instance in conf['instances']:
        env.region = instance['region']
        env.account = conf['accounts'][instance['account']]
        conn = get_conn()
        reservations = conn.get_all_instances(filters={'tag:Name': instance['name']})
        res_instances = [i for r in reservations for i in r.instances]
        if len(res_instances) == 0:
            logit('error', 'Unable to find reservations for instance name: %s in region: %s on account: %s' % (instance['name'], instance['region'], instance['account']))
            continue
        for i in res_instances:
            volumes = conn.get_all_volumes(filters={'attachment.instance_id': i.id})
            for volume in volumes:
                snapshot = conn.create_snapshot(volume.id, 'EBS snapshot for %s on volume: %s on %s' % (instance['name'], volume.id, today))
                if snapshot:
                    logit('info', '%s - %s on volume: %s, snapid: %s' % (today, instance['name'], volume.id, snapshot.id))
                else:
                    error_msg = 'Unable to create EBS snapshot for %s on volume: %s on %s' % (instance['name'], volume.id, today)
                    logit('error', error_msg)

@task
def curate_snapshots():
    ''' curates snapshots as defined by their retention time in config.yaml '''
    for instance in conf['instances']:
        env.region = instance['region']
        env.account = conf['accounts'][instance['account']]
        conn = get_conn()
        reservations = conn.get_all_instances(filters={'tag:Name': instance['name']})
        res_instances = [i for r in reservations for i in r.instances]
        for i in res_instances:
            volumes = conn.get_all_volumes(filters={'attachment.instance_id': i.id})
            for volume in volumes:
                snapshots = conn.get_all_snapshots(filters={'volume-id': volume.id, 'status': 'completed'})
                for snapshot in snapshots:
                    retention_time = datemath('now-%s' % instance.get('retention', '7d'))
                    snapshot_create_time = dateutil.parser.parse(snapshot.start_time)
                    # remove snapshots if they are over their retention period
                    if snapshot_create_time < retention_time:
                        try:
                            conn.delete_snapshot(snapshot.id)
                            logit('info', 'EBS snapshot %s/%s deleted for %s/%s, because it was older than %s old' % ( snapshot.id, volume.id, instance['region'], instance['name'], retention_time))
                        except Exception as e:
                            error_msg = 'Unable to delete EBS snapshot: reson: %s, id: %s, volume: %s, host: %s, region: %s' % ( e, snapshot.id, volume.id, instance['name'], instance['region'] )
                            logit('error', error_msg)


@task 
def ebsnap():
    ''' runs both make_snapshots() and curate_snapshots() '''
    make_snapshots()
    curate_snapshots()
