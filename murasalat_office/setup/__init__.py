"""Site setup helpers.

Two things live here, both deliberately explicit and administrator-invoked:

* ``master_data``  — seeds the lookup tables the transaction DocTypes link to.
                     Data only: no roles, no permissions, no workflows.
* ``governance_plan`` — prints the exact Desk configuration a site needs, and can
                     materialise it only when a caller explicitly asks for that.

Nothing in this package is applied automatically on install or migrate. There is no
``fixtures`` hook. Site governance stays the site administrator's decision.
"""
