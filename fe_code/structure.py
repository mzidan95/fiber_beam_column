import numpy as np

from .node import Node
from .fiber_beam import FiberBeam
from .io import warning


DOF_INDEX_MAP = {"u": 0, "v": 1, "w": 2, "x": 3, "y": 4, "z": 5}


def index_from_dof(dof):
    node_id, dof_type = dof
    return 6 * (node_id - 1) + DOF_INDEX_MAP[dof_type]


def dof_from_index(index):
    raise NotImplementedError


class Structure:
    def __init__(self):
        self._nodes = dict()
        self._elements = dict()
        self._dirichlet_conditions = dict()
        self._newmann_conditions = dict()
        self._tolerance = 1e-7

        self.controled_dof = None

        self._load_factor_increment = 0.0
        self._load_factor = 0.0
        self.converged_load_factor = 0.0
        self.length_increment = 0.4

        self._stiffness = None
        self._unbalanced_forces = None
        self._displacement_increment = None
        self._displacement = None
        self.converged_displacement = None

    @property
    def tolerance(self):
        return self._tolerance

    @tolerance.setter
    def tolerance(self, value):
        self._tolerance = value

    def set_section_tolerance(self, value):
        for element in self.elements:
            for section in element.sections:
                section.tolerance = value

    @property
    def nodes(self):
        return self._nodes.values()

    def get_node(self, node_id):
        return self._nodes[node_id]

    @property
    def elements(self):
        return self._elements.values()

    def get_element(self, element_id):
        return self._elements[element_id]

    @property
    def no_dofs(self):
        return len(self._nodes) * 6

    def add_node(self, node_id, x_pos, y_pos, z_pos):
        self._nodes[node_id] = Node(node_id, x_pos, y_pos, z_pos)

    def add_fiber_beam_element(self, element_id, node1_id, node2_id):
        self._elements[element_id] = FiberBeam(self.get_node(node1_id), self.get_node(node2_id))

    def add_dirichlet_condition(self, node_id, dof_types, value):
        for dof_type in dof_types:
            dof = (node_id, dof_type)
            self._dirichlet_conditions[dof] = value

    def add_neumann_condition(self, node_id, dof_types, value):
        for dof_type in dof_types:
            dof = (node_id, dof_type)
            self._newmann_conditions[dof] = value

    def initialize(self):
        self._stiffness = np.zeros((self.no_dofs, self.no_dofs))
        self._displacement_increment = np.zeros(self.no_dofs)
        self._unbalanced_forces = np.zeros(self.no_dofs)
        self._displacement_increment = np.zeros(self.no_dofs)
        self._displacement = np.zeros(self.no_dofs)
        self.converged_displacement = np.zeros(self.no_dofs)

        for element in self.elements:
            element.initialize()
        self._calculate_stiffness_matrix()

    # FIXME temp fix
    @property
    def force_vector(self):
        controlled_dof = (2, "w")
        force = np.zeros(self.no_dofs)
        force[index_from_dof(controlled_dof)] = 1
        return force

    def _calculate_stiffness_matrix(self):
        stiffness_matrix = np.zeros((self.no_dofs, self.no_dofs))

        for element in self.elements:
            k_e = element.calculate_global_stiffness_matrix()
            i = [index_from_dof(dof) for dof in element.dofs]
            stiffness_matrix[np.ix_(i, i)] = k_e  # stiffness_matrix[i][:i] = k_e

        self._stiffness = stiffness_matrix

    def _calculate_force_vector(self):
        forces = np.zeros(self.no_dofs)
        for condition in self._newmann_conditions.items():
            dof, value = condition
            forces[index_from_dof(dof)] += self._load_factor * value
        return forces

    def _construct_unbalance_forces_first_iteration(self):
        self._unbalanced_forces = np.zeros(self.no_dofs)
        for condition in self._newmann_conditions.items():
            dof, value = condition
            self._unbalanced_forces[index_from_dof(dof)] += self._load_factor * value

    def solve(self, max_ele_iterations):
        """
        main solution loop until element convergence

        steps 3-17
        """
        dofs = self.no_dofs
        lhs = np.zeros((dofs + 1, dofs + 1))
        lhs[:dofs, :dofs] = self._stiffness
        for dof, value in self._dirichlet_conditions.items():
            if value == 0:
                i = index_from_dof(dof)
                lhs[:, i] = 0
                lhs[i, :] = 0
                lhs[i, i] = 1

        lhs[:dofs, -1] = -self.force_vector
        lhs[-1, :dofs] = -self.force_vector
        rhs = np.zeros(dofs + 1)
        rhs[:dofs] = self._unbalanced_forces
        rhs[-1] = self.force_vector @ self._displacement_increment - self.length_increment

        change_in_increments = np.linalg.solve(lhs, rhs)
        self._displacement_increment += change_in_increments[:dofs]
        self._load_factor_increment += change_in_increments[-1]
        self._displacement = self.converged_displacement + self._displacement_increment
        self._load_factor = self.converged_load_factor + self._load_factor_increment

        # STEP 4
        for element in self.elements:
            indices = [index_from_dof(dof) for dof in element.dofs]
            element.calculate_displacement_increment_from_structure(
                change_in_increments[:dofs][indices]
            )

        # STEP 5
        for j in range(1, max_ele_iterations + 1):
            for element in self.elements:
                # STEP 6 & 7
                element.calculate_forces()
                # STEP 8-12
                element.state_determination()

            # STEPS 13-15
            conv = True
            for element in self.elements:
                conv *= element.check_convergence()

            # STEP 17
            if conv:  # all elements converged
                self._calculate_stiffness_matrix()
                for element in self.elements:
                    element.displacement_residual = None
                    for section in element.sections:
                        section.residual = np.zeros(3)
                print(f"Elements converged with {j} iteration(s).")
                break

            # AAAND ... BACK TO STEP 6
            for element in self.elements:
                element.calculate_displacement_residuals()

            if j == max_ele_iterations:
                warning(f"ELEMENTS DID NOT CONVERGE WITH {max_ele_iterations} ITERATIONS")

    def check_nr_convergence(self):
        """ steps 18-20 """
        resisting_forces = np.zeros(self.no_dofs)
        for element in self.elements:
            f_e = element.l_e @ element.resisting_forces
            i = [index_from_dof(dof) for dof in element.dofs]
            resisting_forces[i] += f_e
        for dof, value in self._dirichlet_conditions.items():
            if value == 0:
                resisting_forces[index_from_dof(dof)] = value

        external_forces = self._calculate_force_vector()

        self._unbalanced_forces = external_forces - resisting_forces

        return abs(np.linalg.norm(self._unbalanced_forces)) < self._tolerance

    def finalize_load_step(self):
        """ step 21 """
        self._displacement_increment = np.zeros(self.no_dofs)
        self._load_factor_increment = 0.0
        self.converged_displacement = self._displacement
        self.converged_load_factor = self._load_factor
        for element in self.elements:
            element.finalize_load_step()

    def reverse_all_fibers(self):
        for element in self.elements:
            for section in element.sections:
                for fiber in section.fibers:
                    fiber.reverse_loading()

    def new_loading(self, length_incr, controled_displacement):
        self.length_increment = length_incr
        self._dirichlet_conditions[(2, "w")] = controled_displacement
