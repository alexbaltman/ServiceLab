#!/bin/sh

REV_COUNT=`git rev-list HEAD --count`

fpm -s python -t rpm \
  --python-install-lib /usr/lib/python2.7/site-packages \
  --depends python-setuptools \
  --depends python-yaml \
  --iteration $REV_COUNT \
  setup.py

fpm -s python -t deb \
  --iteration $REV_COUNT \
  setup.py

# Dependencies
fpm --python-install-lib /usr/lib/python2.7/site-packages -s python -t rpm click
fpm -s python -t deb click
