from functools import partial

import gurobipy as gp
from gurobipy import GRB
import time


class CallbackData:
    def __init__(self):
        self.last_gap_change_time = -GRB.INFINITY
        self.last_gap = GRB.INFINITY


def callback(model, where, *, cbdata):
    if where != GRB.Callback.MIP:
        return
    if model.cbGet(GRB.Callback.MIP_SOLCNT) == 0:
        return

    # Temps écoulé depuis le début de l'optimisation
    current_time = time.time()

    # Récupérer le MIPGap actuel
    current_objbst = model.cbGet(GRB.Callback.MIP_OBJBST)
    current_objbnd = model.cbGet(GRB.Callback.MIP_OBJBND)
    current_gap = abs(current_objbst - current_objbnd) / (1.0 + abs(current_objbst))

    # Si c'est la première solution trouvée, initialise les données
    if cbdata.last_gap_change_time == -GRB.INFINITY:
        cbdata.last_gap_change_time = current_time
        cbdata.last_gap = current_gap
        return

    # Vérifie si le MIPGap a changé de manière significative
    if abs(cbdata.last_gap - current_gap) > epsilon_to_compare_gap:
        cbdata.last_gap_change_time = current_time
        cbdata.last_gap = current_gap
        return

    # Vérifie si le MIPGap n'a pas changé significativement depuis 50 secondes
    if current_time - cbdata.last_gap_change_time > time_from_best:
        print("Stopping optimization: MIPGap did not improve significantly for 50 seconds.")
        model.terminate()



with gp.read("data/mkp.mps.bz2") as model:
    # Global variables used in the callback function
    time_from_best = 50
    epsilon_to_compare_gap = 1e-4

    # Initialize data passed to the callback function
    callback_data = CallbackData()
    callback_func = partial(callback, cbdata=callback_data)

    model.optimize(callback_func)