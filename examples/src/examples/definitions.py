import examples.defs

from dagster import definitions, load_defs


@definitions
def defs():
    return load_defs(defs_root=examples.defs)
