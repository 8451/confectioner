# Usage

Confectioner is a framework for organizing configuration files in a composable way. Confectioner is built around the idea of
*recipes* and *ingredients*. Ingredients are the config files that you actually use in your program (usually JSON), 
while recipes are config files that declare how to combine different ingredients given a set of parameters. Recipes
can themselves contain ingredients or more recipes.

## A Simple Example

Let's say that your application can runs in a dev environment and a prod environment, but it has a few parameters that 
are different depending on the environment. Without confectioner, you might have two config files like this:


### conf/dev.json
```json
{
  "PROJECT_ROOT": "s3://dev_bucket",
  "INPUT_SUBPATH": "inputs",
  "OUTPUT_SUBPATH": "output"
}
```

### conf/prd.json
```json
{
  "PROJECT_ROOT": "s3://prd_bucket",
  "INPUT_SUBPATH": "inputs",
  "OUTPUT_SUBPATH": "output"
}
```

This works, but we had to duplicate options across config files, which means if there are any updates we need to update
both files. Instead, we could merge the files like this.

### conf/config.json
```json
{
  "DEV": {
    "PROJECT_ROOT": "s3://dev_bucket"  
  },
  "PRD": {
    "PROJECT_ROOT": "s3://prd_bucket"
  },
  "COMMON": {
    "INPUT_SUBPATH": "inputs",
    "OUTPUT_SUBPATH": "output"
  }
}
```

This works at first, but in your code you have to keep track of which config entries are environment-specific. If you have
a parameter that used to be the same across all environments and suddenly becomes environment-specific, you need to change
your code to look in the environment-specific area rather than the common area.

With confectioner, we handle this by separating the config into multiple files and then combining them at runtime. In this
example, our configs would look like this

### Directory Structure

```
recipe.yml
conf/
    dev.json
    prd.json
    global.json
```

### conf/dev.json
```json
{
  "PROJECT_ROOT": "s3://dev_bucket"
}
```

### conf/prd.json
```json
{
  "PROJECT_ROOT": "s3://prd_bucket"
}
```

### conf/global.json
```json
{
  "INPUT_SUBPATH": "inputs",
  "OUTPUT_SUBPATH": "output"
}
```

In order to combine the config files, we create a *recipe* file, here called *recipe.yml*.

### recipe.yml
```yaml
- ingredients: conf/global.json
- env: dev
  ingredients: conf/dev.json
- env: prd
  ingredients: conf/prd.json 
```

To load in our config file, we use the confectioner `bake` function, and pass `env='dev'` or `env='prd'` to signify
what files we want to load.

```python
>>> from confectioner import bake
>>> 
>>> bake('recipe.yml', env='dev')
{'INPUT_SUBPATH': 'inputs', 'OUTPUT_SUBPATH': 'outputs', 
'PROJECT_ROOT': 's3://dev_bucket'}
>>> 
>>> bake('recipe.yml', env='prd')
{'INPUT_SUBPATH': 'inputs', 'OUTPUT_SUBPATH': 'outputs', 
'PROJECT_ROOT': 's3://prd_bucket'}
```

## What It's Doing

Let's take a look at that simple recipe file we created and break down what it's saying.

### recipe.yml
```yaml
- ingredients: conf/global.json
- env: dev
  ingredients: conf/dev.json
- env: prd
  ingredients: conf/prd.json 
```

There are three entries listed here. Let's break them down one-by-one.

### Global

```yaml
- ingredients: conf/global.json
```

This entry only has the ingredients tag, so it will be included any time we run `bake` with this recipe. The ingredients
are the `conf/global.json` file. Because that is a relative path, confectioner will look relative to the recipe file that 
included the ingredient.

### Dev

```yaml
- env: dev
  ingredients: conf/dev.json
```

This entry has `env: dev`, so it will only be included when we pass `env='dev'`

### Prd

```yaml
- env: prd
  ingredients: conf/prd.json 
```

This entry has `env: prd`, so it will only be included when we pass `env='prd'`


## Templating
Confectioner supports templating in ingredients files. This allows confectioner to dynamically generate config entries based on
other config entries. For example, let's say we have a config file that looks like this:

```json
{
  "PROJECT_ROOT": "s3://dev_bucket",
  "INPUT_SUBPATH": "inputs",
  "INPUT_PATH": "{PROJECT_ROOT}/{INPUT_SUBPATH}",
}
```

When this file is loaded, the `INPUT_PATH` entry will be populated with the value `"s3://dev_bucket/inputs"`. 
This allows us to avoid duplicating information across config files.


## More Complex Recipes

### Multiple Match Conditions

A recipe entry can use multiple match conditions. If every condition is met, then the ingredients are included.

```yaml
- env: dev
  job: scoring
  ingredients: dev/scoring.json
- env: prd
  job: scoring
  ingredients: prd/scoring.json
```

### Multiple Ingredients

A recipe entry can point to multiple files. For example, if we add a test environment, we could add a non-prod file that
is included in both dev and test environments for any common configuration.

