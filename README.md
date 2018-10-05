# A Python Library for NFL Game Pass

[![Build Status](https://travis-ci.org/aqw/pigskin.svg?branch=master)](https://travis-ci.org/aqw/pigskin)
[![codecov](https://codecov.io/gh/aqw/pigskin/branch/master/graph/badge.svg)](https://codecov.io/gh/aqw/pigskin)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/1c93258e07e444798ef09a31473da3bb)](https://www.codacy.com/app/aqw/pigskin?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=aqw/pigskin&amp;utm_campaign=Badge_Grade)

Pigskin is a Python library for connecting to the NFL Game Pass service. The
code originated with the [xbmc-gamepass project](https://github.com/aqw/xbmc-gamepass),
but was moved to its own repo to encourage reuse across projects.

This library handles authentication, querying of available games, shows, and
statistics, and returns the URLs to watch authenticated streams. It is meant to
be used by a variety of front-ends (such as Kodi, Plex, and VLC).

## NOTE

Currently, only Game Pass Europe (WPP/Bruin) is supported, as none of the
developers have a Game Pass International (NeuLion) subscription. If you're
interested in getting International Support working again, we'd love to have
your help.

Check out issue [#1](https://github.com/aqw/pigskin/issues/1) for more information.

## Dependencies

-   Requests 2.x

-   m3u8 >= 0.2.10
    -   which needs iso8601

## What is NFL Game Pass?

NFL Game Pass is service that allows those with subscriptions to watch NFL
games. Live games, archives of old games, NFL TV shows, NFL Network, Red Zone,
coaches tape (22 man view), and game statistics are available.

In 2017, the service split into two services, Game Pass Europe and Game Pass
International.

### What is Game Pass Europe?

Game Pass Europe uses WPP/Bruin as its streaming provider(s), and is currently
the only service this library supports.

### What is Game Pass International?

Game Pass International uses NeuLion as its streaming partner.

We are looking for a developer with access to an International subscription to
resuscitate support for International subscription. If you're interested in
helping out, check out issue [#1](https://github.com/aqw/pigskin/issues/1).

## Disclaimer

This library is unofficial and is not endorsed nor supported by the NFL or NFL
Game Pass in any way.
