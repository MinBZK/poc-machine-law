How to build the gopy bindings

Build the docker container with:

```bash
docker build -t gopy-container .
```

Run the container with:

```bash
docker run -it -v $(pwd):/app gopy-container bash
```

Run in the container:
```bash
gopy build --output=gopy_machine -vm=python3 ./service
```

A new .so file be created into this folder
