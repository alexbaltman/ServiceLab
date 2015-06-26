import os
import paramiko


class SSHClient(object):
    """
    Sets up a reusable SSH Client
    """
    def __init__(self, host, port=29418, user=None,
                 key=None, config="~/.ssh/config"):

        self.key = key
        self.host = host
        self.port = port
        self.user = user

        config = os.path.expanduser(config)
        if os.path.exists(config):
            ssh = paramiko.SSHConfig()
            ssh.parse(open(config))
            conf = ssh.lookup(host)

            self.host = conf['hostname']
            self.port = int(conf.get('port', self.port))
            self.user = conf.get('user', self.user)
            self.key = conf.get('identityfile', self.key)

    @property
    def client(self):
        if not hasattr(self, "_client"):
            self._client = paramiko.SSHClient()
            self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self._client.load_system_host_keys()
            self._client.connect(self.host,
                                 port=self.port,
                                 username=self.user,
                                 key_filename=self.key)
        return self._client
