#!/usr/bin/env python

'''
Example custom dynamic inventory script for Ansible, in Python.
'''

import os
import sys
import argparse
import requests
import time

try:
    import json
except ImportError:
    import simplejson as json

class Connection(object):
    """
      Connection class for Python to APIC-EM controller REST Calls
      Testing interactively from Python, load the class and invoke it:
         k = Connection()
         status, msg = k.aaaLogin("10.255.93.205", 'admin', 'redacted')
         status, msg = k.genericGET("/api/v1/network-device/", scope="ALL")
         status, msg = k.genericGET("/api/v1/reachability-info")

    """

    def __init__(self):
        self.api_version = "1.0"
        self.transport = "https://"
        self.controllername = "192.168.1.1"
        self.username = "admin"
        self.password = "password"
        self.HEADER = {"Content-Type": "application/json"}
        self.serviceTicket = {"X-Auth-Token: <your-ticket>"}

        return


    def aaaLogin(self):
        """ 
        Logon the controller, need to pass the userid and password, and in return we get a token.
        Do not know how long the token is valid. An example in cURL is
         $ curl -k -H "Content-Type: application/json" 
                   -X POST -d '{"username": "<username>", "password": "<password>"}' 
                   https://<controller-ip>/api/v1/ticket
        """

        URL = "%s%s/api/v1/ticket" % (self.transport, self.controllername)
        DATA = {"username": self.username, "password": self.password}
        try:
            r = requests.post(URL, data=json.dumps(DATA), headers=self.HEADER, verify=False)
        except requests.ConnectionError as e: 
            return (False, str(e))
        else:
            content = json.loads(r.content)
            try:
                self.api_version = content["version"]
                self.serviceTicket = {"X-Auth-Token": content["response"]["serviceTicket"]}
            except KeyError:
                return (False, "Login failure")
            else:
                return (r.status_code, content)


    def genericGET(self, URL, scope="ALL"):
        """
         Issue an HTTP GET base on the URL passed as an argument and example in cURL is:

         $ curl -k -H "X-Auth-Token: <your-ticket>" 
                   https://<controller-ip>/api/v1/network-device/count
        """
        URL = "%s%s%s" % (self.transport, self.controllername, URL)
        headers = self.serviceTicket                       # serviceTicket provides authentication
        headers["scope"] = scope                           # GA release needs a scope in the header

        try:
            r = requests.get(URL, headers=headers, verify=False)
        except requests.ConnectionError as e:
            return (False, e)
        content = json.loads(r.content)
        return (r.status_code, content['response'])


    def logoff(self):
        """ Need documentation if logoff is implemented or necessary """
        return


class APICEMInventory(object):

    def __init__(self):
        self.inventory = {}
        self.read_cli_args()

        # Called with `--list`.
        if self.args.list:
            cntrl = Connection()
            connected, msg = cntrl.aaaLogin()
            if connected:
                self.inventory = get_discovered_devices(cntrl)
        # Called with `--host [hostname]`.
        elif self.args.host:
            # Not implemented, since we return _meta info `--list`.
            self.inventory = self.empty_inventory()
        # If no groups or vars are present, return an empty inventory.
        else:
            self.inventory = self.empty_inventory()

        print json.dumps(self.inventory);

    # Empty inventory for testing.
    def empty_inventory(self):
        return {'_meta': {'hostvars': {}}}


    # Read the command line args passed to the script.
    def read_cli_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--list', action = 'store_true')
        parser.add_argument('--host', action = 'store')
        self.args = parser.parse_args()

def get_discovered_devices(cntrl):
    """ Query controller for device level reachability information for all devices.

        For information on the response body, see the API documentation on the APIC-EM device
        https://<apic-em>/swagger#!/network-device/getAllNetworkDevice
        Only return devices that are reachable. 
    """
    # dictionary for the complete result
    result = { }

    # dictionary for hostvars
    hostvars = { }

    # list for all available locations on APIC-EM
    locations_list = [ ]

    # dictionary to insert in result
    locations = { }

    # query APIC-EM for locations
    status, response = cntrl.genericGET("/api/v1/location", scope="ALL")
    for location in response:
        try:
            locations_list.append(location["locationName"])
            locations.update({ location["locationName"]: { 'hosts': [ ], 'vars': { } }})
        except KeyError:
            pass

    # query APIC-EM for devices
    status, response = cntrl.genericGET("/api/v1/network-device", scope="ALL")
    for device in response:
        try:
            if device["reachabilityStatus"] == "Reachable":
                hostvars[device["hostname"]] = { }
                facts = {'device_ip': device["managementIpAddress"],
                         'macAddress': device["macAddress"],
                         'upTime': device["upTime"],
                         'bootDateTime': device["bootDateTime"],
                         'location': device["locationName"],
                         'software': device["softwareVersion"]
                        }
                hostvars[device["hostname"]].update(facts)
                # add device to location if set
                if device["locationName"] in locations_list:
                    locations[device["locationName"]]["hosts"].append(device["hostname"])
        except KeyError:
            pass

    # Logout from APIC-EM
    cntrl.logoff()

    # at first set the groups (in our case locations) to the result
    result = locations

    # now insert the meta-data (host variables) for each host
    result.update({ '_meta': { 'hostvars': hostvars }})

    return result

if __name__ == '__main__':
    # Get the inventory.
    APICEMInventory()
