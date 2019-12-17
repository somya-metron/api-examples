# Expanse API Code Samples
This is a library of code samples and scripts for Expanse's APIs.

## Features

- Call Expanse APIs simply using scripts
- Handle Expanse Auth with fewer lines of code
- Use standard tooling for installation

## Documentation
Learn how to use the Expanse API Code Samples with these guides:

### Getting Started
To use, download the .zip and extract the contents, or clone the repository.
#### Setup - Python Scripts

- First, you'll need to install dependencies with pip:
```shell script
pip install -r requirements.txt
```

- To run a script, from directory root: 
```shell script
cd expander_api/python
python script-name parameter
```

- To run unit tests: 
```shell script
cd tests
pytest test_name.py
```

Each script is documented with usage instructions.

#### Supported Python Versions
Python 3.7 and above is supported and tested.


## Third Party Libraries and Dependencies

The following libraries are used (see [requirements.txt](expander_api/python/requirements.txt)):
* [Requests](https://pypi.org/project/requests/)
* [PyTest](https://github.com/pytest-dev/pytest/)
