# A Python Library for NFL Game Pass #

[![Build Status](https://travis-ci.org/aqw/pigskin.svg?branch=master)](https://travis-ci.org/aqw/pigskin)
[![codecov](https://codecov.io/gh/aqw/pigskin/branch/master/graph/badge.svg)](https://codecov.io/gh/aqw/pigskin)

This is a Python module for connecting to the NFL Game Pass service. The code
originated with the aqw/xbmc-gamepass project, but was moved to its own repo to
encourage reuse across projects.

This library handles authentication, querying of available shows and games, and
returns the URLs to watch authenticated streams. It is meant to be used by
various front-ends (such as Kodi, Plex, and VLC).

# NOTE #

Currently, only Game Pass Europe (WPP/Bruin) is supported, as none of the
developers have a Game Pass International (NeuLion) subscription. If you're
interested in getting International Support working again, we'd love to have
your help.

Check out issue #1 for more information.

## Dependencies ##

* Requests 2.x
* m3u8 >= 0.2.10
  * which needs iso8601

## What is NFL Game Pass? ##

NFL Game Pass is service that allows those with subscriptions to watch NFL
games. Live games, archives of old games, NFL TV shows, NFL Network, Red Zone,
coaches tape (22 man view), and game statistics are available.

In 2017, the service split into two services, Game Pass Europe and Game Pass
International.

### What is Game Pass Europe? ##

Game Pass Europe uses WPP/Bruin as its streaming provider(s), and is currently
the only service this module supports.

### What is Game Pass International? ##

Game Pass International uses NeuLion as its streaming partner.

We are looking for a developer with access to an International subscription to
resuscitate support for International subscription. If you're interested in
helping out, checkout issue #1.

## Disclaimer ##

This module is unofficial and is not endorsed or supported by the NFL or NFL
Game Pass in any way.
