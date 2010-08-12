from openalea.core.alea import *

pm = PackageManager()
pm.init(verbose=False)

# These tests use gnuplot interface, which requires human interaction
# Consequently, they cannot be used within builbot (which hangs forever)
# We added a flags inside aml/src/aml/wralea/py_stat.py to prevent gnuplot
# to be launched if these tests are run with nosetests. The remaining of the
# nodes are run.
# In order to have the gnuplot interface, run this script with python instead of nosetests 

def test_pylab_nodes():
    res = run(('openalea.pylab.nodes', 'PyLabRandom'),{},pm=pm)
    assert len(res[0]) == 100

res = test_pylab_nodes()
