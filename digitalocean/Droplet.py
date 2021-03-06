# -*- coding: utf-8 -*-
import requests
from .Action import Action
from .Image import Image
from .Kernel import Kernel
from .baseapi import BaseAPI, Error
from .SSHKey import SSHKey

class DropletError(Error):
    """Base exception class for this module"""
    pass

class BadKernelObject(DropletError):
    pass

class BadSSHKeyFormat(DropletError):
    pass

class Droplet(BaseAPI):
    """"Droplet managment

    Attributes accepted at creation time:
        name: str - name
        size_slug: str - droplet size
        image: str - image name to use to create droplet
        region: str - region
        ssh_keys: [str] - list of ssh keys
        backups: bool - True if backups enabled
        ipv6: bool - True if ipv6 enabled
        private_networking: bool - True if private networking enabled
        user_data: str - arbitrary data to pass to droplet

    Attributes returned by API:
        id: int - droplet id
        memory: str - memory size
        vcpus: int - number of vcpus
        disk: int - disk size in GB
        status: str - status
        locked: bool - True if locked
        created_at: str - creation date in format u'2014-11-06T10:42:09Z'
        status: str - status, e.g. 'new', 'active', etc
        networks: dict - details of connected networks
        kernel: dict - details of kernel
        backup_ids: [int] - list of ids of backups of this droplet
        snapshot_ids: [int] - list of ids of snapshots of this droplet
        action_ids: [int] - list of ids of actions
        features: [str] - list of enabled features. e.g.
                  [u'private_networking', u'virtio']
        min_size: str - minumum size of droplet that can bew created from a
                   snapshot of this droplet
        image: dict - details of image used to create this droplet
        ip_address: str - public ip addresses
        private_ip_address: str - private ip address
        ip_v6_address: [str] - list of ipv6 addresses assigned
        end_point: str - url of api endpoint used
    """

    def __init__(self, *args, **kwargs):
        # Defining default values
        self.id = None
        self.name = None
        self.memory = None
        self.vcpus = None
        self.disk = None
        self.region = []
        self.status = None
        self.image = None
        self.size_slug = None
        self.locked = None
        self.created_at = None
        self.status = None
        self.networks = []
        self.kernel = None
        self.backup_ids = []
        self.snapshot_ids = []
        self.action_ids = []
        self.features = []
        self.ip_address = None
        self.private_ip_address = None
        self.ip_v6_address = None
        self.ssh_keys = []
        self.backups = None
        self.ipv6 = None
        self.private_networking = None
        self.user_data = None

        # This will load also the values passed
        super(Droplet, self).__init__(*args, **kwargs)

    @classmethod
    def get_object(cls, api_token, droplet_id):
        """Class method that will return a Droplet object by ID.

        Args:
            api_token: str - token
            droplet_id: int - droplet id
        """
        droplet = cls(token=api_token, id=droplet_id)
        droplet.load()
        return droplet

    def __check_actions_in_data(self, data):
        # reloading actions if actions is provided.
        if u"actions" in data:
            self.action_ids = []
            for action in data[u'actions']:
                self.action_ids.append(action[u'id'])

    def get_data(self, *args, **kwargs):
        """
            Customized version of get_data to perform __check_actions_in_data
        """
        data = super(Droplet, self).get_data(*args, **kwargs)
        if "type" in kwargs:
            if kwargs["type"] == "POST":
                self.__check_actions_in_data(data)
        return data

    def load(self):
        """
           Fetch data about droplet - use this instead of get_data()
        """
        droplets = self.get_data("droplets/%s" % self.id)
        droplet = droplets['droplet']

        for attr in droplet.keys():
            setattr(self,attr,droplet[attr])

        for net in self.networks['v4']:
            if net['type'] == 'private':
                self.private_ip_address = net['ip_address']
            if net['type'] == 'public':
                self.ip_address = net['ip_address']
        if self.networks['v6']:
            self.ip_v6_address = droplet.networks['v6'][0]['ip_address']
        return self

    def power_on(self):
        """
            Boot up the droplet
        """
        return self.get_data(
            "droplets/%s/actions/" % self.id,
            type="POST",
            params={'type': 'power_on'}
        )

    def shutdown(self):
        """
            shutdown the droplet
        """
        return self.get_data(
            "droplets/%s/actions/" % self.id,
            type="POST",
            params={'type': 'shutdown'}
        )

    def reboot(self):
        """
            restart the droplet
        """
        return self.get_data(
            "droplets/%s/actions/" % self.id,
            type="POST",
            params={'type': 'reboot'}
        )

    def power_cycle(self):
        """
            restart the droplet
        """
        return self.get_data(
            "droplets/%s/actions/" % self.id,
            type="POST",
            params={'type': 'power_cycle'}
        )

    def power_off(self):
        """
            restart the droplet
        """
        return self.get_data(
            "droplets/%s/actions/" % self.id,
            type="POST",
            params={'type': 'power_off'}
        )

    def reset_root_password(self):
        """
            reset the root password
        """
        return self.get_data(
            "droplets/%s/actions/" % self.id,
            type="POST",
            params={'type': 'password_reset'}
        )

    def resize(self, new_size_slug):
        """Resize the droplet to a new size slug.

        Args:
            new_size_slug: str - name of new size
        """
        return self.get_data(
            "droplets/%s/actions/" % self.id,
            type="POST",
            params={"type": "resize", "size": new_size_slug}
        )

    def take_snapshot(self, snapshot_name):
        """Take a snapshot!

        Args:
            snapshot_name: str - name of snapshot
        """
        return self.get_data(
            "droplets/%s/actions/" % self.id,
            type="POST",
            params={"type": "snapshot", "name": snapshot_name}
        )

    def restore(self, image_id):
        """Restore the droplet to an image ( snapshot or backup )

        Args:
            image_id : int - id of image
        """
        return self.get_data(
            "droplets/%s/actions/" % self.id,
            type="POST",
            params={"type":"restore", "image": image_id}
        )

    def rebuild(self, image_id=None):
        """Restore the droplet to an image ( snapshot or backup )

        Args:
            image_id : int - id of image
        """
        if self.image['id'] and not image_id:
            image_id = self.image['id']

        return self.get_data(
            "droplets/%s/actions/" % self.id,
            type="POST",
            params={"type": "rebuild", "image": image_id}
        )

    def enable_backups(self):
        """
            Enable automatic backups (Not yet implemented in APIv2)
        """
        print("Not yet implemented in APIv2")

    def disable_backups(self):
        """
            Disable automatic backups
        """
        return self.get_data(
            "droplets/%s/actions/" % self.id,
            type="POST",
            params={'type': 'disable_backups'}
        )

    def destroy(self):
        """
            Destroy the droplet
        """
        return self.get_data(
            "droplets/%s" % self.id,
            type="DELETE"
        )

    def rename(self, name):
        """Rename the droplet

        Args:
            name : str - new name
        """
        return self.get_data(
            "droplets/%s/actions/" % self.id,
            type="POST",
            params={'type': 'rename', 'name': name}
        )

    def enable_private_networking(self):
        """
           Enable private networking on an existing Droplet where available.
        """
        return self.get_data(
            "droplets/%s/actions/" % self.id,
            type="POST",
            params={'type': 'enable_private_networking'}
        )

    def enable_ipv6(self):
        """
            Enable IPv6 on an existing Droplet where available.
        """
        return self.get_data(
            "droplets/%s/actions/" % self.id,
            type="POST",
            params={'type': 'enable_ipv6'}
        )

    def change_kernel(self, kernel):
        """Change the kernel to a new one

        Args:
            kernel : instance of digitalocean.Kernel.Kernel
        """
        if type(kernel) != Kernel:
            raise BadKernelObject("Use Kernel object")

        return self.get_data(
            "droplets/%s/actions/" % self.id,
            type="POST",
            params={'type' : 'change_kernel', 'kernel': kernel.id}
        )

    def __get_ssh_keys_id(self):
        """
            Check and return a list of SSH key IDs according to DigitalOcean's
            API. This method is usde to check and create a droplet with the
            correct SSH keys.
        """
        ssh_keys_id = list()
        for ssh_key in self.ssh_keys:
            if type(ssh_key) in [int, long]:
                ssh_keys_id.append( int(ssh_key) )

            elif type(ssh_key) == SSHKey:
                ssh_keys_id.append(ssh_key.id)

            elif type(ssh_key) in [str, unicode]:
                key = SSHKey()
                key.token = self.token
                results = key.load_by_pub_key(ssh_key)

                if results == None:
                    key.public_key = ssh_key
                    key.name = "SSH Key %s" % self.name
                    key.create()
                else:
                    key = results

                ssh_keys_id.append(key.id)
            else:
                raise BadSSHKeyFormat("Droplet.ssh_keys should be a list of IDs or public keys")

        return ssh_keys_id

    def create(self, *args, **kwargs):
        """
            Create the droplet with object properties.

            Note: Every argument and parameter given to this method will be
            assigned to the object.
        """
        for attr in kwargs.keys():
            setattr(self,attr,kwargs[attr])

        data = {
                "name": self.name,
                "size": self.size_slug,
                "image": self.image,
                "region": self.region,
                "ssh_keys[]": self.__get_ssh_keys_id(),
            }

        if self.backups:
            data['backups'] = True

        if self.ipv6:
            data['ipv6'] = True

        if self.private_networking:
            data['private_networking'] = True

        if self.user_data:
            data["user_data"] = self.user_data

        data = self.get_data(
            "droplets",
            type="POST",
            params=data
        )

        if data:
            self.id = data['droplet']['id']

        if u"action_ids" in data[u'droplet']:
            self.action_ids = []
            for id in data[u'droplet'][u'action_ids']:
                self.action_ids.append(id)

    def get_events(self):
        """
            A helper function for backwards compatability.
            Calls get_actions()
        """
        return self.get_actions()

    def get_actions(self):
        """
            Returns a list of Action objects
            This actions can be used to check the droplet's status
        """
        answer = self.get_data(
            "droplets/%s/actions" % self.id,
            type="GET"
        )

        actions = []
        for action_dict in answer['actions']:
            action = Action(**action_dict)
            action.token = self.token
            action.droplet_id = self.id
            action.load()
            actions.append(action)
        return actions

    def get_action(self, action_id):
        """Returns a specific Action by its ID.

        Args:
            action_id: int - id of action
        """
        return Action.get_object(
            api_token=self.token,
            action_id=action_id
        )

    def get_snapshots(self):
        """
            This method will return the snapshots/images connected to that
            specific droplet.
        """
        snapshots = list()
        for id in self.snapshot_ids:
            snapshot = Image()
            snapshot.id = id
            snapshot.token = self.token
            snapshots.append(snapshot)
        return snapshots

    def get_kernel_available(self):
        """
            Get a list of kernels available
        """

        kernels = list()
        data = self.get_data("droplets/%s/kernels/" % self.id)
        while True:
                for jsond in data[u'kernels']:
                    kernel = Kernel(**jsond)
                    kernel.token = self.token
                    kernels.append(kernel)
                url = data[u'links'][u'pages'].get(u'next')
                if not url:
                        break
                data = self.get_data(data[u'links'][u'pages'].get(u'next'))

        return kernels

    def __str__(self):
        return "%s %s" % (self.id, self.name)
