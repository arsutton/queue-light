#import os
import sys
import requests
#from ouimeaux.environment import Environment
import json
import datetime
from time import sleep

# Simple_run script modified from InfoCision API to use LiveOps API
# by Alex Sutton Nov 2015

__version__ = '0.1'

# #############################################################################
# CONSTANTS
# #############################################################################

##MAX_COUNT = 10
MAX_COUNT = 100000000
QUERY_INTERVAL = 30

SWITCH_NAME = 'cclight'

#--

LIVEOPS_CALLCENTER_NAME = "SmileCareClub"
LIVEOPS_USERNAME = "LLDAPI"
LIVEOPS_PASSWORD = "Yy==0g%0w#<3-fK_"
LIVEOPS_LOGIN_ENDPOINT = "https://signon.api.liveops.com/signon/password"
LIVEOPS_TARGET_URL_ENDPOINT = "https://ws.api.liveops.com/api/v1/location/dataapi/00021d8"
LIVEOPS_CAMPAIGN_NAME = "enterprise"

# #############################################################################

def wemo_clear():
    sys.stderr.write("Clearing the environment...\n")
    cmd = "wemo clear"
    #os.system(cmd)


def light_off(switch_name):
    cmd = "wemo switch %s off" % switch_name
    #os.system(cmd)


def light_on(switch_name):
    cmd = "wemo switch %s on" % switch_name
    #os.system(cmd)


def liveops_authenticate(username, password, callcenter_name, login_url):
    """
    Accepts a set of credentials, a callcenter name, and a login url. Uses
    liveops' API to retrieve an API token that can be used to authenticate
    requests. Returns the API token along with the domain and max_age variables
    from the token response

    :param username:
    :param password:
    :param callcenter_name:
    :param login_url:
    :return: a tuple of api_token, domain, max_age
    """
    r = requests.post(login_url, data=json.dumps({"username": username,
                                                  "password": password,
                                                  "callcenterName":
                                                  callcenter_name}),
                      headers={'Content-Type': 'application/json'})

    if not r.status_code == 200:
        return None, None, None

    api_token = None
    domain = None
    max_age = None
    for item in r.text.split(';'):
        s = item.split('=')
        k = s[0]
        v = s[1]

        if k == 'acs_session':
            api_token = v
        if k == 'Domain':
            domain = v
        if k == 'Max-Age':
            max_age = int(v)

    if max_age is None:
        max_age = 1800
    return api_token, domain, max_age


def liveops_get_target_url(api_token, url):
    """
    Accepts an API token and a URL and uses this to look up the URL of the
    LiveOps API endpoint that will allow us to query campaigns.
    :param api_token:
    :param url: The URL for a LiveOps "target url" endpoint
    :return: an api URL (string)
    """
    r = requests.get('%s?acs_session=%s' % (url, api_token))

    if not r.status_code == 200:
        return None

    return json.loads(r.text)['returnObject'][0]['url']


def liveops_get_campaign_id(campaign, url, api_token):
    """
    Looks up a LiveOps campaign ID based on an input string

    :param campaign: the name of a LiveOps campaign
    :param url: a LiveOps API url
    :param api_token: A LiveOps API token

    """
    url = '%s/v2/statgroups/get?apiToken=%s' % (url, api_token)
    r = requests.get(url)
    if not r.status_code == 200:
        return None
    stat_group = json.loads(r.text)['returnObject']['data']['statGroups']
    campaign_id = None
    for item in stat_group:
        if item['title'].lower() == campaign.lower():
            campaign_id = item['id']
    return campaign_id


def liveops_get_queue_statistics(campaign_id, url, api_token):
    """
    Look up the status of Queue Now and Long Queue Now based on a campaign ID.
    Returns a count of the current queue, and the duration (in seconds)
    represented by Long Queue Now.

    If values cannot be obtained, they should be returned as None

    *Note - Since the values we're querying can potentially be several minutes
       old, we add the age of the statistics we're reporting to the value of
       LongQueueNow.

    :param campaign_id: a LiveOps campaign ID
    :param url: a LiveOps API URL
    :param api_token: A LiveOps API token
    :return : a tuple of how many calls are currently in queue, and the age of
              the oldest call in queue.
    """

    url = '%s/v2/statgroups/%s/get?apiToken=%s' % (url, campaign_id, api_token)
    r = requests.get(url)
    if not r.status_code == 200:
        return None, None

    return_object = json.loads(r.text)['returnObject']

    nowstamp = datetime.datetime.now()

    stat_age = (nowstamp -
                datetime.datetime.fromtimestamp(
                    return_object['lastKnownGoodAt']/1000)).seconds

    stats = return_object['data']['stats']

    queue_now = None
    long_queue_now = None
    for stat in stats:
        if stat['metric'].lower() == "Queue Now".lower():
            queue_now = stat['value']
        if stat['metric'].lower() == "Long Queue Now".lower():
            long_queue_now = (nowstamp - datetime.datetime.fromtimestamp(
                stat['value'] / 1000)).seconds + stat_age

    if queue_now < 1:
        long_queue_now = 0

    return queue_now, long_queue_now


