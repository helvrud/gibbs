"""
Patch to use asyncio in Jupyter, import it to the script you want to run in Jupyter
"""

def isnotebook():
    try:
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':
            return True   # Jupyter notebook or qtconsole
        elif shell == 'TerminalInteractiveShell':
            return False  # Terminal running IPython
        else:
            return False  # Other type (?)
    except NameError:
        return False      # Probably standard Python interpreter
if isnotebook():
    import nest_asyncio
    nest_asyncio.apply()
    print("Interaction environment notified.\n Asyncio patched!")
else:
    print("Python interpreter notified.\n Asyncio not patched!")