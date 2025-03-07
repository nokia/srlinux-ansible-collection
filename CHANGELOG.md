# Changelog

* [Changelog](#changelog)
  * [v1.0.0](#v100)
    * [New modules](#new-modules)
  * [v1.0.2](#v102)
    * [Bug fixes](#bug-fixes)
  * [v1.0.3](#v103)
    * [Chores](#chores)

## v1.0.0

### New modules

* nokia.srlinux.get - Retrieve configuration or state element from Nokia SR Linux devices.
* nokia.srlinux.config - Update, replace and delete configuration on SR Linux devices.
* nokia.srlinux.validate - Validating configuration on SR Linux devices.
* nokia.srlinux.cli - Execute CLI commands on SR Linux devices.

## v1.0.2

### Bug fixes

* Retry on `save_when` when the json-rpc is undergoing a reload. This happens when the replace/update operation changes json-rpc server config.

## v1.0.3

### Chores

* Removed unused artifacts from the build.