```yaml
- env: dev
  ingredients: 
    - dev.json
    - non-prod.json
- env: tst
  ingredients: 
    - tst.json
    - non-prod.json
- env: prd
  ingredients: prd.json
```

### List conditions

If a tag in a recipe contains a list, then it will match if the value passed to `bake` is in the list. We can accomplish
the same thing as the prior example by adding an entry that matches either when 
either dev or prd is the environment.

```yaml

- env: dev
  ingredients: dev.json
- env: tst
  ingredients: tst.json
- env:
    - dev
    - tst
  ingredients: non-prod.json
- env: prd
  ingredients: prd.json
```

### Sub-Recipes

We can also include other recipes within our recipe. This makes our recipe files modular to increase readability. 

Let's take the following recipe and break it up into smaller pieces

#### Before

##### Directory Structure

```
recipe.yml
jobs/
    dev/
        foo.json
        bar.json
    prd/
        foo.json
        bar.json
```

##### recipe.yml

```yaml
- env: dev
  job: foo
  ingredients: jobs/dev/foo.json
- env: dev
  job: bar
  ingredients: jobs/dev/bar.json
- env: prd
  job: foo
  ingredients: jobs/prd/foo.json
- env: prd
  job: bar
  ingredients: jobs/prd/bar.json
```


#### After

##### Directory Structure
```
recipe.yml
recipes/
    dev.yml
    prd.yml
jobs/
    dev/
        foo.json
        bar.json
    prd/
        foo.json
        bar.json
```

##### recipe.yml

```yaml
- env: dev
  recipes: recipes/dev.yml
- env: prd
  recipes: recipes/prd.yml
```

##### recipes/dev.yml

```yaml
- job: foo
  ingredients: ../jobs/dev/foo.json
- job: bar
  ingredients: ../jobs/dev/bar.json
```

##### recipes/prd.yml

```yaml
- job: foo
  ingredients: ../jobs/prd/foo.json
- job: bar
  ingredients: ../jobs/prd/bar.json
```

### String Formatting in Recipes

Recipes support string formatting. The strings should be enclosed in double quotes. We can simplify the example from
the past section by leveraging this. Here calling `bake('recipe.yml', env='dev', job='foo')` would load 
`jobs/dev/foo.json`.

#### Directory Structure

```
recipe.yml
jobs/
    dev/
        foo.json
        bar.json
    prd/
        foo.json
        bar.json
```

#### recipe.yml

```yaml
- env: 
    - dev
    - prd
  job: 
    - foo
    - bar
  ingredients: "{env}/{job}.yml"
```

### Else Blocks

To avoid listing out exhaustive match patterns, use the `else` tag. Else matches whenever the
previous entry did not match. Else blocks can include other conditions to act like an else-if, 
and can be strung together like a Python if-elif-else block. 

```yaml
- day: 
    - saturday
    - sunday
  weather: sunny
  ingredients: hike.json
- else:
  day:
    - saturday
    - sunday
  ingredients: movie.json
- else:
  ingredients: work.json
```

## Creating Baker Objects

By default, when given a relative path confectioner looks in the current working directory (`os.getcwd()`). This is usually
the directory from which the python process was started. If you are writing a python package that ships with 
config files, you may want to explicitly set the home directory as a directory containing all the config files in your
package. You can do this by creating a `Baker` object. `Baker` objects expose wrappers for all the core confectioner 
functions (`bake`, `shop`, `prep`, `mix`). This allows you to use relative paths for readability and portability while 
still ensuring you can specify exactly where your config files live.

### Directory Structure

```
setup.py
mypackage/
    main.py
    utils.py
    conf/
        recipe.yml
        ingredient1.json
        ingredient2.json
```

### mypackage/main.py

```python
from confectioner import Baker
import os


curdir = os.path.abspath(os.path.dirname(__file__))
home = os.path.join(curdir, 'conf')

baker = Baker(home)


def load_config(arg1):
  return baker.bake('recipe.yml', arg1=arg1)
```

## Extending IO
Out of the box, confectioner supports reading and writing json and yaml files from the local filesystem. However, you can
extend confectioner to support other file types and other storage locations using 
`confectioner.files.register_reader` and `confectioner.files.register_loader`.

### Registering a Reader

*Readers* are functions that take a path and return a file IO object (like the built-in `open` function). If you want
to support a file on a new file system, such as azure blob storage, you can register a reader by providing a function
that handles azure blob storage paths as well as the protocol for those paths.

```python
import typing

import confectioner.files

def azure_blob_reader(path: str) -> typing.IO:
    ...

confectioner.files.register_reader('abfss', azure_blob_reader)
```

### Registering a Loader
*Loaders* are functions that take a file IO object and return a python object representation of the contents of
the IO (like the `json.load` function from the standard library). To provide support for a new file type, such as
toml, you can register a loader by providing a function that handles the file type and the file extension where
it should be used.

```python
import typing

import confectioner.files

def toml_loader(file: typing.IO) -> typing.Any:
    ...

confectioner.files.register_loader('.toml', toml_loader)
```