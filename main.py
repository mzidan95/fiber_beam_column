"""
Example
"""

from fe_code import io
from plotting import plot_disctrized_2d, initiate_plot, update_plot
from models.column import model1, model2, model3
from disp_calc import calculate_loadsteps

STEP = 0.4
STEPS = calculate_loadsteps(STEP)

PLOT_FLAG = True
SAVE_PLOT = True


def add_solution_parameters(structure):
    """ add tolerance values and boundary conditions """
    # CONVERGENCE TOLERANCE VALUES
    structure.tolerance = 0.05
    structure.set_section_tolerance(0.05)

    # BOUNDARY CONDITIONS
    structure.set_controled_dof(2, "w")
    structure.add_dirichlet_condition(1, "uvwxyz", 0)
    structure.add_dirichlet_condition(2, "x", 0)
    structure.add_dirichlet_condition(2, "z", 0.005)  # useless
    print("Added the boundary conditions.")


def advance_in_load(structure, load_step):
    """ load stepping loop """

    if load_step < STEPS[0]:
        structure.controled_dof_increment = STEP

    elif load_step < STEPS[1]:
        structure.controled_dof_increment = -STEP

    elif load_step < STEPS[2]:
        structure.controled_dof_increment = STEP

    elif load_step < STEPS[3]:
        structure.controled_dof_increment = -STEP

    elif load_step < STEPS[4]:
        structure.controled_dof_increment = STEP

    elif load_step < STEPS[5]:
        structure.controled_dof_increment = -STEP

    else:
        structure.controled_dof_increment = STEP


def solution_loop(structure):
    max_nr_iterations = 100
    max_ele_iterations = 100

    structure.initialize()
    print(":: Initialized the solver ::")

    load = [0]
    disp = [0]
    print("\n:: Starting solution loop ::")

    if PLOT_FLAG:
        fig, axes, line = initiate_plot()

    for k in range(1, STEPS[-1]):
        print(f"\nLOAD STEP : {k}")
        advance_in_load(structure, k)

        for i in range(1, max_nr_iterations + 1):
            structure.solve(max_ele_iterations)
            convergence, residual = structure.check_nr_convergence()
            if convergence:
                print(f"NR converged with {i} iteration(s). Residual = {residual}")
                break
            if i == max_nr_iterations:
                io.warning(f"Newton-Raphson did not converge {max_nr_iterations} iterations")

        structure.finalize_load_step()

        if PLOT_FLAG:
            load.append(100 * structure.converged_load_factor)
            disp.append(1 / 10000 * 3 * structure.converged_controled_dof)
            update_plot(axes, line, disp, load)

    print("\n:: Finished solution loop ::")
    if PLOT_FLAG and not SAVE_PLOT:
        fig.show()
    if PLOT_FLAG and SAVE_PLOT:
        fig.savefig("moment_curvature.png")


if __name__ == "__main__":
    stru = model3()
    plot_disctrized_2d(stru.get_element(1))
    add_solution_parameters(stru)
    solution_loop(stru)
