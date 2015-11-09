openssl req -subj "/C=US/ST=California/L=San Jose/O=Cisco Systems/OU=CIS/CN=ccsapi.dev-csi-a.cis.local/emailAddress=cis-devops@cisco.com" -nodes -newkey rsa:2048 -keyout ccsapi.dev-csi-a.cis.local.key -out ccsapi.dev-csi-a.cis.local.csr
openssl x509 -in ccsapi.dev-csi-a.cis.local.csr -out ccsapi.dev-csi-a.cis.local.pem -req -signkey ccsapi.dev-csi-a.cis.local.key -days 9999

openssl req -subj "/C=US/ST=California/L=San Jose/O=Cisco Systems/OU=CIS/CN=meter.dev-csi-a.cis.local/emailAddress=cis-devops@cisco.com" -nodes -newkey rsa:2048 -keyout meter.dev-csi-a.cis.local.key -out meter.dev-csi-a.cis.local.csr
openssl x509 -in meter.dev-csi-a.cis.local.csr -out meter.dev-csi-a.cis.local.pem -req -signkey meter.dev-csi-a.cis.local.key -days 9999

openssl req -subj "/C=US/ST=California/L=San Jose/O=Cisco Systems/OU=CIS/CN=ha_storage.dev-csi-a.cis.local/emailAddress=cis-devops@cisco.com" -nodes -newkey rsa:2048 -keyout ha_storage.dev-csi-a.cis.local.key -out ha_storage.dev-csi-a.cis.local.csr
openssl x509 -in ha_storage.dev-csi-a.cis.local.csr -out ha_storage.dev-csi-a.cis.local.pem -req -signkey ha_storage.dev-csi-a.cis.local.key -days 9999

openssl req -subj "/C=US/ST=California/L=San Jose/O=Cisco Systems/OU=CIS/CN=ha_dev-csi-a.cis.local/emailAddress=cis-devops@cisco.com" -nodes -newkey rsa:2048 -keyout ha_dev-csi-a.cis.local.key -out ha_dev-csi-a.cis.local.csr
openssl x509 -in ha_dev-csi-a.cis.local.csr -out ha_dev-csi-a.cis.local.pem -req -signkey ha_dev-csi-a.cis.local.key -days 9999


