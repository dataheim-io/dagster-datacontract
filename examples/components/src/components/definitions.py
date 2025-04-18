from dagster.components import definitions, load_defs

import components.defs


@definitions
def defs():
    return load_defs(defs_root=components.defs)