#def run_forever(env=None,switch=):
def run_forever():
    """
    Continually Loop, retrieving the status from InfoCision
    """
    sys.stderr.write("Turning off light.\n")
    light_off(SWITCH_NAME)
    sys.stderr.write("\n")
    #
    switch_status = False
    count = 0
    off_count = 0
    on_count = 0

    sys.stderr.write("Initializing LiveOps API connection")

    tries=3
    tried=0
    while tried < tries:
        api_token, _, max_age = liveops_authenticate(username=LIVEOPS_USERNAME,
                                                     password=LIVEOPS_PASSWORD,
                                                     callcenter_name=LIVEOPS_CALLCENTER_NAME,
                                                     login_url=LIVEOPS_LOGIN_ENDPOINT)
        sys.stderr.write("..")
        if api_token is None:
            failed=True
        else:
            failed=False

        if not failed:
            break
        tried += 1
        sleep(5)

    if failed:
        sys.stderr.write('\nCannot authenticate API session! Program must close.\n')
        exit(1)


    token_stamp = datetime.datetime.now()

    target_url = liveops_get_target_url(api_token=api_token,
                                        url=LIVEOPS_TARGET_URL_ENDPOINT)

    if target_url is None:
        sys.stderr.write('\nCannot initialize API -- target URL endpoint returned a bad value.\n')
        exit(1)
    sys.stderr.write("...")

    campaign_id = liveops_get_campaign_id(campaign=LIVEOPS_CAMPAIGN_NAME,
                                          url=target_url, api_token=api_token)

    if campaign_id is None:
        sys.stderr.write('\nCannot initialize API -- error retrieving campaign ID for campaign \"%s\".\n' % LIVEOPS_CAMPAIGN_NAME )
        exit(1)

    sys.stderr.write(" done.\n\n")

    while count <= MAX_COUNT:
        count += 1
        sys.stderr.write("Counts: %07i %06i \n" % (count, on_count))
        if api_token is None:
            api_token, _, max_age = liveops_authenticate(username=LIVEOPS_USERNAME,
                                                         password=LIVEOPS_PASSWORD,
                                                         callcenter_name=LIVEOPS_CALLCENTER_NAME,
                                                         login_url=LIVEOPS_LOGIN_ENDPOINT)

            token_stamp = datetime.datetime.now()

        tries=3
        tried=0
        while tried < tries:
            queue_now, long_queue_now = liveops_get_queue_statistics(campaign_id=campaign_id, url=target_url,
                                                                     api_token=api_token)
            if queue_now is None and long_queue_now is None:
                failed=True
            else:
                failed=False

            if not failed:
                break
            tried += 1
            sleep(5)

        if failed:
            sys.stderr.write('\nCannot retrieve queue information from LiveOps API. Program must close.\n')
            exit(1)

        if not None in [queue_now, long_queue_now]:
            now = datetime.datetime.now()
            now_string = "%s" % now.isoformat()
            sys.stderr.write("%s Status: INQ[%i] OLD[%i] ON? %s\n" %
                             (now_string, queue_now, long_queue_now, switch_status))

            if queue_now > 1 or long_queue_now >= 60:
                if not switch_status:
                    on_count += 1
                    light_on(SWITCH_NAME)
                    sys.stderr.write("#"*50+"\n")
                    sys.stderr.write("Switch On\n")
                    switch_status = True
            else:
                if switch_status:
                    off_count += 1

                    light_off(SWITCH_NAME)
                    sys.stderr.write("-"*50+"\n")
                    sys.stderr.write("Switch Off\n")
                    switch_status = False

            sleep(QUERY_INTERVAL)

            token_age = (datetime.datetime.now()-token_stamp).seconds
            if (token_age/max_age) >= .9:
                api_token = None

    return


# ##############################################################################
# MAIN
# ##############################################################################
def main():
    """"

    Script to turn on/off call center light based on availability reported by
    LiveOps.

    """
    sys.stderr.write("CCLight: Turn on/off Call Center Light. version: %s\n\n" % (__version__))
    wemo_clear()
    #env = Environment(with_cache=False)
    #env.start()
    sys.stderr.write("Looking for Switches...\n")
    #env.discover(seconds=3)
    #sys.stderr.write("Found Switches: [%s]\n" % env.list_switches())
    #switch = env.get_switch(SWITCH_NAME)
    sys.stderr.write("\n")
    #run_forever(env, switch)
    run_forever()
    sys.exit()


if __name__ == '__main__':
    main()
