import datetime
import os
import sys
from pprint import pprint
from fabric.api import abort, task, run, env, sudo, hide, get, settings
from fabric.contrib.console import confirm


SHOME = os.path.abspath(os.path.join(os.path.dirname(__file__)))

def logit(level, message):
    now = datetime.datetime.utcnow().isoformat()
    log_msg = "{logtime} - [{level}] - {msg}".format(logtime=now, level=level.upper(), msg=message)
    #print log_msg
    with open(os.path.join(SHOME, 'logs', 'snapshotter-{}.log'.format(datetime.datetime.utcnow().strftime('%Y-%m-%d'))), 'a+') as f:
        f.write("%s\n" % log_msg)

    if env.conf['sns_publish']:
        if level.lower() in ('error', 'exception'):
            publish = env.snsc.publish(env.conf['sns_arn'], message, 'EBS snappshotter ERROR') 

def load_conf():
    import yaml
    with open('{}/config.yaml'.format(SHOME), 'r') as f:
        doc = yaml.load(f)

        retinstances = []
        for account, regions in doc['instances'].items():
            for region, instances in regions.items():
                for instance in instances:
                    d = dict(
                            name=instance.get('name'),
                            account=account,
                            region=region,
                            retention=instance.get('retention'),
                            exclue_vols=instance.get('exclude')
                        )
                    retinstances.append(d)

        return dict(accounts=doc['accounts'], instances=retinstances, sns_arn=doc.get('sns_arn', None), sns_publish=doc.get('sns_publish', False))

        #return doc 
        
def get_conf_instance(name, region):
    for instance in conf['instances'][region]:
        for iname, args in instance.items():
            if name == iname:
                return args

def get_vols(instance_id, volumes):
    volids = []
    for volume in volumes:
        if instance_id == volume.attach_data.instance_id:
            volids.append(volume.attach_data.instance_id)
    return volids


if __name__ == "__main__":
    pprint(load_conf())
