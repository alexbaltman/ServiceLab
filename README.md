servicelab
==========

servicelab is a virtual environment for testing service deployments.

## Quickstart

```
./stack workon [servicename]
./stack up
./stack deploy
```

## ./stack Command Reference

```
./stack workon [servicename]
```
Sets up the environment for working on a particular service.  Expects a repo for the form "service-[servicename]" in gerrit.
Services get installed into `services/`.  The target service is symlinked to `service/` for ease of use.

```
./stack up
```
Runs vagrant up

```
./stack deploy
```
Runs heighliner deploy on the target service

```
./stack clean
```
Destroys existing vagrant vms and unlinks the target service.  Start work again with `./stack workon`. Services cloned to `services/` remain intact.
