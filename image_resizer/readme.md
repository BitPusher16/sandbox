
https://kevingal.com/blog/cli-tools.html
"Recreating grep in Python"

https://packaging.python.org/en/latest/discussions/setup-py-deprecated/
"Is setup.py deprecated?"

https://stackoverflow.com/questions/62983756/what-is-pyproject-toml-file-for
"pyproject.toml is a new configuration file introducted by PEP 517..."

https://packaging.python.org/en/latest/tutorials/packaging-projects/

packaging_tutorial/
├── LICENSE
├── pyproject.toml
├── README.md
├── src/
│   └── example_package_YOUR_USERNAME_HERE/
│       ├── __init__.py
│       └── example.py
└── tests/

calling python module from scripts dir:
https://stackoverflow.com/questions/57744466/how-to-properly-structure-internal-scripts-in-a-python-project


This page has most detailed explanation so far on 
how to write and run packages:
https://python.land/project-structure/python-packages
.
└── package_name
    ├── __init__.py
    ├── subpackage1
        ├── __init__.py
        ├── module1.py
    └── subpackage2
        ├── __init__.py
        ├── module2.py

https://stackoverflow.com/questions/7610001/what-is-the-purpose-of-the-m-switch

Module execution via import statement (i.e., import <modulename>):

sys.path is not modified in any way
__name__ is set to the absolute form of <modulename>
__package__ is set to the immediate parent package in <modulename>
__init__.py is evaluated for all packages (including its own for package modules)
__main__.py is not evaluated for package modules; the code is evaluated for code modules

Module execution via command line with filename (i.e., python <filename>):

sys.path is modified to include the final directory in <filename>
__name__ is set to '__main__'
__package__ is set to None
__init__.py is not evaluated for any package (including its own for package modules)
__main__.py is evaluated for package modules; the code is evaluated for code modules.

Module execution via command line with modulename (i.e., python -m <modulename>):

sys.path is modified to include the current directory
__name__ is set to '__main__'
__package__ is set to the immediate parent package in <modulename>
__init__.py is evaluated for all packages (including its own for package modules)
__main__.py is evaluated for package modules; the code is evaluated for code modules


https://stackoverflow.com/questions/62983756/what-is-pyproject-toml-file-for

How would one install a project with pyproject.toml in an editable state?

Solution
Since the release of poetry-core v1.0.8 in Feb 2022 you can do this:

a) you need this entry in your pyproject.toml:

[build-system]
requires = ["poetry-core>=1.0.8"]
build-backend = "poetry.core.masonry.api"
b) run:

pip install -e .

(pip install -e . does indeed find "image_resizer" in src/ and install it,
but it's not clear how it is searching for packages.)

numpy uses this structure;

numpy/
  numpy
  requirements
  tools

learnings:
it's very confusing that packaging.python.org recommends putting module in src.
this does in fact work with pyproject.toml.
and it can be installed dynamically (somewhat) with pip.
however, it makes running as a module from repo root difficult,
because python -m only adds the current dir to python path.
many reputable repos do stutter structure, so i will too.

2024-03-25
Trying different python LSP servers.
pylyzer wouldn't install (rust error)
installed jedi, got jumps working, but limited live feedback.
installed pylsp, getting more feedback now.
jumps are working.
