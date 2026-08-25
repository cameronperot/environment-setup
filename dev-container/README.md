# Dev Container
This dev container is designed for LLM-assisted coding to restrict the data and information the agent has access to and reduce the chance of harmful changes to the host system.

Note: Containers are not a security measure. If you need security isolation then consider using a VM.

## Building
The Containerfile copies the repository root into the image, so the build context is the
repository root (the parent of this directory). Run the provided script from anywhere:
```bash
./dev-container/build.sh
```

## Usage
This is best used with the following alias that will run a container and mount the current working directory to `/work`:
```bash
alias c='podman run \
  -it \
  --rm \
  --userns keep-id \
  --security-opt label=disable \
  -v dev-antigen:/home/user/.antigen \
  -v ${PWD}:/work \
  dev:latest'
```
The alias can be used to run `some_executable` in the current working directory with:
```bash
c some_executable
```

A compose file running Jupyter lab is also provided for a longer running environment:
```bash
podman-compose -f compose.yml up
```
