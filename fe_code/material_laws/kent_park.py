"""
Module contains only KentParkMod class
"""

from .material import UniaxialIncrementalMaterial


class KentPark(UniaxialIncrementalMaterial):
    """
    Modified Concrete uniaxial material law

    Parameters
    ----------
    fc : float
        yield compressive strength
    K : float
        confinement factor
    Z : float
        softening slope
    e0 : float
        strain at maximum stress. default 0.002
    eu : float, optional
        ultimate strain (crushing)

    Note :: can be construced either using
    KentPark(fc, K, Z, e0) or
    KentPark.eu(fc, K, eu, e0)

    Attributes
    ----------
    tangent_modulus : float
    stress : float
    strain : float
    """

    def __init__(self, fc, Z, e0=0.002):

        self._fc = fc
        self._strain_0 = e0
        self._strain_u = -(0.8 / abs(Z) + abs(e0))

        if self._fc > 0:
            self._fc = -self._fc
        if self._strain_0 > 0:
            self._strain_0 = -self._strain_0

        Et0 = 2 * self._fc / self._strain_0
        self._strain = 0.0
        self._stress = 0.0
        self._strain_r = 0.0
        self._strain_p = 0.0
        self._unload_slope = Et0
        self._Et = Et0

        self._c_strain = 0.0
        self._c_stress = 0.0
        self._c_strain_r = 0.0
        self._c_strain_p = 0.0
        self._c_unload_slope = Et0
        self._c_Et = Et0

    @classmethod
    def eu(cls, fc, eu, e0=0.002):
        """
        Overloading the default constructor with eu
        instead of Z
        """
        Z = 0.8 / (eu - e0)
        return cls(fc, Z, e0)

    @property
    def tangent_modulus(self):
        """ current tangent modulus """
        return self._Et

    @property
    def stress(self):
        """ current stress """
        return self._stress

    @property
    def strain(self):
        """ current strain """
        return self._strain

    def update_strain(self, fiber_strain):
        """
        set new strain and test for reversal

        Parameters
        ----------
        fiber_strain : float
            fiber strain

        Returns
        -------
        reversal : bool
            flag True if reversed
        """
        self._set_trial_state(fiber_strain)
        return

    def _set_trial_state(self, new_strain):
        self._strain = new_strain

        self._strain_r = self._c_strain_r
        self._strain_p = self._c_strain_p
        self._unload_slope = self._c_unload_slope
        self._stress = self._c_stress
        self._Et = self._c_Et

        deps = self._strain - self._c_strain
        if abs(deps) < 1e-15:
            return

        if self._strain > 0.0:
            self._stress = 0.0
            self._Et = 0.0
            return

        stress_temp = (
            self._c_stress + self._unload_slope * (self._strain - self._c_strain)
        )
        # further into compression
        if self._strain < self._c_strain:
            self._reload()
            if stress_temp > self._stress:
                self._stress = stress_temp
                self._Et = self._unload_slope
        # towards tension
        elif self._strain < self._strain_p:
            self._stress = stress_temp
            self._Et = self._unload_slope
        # further into tension
        else:
            self._stress = 0.0
            self._Et = 0.0

    def _reload(self):
        if self._strain < self._strain_r:
            self._strain_r = self._strain
            self._envelope()
            self._unload()
        elif self._strain < self._strain_p:
            self._Et = self._unload_slope
            self._stress = self._Et * (self._strain - self._strain_p)
        else:
            self._stress = 0.0
            self._Et = 0.0

    def _envelope(self):
        if self._strain > self._strain_0:
            eta = self._strain / self._strain_0
            self._stress = self._fc * (2 * eta - eta * eta)
            E0 = 2 * self._fc / self._strain_0
            self._Et = E0 * (1.0 - eta)
        elif self._strain >= self._strain_u:
            self._Et = (self._fc - 0.2 * self._fc) / (self._strain_0 - self._strain_u)
            self._stress = self._fc + self._Et * (self._strain - self._strain_0)
        else:
            self._stress = 0.2 * self._fc
            self._Et = 0.0

    def _unload(self):
        # is strain_temp strain_r?
        strain_temp = self._strain_r
        if strain_temp < self._strain_u:
            strain_temp = self._strain_u
        eta = strain_temp / self._strain_0
        ratio = 0.707 * (eta - 2.0) + 0.834
        if eta < 2:
            ratio = 0.145 * eta * eta + 0.13 * eta
        self._strain_p = ratio * self._strain_0

        # self._unload_slope = self._stress / (self._strain_r - self._strain_p)

        temp1 = self._strain_r - self._strain_p
        E0 = 2 * self._fc / self._strain_0
        temp2 = self._stress / E0
        if temp1 > -1e-15:
            self._unload_slope = E0
        if temp1 <= temp2:
            self._strain_p = self._strain_r - temp1
            self._unload_slope = self._stress / temp1
        else:
            self._strain_p = self._strain_r - temp2
            self._unload_slope = E0

    def finalize_load_step(self):
        """
        update the converged variables. Called when the
        whole structure is converged at the load step
        """
        self._c_strain = self._strain
        self._c_stress = self._stress
        self._c_strain_r = self._strain_r
        self._c_strain_p = self._strain_p
        self._c_unload_slope = self._unload_slope
        self._c_Et = self._Et
