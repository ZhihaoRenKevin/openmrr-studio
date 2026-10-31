"""Comprehensive Integrated Photonics Material Optical Property Library.

Clean-room implementation from peer-reviewed literature (no proprietary vendor
material files used). Covers 14+ core waveguide, cladding, and active materials:
  - Group IV: Crystalline Si (`Si`), Hydrogenated Amorphous Si (`a-Si`), Germanium (`Ge`)
  - Nitrides: Stoichiometric LPCVD `Si3N4` (`SiN`), Silicon-Rich `SiNx`, Wurtzite `AlN`,
    Scandium-doped `ScAlN` (`Sc_x Al_{1-x} N`, continuous x in [0, 0.40])
  - Carbides: Uniaxial `4H-SiC` (c-cut), Cubic `3C-SiC`
  - Ferroelectrics: Thin-Film Lithium Niobate `LiNbO3` (`LN_Zcut` & `LN_Xcut`)
  - Dielectrics & Oxides: Fused Silica (`SiO2`), Sapphire/ALD Alumina (`Al2O3`), `Air`
  - Phase-Change Materials: Low-loss `GSST` (`Ge2Sb2Se4Te1`, amorphous & crystalline states)

All wavelengths are in SI metres (m) unless noted; temperatures in Kelvin (K).
Cross-section axis convention:
  x = radial / horizontal in-plane, y = vertical (wafer normal), z = propagation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Callable

import numpy as np

# Fundamental physical constants (SI units)
C0_M_PER_S = 299792458.0          # unit: m/s
H_PLANCK_J_S = 6.62607015e-34     # unit: J*s
HBAR_J_S = H_PLANCK_J_S / (2.0 * math.pi)
EPS0_F_PER_M = 8.8541878128e-12   # unit: F/m
Z0_OHM = 376.730313668            # unit: Ohm
T_REF_K = 300.0                   # unit: K


@dataclass(frozen=True)
class MaterialIndexTensor:
    """Diagonal complex refractive index + thermo/electro-optic & Kerr properties."""
    nx: float
    ny: float
    nz: float
    kx: float = 0.0
    ky: float = 0.0
    kz: float = 0.0
    dn_dt_per_k: float = 0.0       # unit: K^-1 (dominant thermo-optic coefficient)
    r33_pm_per_v: float = 0.0      # unit: pm/V (Pockels r_33 along crystal c/Z axis)
    r13_pm_per_v: float = 0.0      # unit: pm/V (Pockels r_13 perpendicular to c/Z axis)
    n2_m2_per_w: float = 0.0       # unit: m^2/W (Kerr nonlinear index)
    crystal_symmetry: str = "isotropic"
    validity_um: tuple[float, float] = (0.4, 5.0)
    source: str = ""
    is_anisotropic: bool = False

    def complex_eps_diag(self) -> tuple[complex, complex, complex]:
        ex = (self.nx + 1j * self.kx) ** 2
        ey = (self.ny + 1j * self.ky) ** 2
        ez = (self.nz + 1j * self.kz) ** 2
        return ex, ey, ez

    def to_dict(self) -> dict:
        return asdict(self)


def _check_wl(wavelength_m: float) -> float:
    if not (math.isfinite(wavelength_m) and wavelength_m > 0.0):
        raise ValueError("wavelength_m must be finite and strictly positive")
    return wavelength_m * 1e6  # returns wavelength in um


# ==============================================================================
# 1. Claddings & Oxides (Air, SiO2, Al2O3)
# ==============================================================================

def n_air(wavelength_m: float, temperature_k: float = T_REF_K) -> MaterialIndexTensor:
    """Air / vacuum reference index (n = 1.0)."""
    _ = (_check_wl(wavelength_m), temperature_k)
    return MaterialIndexTensor(
        nx=1.0, ny=1.0, nz=1.0,
        dn_dt_per_k=0.0,
        validity_um=(0.1, 50.0),
        source="Vacuum/Air nominal n=1.0",
        is_anisotropic=False,
    )


def n_sio2_sellmeier(wavelength_m: float, temperature_k: float = T_REF_K) -> MaterialIndexTensor:
    """Fused silica (SiO2) Sellmeier + thermo-optic shift.

    Source: Malitson, JOSA 55, 1205 (1965); Leviton & Frey (2006) dn/dT = 8.5e-6 K^-1.
    """
    u = _check_wl(wavelength_m)
    x = u * u
    n0 = math.sqrt(
        max(
            1.0
            + 0.6961663 * x / (x - 0.068043 ** 2)
            + 0.4079426 * x / (x - 0.1162414 ** 2)
            + 0.8974794 * x / (x - 9.896161 ** 2),
            1.0,
        )
    )
    dn_dt = 8.5e-6
    n = n0 + dn_dt * (temperature_k - T_REF_K)
    return MaterialIndexTensor(
        nx=n, ny=n, nz=n,
        dn_dt_per_k=dn_dt,
        n2_m2_per_w=2.6e-20,
        validity_um=(0.21, 6.7),
        source="Malitson JOSA 1965 + Leviton & Frey 2006 (dn/dT=8.5e-6 K^-1)",
        is_anisotropic=False,
    )


def n_al2o3_sapphire(wavelength_m: float, temperature_k: float = T_REF_K) -> MaterialIndexTensor:
    """ALD Alumina / C-plane Sapphire (Al2O3) Sellmeier dispersion.

    Source: Malitson, JOSA 52, 1377 (1962).
    """
    u = _check_wl(wavelength_m)
    x = u * u
    no = math.sqrt(
        max(
            1.0
            + 1.4313493 * x / (x - 0.0726631 ** 2)
            + 0.65054713 * x / (x - 0.1193242 ** 2)
            + 5.3414021 * x / (x - 18.028251 ** 2),
            1.0,
        )
    )
    dn_dt = 1.2e-5
    n = no + dn_dt * (temperature_k - T_REF_K)
    return MaterialIndexTensor(
        nx=n, ny=n, nz=n,
        dn_dt_per_k=dn_dt,
        n2_m2_per_w=3.0e-20,
        validity_um=(0.25, 5.5),
        source="Malitson JOSA 1962 (Al2O3 / Sapphire)",
        is_anisotropic=False,
    )


# ==============================================================================
# 2. Group IV Semiconductors (Si, a-Si:H, Ge)
# ==============================================================================

def n_si_crystalline(
    wavelength_m: float,
    temperature_k: float = T_REF_K,
    fixed_1550_index: bool = False,
) -> MaterialIndexTensor:
    """Crystalline Silicon (Si) dispersion & thermo-optic model.

    Source: Salzberg & Villa, JOSA 47, 244 (1957); Cocorullo & Della Corte (1999)
    dn/dT = 1.86e-4 K^-1; Bristow et al., APL 90, 191104 (2007) n2 = 4.5e-18 m^2/W.
    """
    u = _check_wl(wavelength_m)
    dn_dt = 1.86e-4
    if fixed_1550_index:
        n = 3.476 + dn_dt * (temperature_k - T_REF_K)
    else:
        x = max(u, 1.12) ** 2
        n0 = math.sqrt(
            1.0
            + 10.6684293 * x / (x - 0.301516485 ** 2)
            + 0.0030434748 * x / (x - 1.13475115 ** 2)
            + 1.54133408 * x / (x - 1104.0 ** 2)
        )
        n = n0 + dn_dt * (temperature_k - T_REF_K)
    return MaterialIndexTensor(
        nx=n, ny=n, nz=n,
        dn_dt_per_k=dn_dt,
        n2_m2_per_w=4.5e-18,
        crystal_symmetry="cubic_m3m",
        validity_um=(1.15, 11.0),
        source="Salzberg & Villa JOSA 1957 + Cocorullo 1999 (dn/dT=1.86e-4 K^-1)",
        is_anisotropic=False,
    )


def n_asi_hydrogenated(wavelength_m: float, temperature_k: float = T_REF_K) -> MaterialIndexTensor:
    """Hydrogenated Amorphous Silicon (a-Si:H) PECVD waveguide film.

    Source: Della Corte et al., JAP 88, 7115 (2000); Kuyken et al., Opt. Express (2011).
    """
    u = max(_check_wl(wavelength_m), 1.20)
    x = u * u
    n0 = math.sqrt(1.0 + 10.90 * x / (x - 0.365 ** 2))
    dn_dt = 2.30e-4
    n = n0 + dn_dt * (temperature_k - T_REF_K)
    return MaterialIndexTensor(
        nx=n, ny=n, nz=n,
        dn_dt_per_k=dn_dt,
        n2_m2_per_w=1.3e-17,
        validity_um=(1.25, 5.5),
        source="PECVD a-Si:H Cauchy/Sellmeier (Della Corte 2000; dn/dT=2.3e-4 K^-1)",
        is_anisotropic=False,
    )


def n_ge_crystalline(wavelength_m: float, temperature_k: float = T_REF_K) -> MaterialIndexTensor:
    """Crystalline Germanium (Ge) Mid-IR waveguide dispersion.

    Source: Barnes & Piltch, JOSA 69, 178 (1979) (valid 2.0 - 14.0 um).
    """
    u = max(_check_wl(wavelength_m), 1.95)
    x = u * u
    n0 = math.sqrt(
        9.28156
        + 6.72880 * x / (x - 0.44105)
        + 0.21307 * x / (x - 3870.1)
    )
    dn_dt = 4.02e-4
    n = n0 + dn_dt * (temperature_k - T_REF_K)
    return MaterialIndexTensor(
        nx=n, ny=n, nz=n,
        dn_dt_per_k=dn_dt,
        n2_m2_per_w=2.5e-17,
        crystal_symmetry="cubic_m3m",
        validity_um=(2.0, 14.0),
        source="Barnes & Piltch JOSA 1979 (Crystalline Ge Mid-IR)",
        is_anisotropic=False,
    )


# ==============================================================================
# 3. Silicon Nitrides & III-Nitrides (Si3N4, SiRich-SiNx, AlN, ScAlN)
# ==============================================================================

def n_sin_lpcvd(wavelength_m: float, temperature_k: float = T_REF_K) -> MaterialIndexTensor:
    """Stoichiometric LPCVD Silicon Nitride (Si3N4 / SiN).

    Source: Luke et al., Opt. Lett. 40, 4823 (2015); Arbabi & Goddard, Opt. Lett. 38,
    3878 (2013) dn/dT = 2.45e-5 K^-1; Ikeda et al. (2008) n2 = 2.4e-19 m^2/W.
    """
    u = _check_wl(wavelength_m)
    x = u * u
    n0 = math.sqrt(
        max(
            1.0
            + 3.0249 * x / (x - 0.1353406 ** 2)
            + 40314.0 * x / (x - 1239.842 ** 2),
            1.0,
        )
    )
    dn_dt = 2.45e-5
    n = n0 + dn_dt * (temperature_k - T_REF_K)
    return MaterialIndexTensor(
        nx=n, ny=n, nz=n,
        dn_dt_per_k=dn_dt,
        n2_m2_per_w=2.4e-19,
        validity_um=(0.31, 5.5),
        source="Luke et al. Opt. Lett. 2015 (LPCVD Si3N4) + Arbabi 2013 (dn/dT=2.45e-5 K^-1)",
        is_anisotropic=False,
    )


def n_sirich_sinx(wavelength_m: float, temperature_k: float = T_REF_K) -> MaterialIndexTensor:
    """Low-stress Silicon-Rich Silicon Nitride (SRN / SiNx, n ~ 2.10 @ 1550 nm).

    Source: Lacava et al., Photonics Res. 5, 151 (2017); Krückel et al., Opt. Express (2015).
    """
    u = max(_check_wl(wavelength_m), 0.55)
    x = u * u
    n0 = math.sqrt(1.0 + 3.320 * x / (x - 0.185 ** 2))
    dn_dt = 3.20e-5
    n = n0 + dn_dt * (temperature_k - T_REF_K)
    return MaterialIndexTensor(
        nx=n, ny=n, nz=n,
        dn_dt_per_k=dn_dt,
        n2_m2_per_w=1.4e-18,
        validity_um=(0.60, 5.0),
        source="Silicon-Rich SiNx (Lacava Photonics Res. 2017; n~2.10@1550nm)",
        is_anisotropic=False,
    )


def n_aln_film(
    wavelength_m: float,
    temperature_k: float = T_REF_K,
    nominal_n_override: float | None = None,
) -> MaterialIndexTensor:
    """Wurtzite c-axis vertical Aluminum Nitride (AlN) uniaxial Sellmeier `[no, ne, no]`.

    Source: Pastrnak & Roskovcova, Phys. Status Solidi 14, K5 (1966);
    Watanabe et al., JAP 104, 103531 (2008) dn/dT = 2.32e-5 K^-1;
    Xiong et al., Nano Lett. 12, 3562 (2012) r33 ~ 1.0 pm/V, r13 ~ 0.67 pm/V.
    """
    u = max(_check_wl(wavelength_m), 0.25)
    dn_dt = 2.32e-5
    if nominal_n_override is not None:
        n = float(nominal_n_override) + dn_dt * (temperature_k - T_REF_K)
        return MaterialIndexTensor(
            nx=n, ny=n, nz=n,
            dn_dt_per_k=dn_dt,
            r33_pm_per_v=1.0,
            r13_pm_per_v=0.67,
            n2_m2_per_w=2.3e-19,
            crystal_symmetry="wurtzite_6mm_scalar_override",
            validity_um=(0.30, 5.2),
            source=f"AlN scalar calibration override n={nominal_n_override:.4f}",
            is_anisotropic=False,
        )
    x = u * u
    no = math.sqrt(1.0 + 3.1399 * x / (x - 0.1362 ** 2)) + dn_dt * (temperature_k - T_REF_K)
    ne = math.sqrt(1.0 + 3.2792 * x / (x - 0.1416 ** 2)) + dn_dt * (temperature_k - T_REF_K)
    return MaterialIndexTensor(
        nx=no, ny=ne, nz=no,
        dn_dt_per_k=dn_dt,
        r33_pm_per_v=1.0,
        r13_pm_per_v=0.67,
        n2_m2_per_w=2.3e-19,
        crystal_symmetry="wurtzite_6mm_c_vertical",
        validity_um=(0.26, 5.2),
        source="Pastrnak & Roskovcova 1966 + Xiong Nano Lett. 2012 (c-axis AlN [no, ne, no])",
        is_anisotropic=True,
    )


def n_scaln_film(
    wavelength_m: float,
    temperature_k: float = T_REF_K,
    sc_fraction: float = 0.20,
) -> MaterialIndexTensor:
    """Wurtzite c-axis Scandium-Doped Aluminum Nitride (Sc_x Al_{1-x} N, 0 <= x <= 0.40).

    Literature parameterization (model input; actual sputtered film index & r_ij depend on
    Sc concentration, stress, and XRD c-axis rocking-curve FWHM):
      - Optical index increase with Sc content x: Baeumler et al., J. Appl. Phys. 126,
        115105 (2019); Wingqvist et al., JAP (2010).
      - Enhanced Pockels r_33(x) trend: Yoshioka et al., APL 123 (2023); Tao et al. (2024).
    """
    if not (0.0 <= sc_fraction <= 0.43):
        raise ValueError("Wurtzite Sc_x Al_{1-x} N sc_fraction x must be in [0.0, 0.43]")
    base = n_aln_film(wavelength_m, temperature_k=T_REF_K)
    u = max(_check_wl(wavelength_m), 0.35)
    # Bandgap redshift with Sc content increases both baseline index and UV pole wavelength
    disp_factor = 1.0 + 0.045 / (u * u)
    delta_no = (0.48 * sc_fraction + 0.22 * (sc_fraction ** 2)) * disp_factor
    # Birefringence (n_e - n_o) softens gradually as c/a ratio decreases with Sc doping
    biref_0 = base.ny - base.nx
    biref_x = biref_0 * max(1.0 - 1.45 * sc_fraction, 0.15)
    dn_dt = 2.32e-5 * (1.0 + 0.65 * sc_fraction)
    dt = temperature_k - T_REF_K

    no = base.nx + delta_no + dn_dt * dt
    ne = no + biref_x
    # Literature nominal Pockels trend (must verify against actual film poling/orientation)
    r33_est = 1.0 + 12.0 * sc_fraction + 45.0 * (sc_fraction ** 2)
    r13_est = 0.67 + 3.5 * sc_fraction + 10.0 * (sc_fraction ** 2)
    return MaterialIndexTensor(
        nx=no, ny=ne, nz=no,
        dn_dt_per_k=dn_dt,
        r33_pm_per_v=r33_est,
        r13_pm_per_v=r13_est,
        n2_m2_per_w=3.5e-19,
        crystal_symmetry=f"wurtzite_6mm_c_vertical_Sc{int(round(sc_fraction*100)):02d}",
        validity_um=(0.38, 5.0),
        source=f"Baeumler JAP 2019 / Yoshioka APL 2023 nominal Sc_{sc_fraction:.2f}Al_{1-sc_fraction:.2f}N (literature model)",
        is_anisotropic=True,
    )


# ==============================================================================
# 4. Silicon Carbides (4H-SiC Uniaxial & 3C-SiC Cubic)
# ==============================================================================

def n_4h_sic_anisotropic(wavelength_m: float, temperature_k: float = T_REF_K) -> MaterialIndexTensor:
    """4H-SiC uniaxial Sellmeier dispersion in c-axis-vertical local coordinates `[no, ne, no]`.

    Source: Wang et al., Opt. Lett. 38, 23 (2013);
    Li et al., PR Applied 2023 (n2 = 8.9e-19 m^2/W); Sato et al. (r33 ~ 2.7 pm/V).
    """
    u = max(_check_wl(wavelength_m), 0.38)
    x = u * u
    no = math.sqrt(
        1.0
        + 0.20075 * x / (x + 12.07224)
        + 5.54861 * x / (x - 0.02641)
        + 35.65066 * x / (x - 1268.24708)
    )
    ne = math.sqrt(6.79485 + 0.15558 / (x - 0.03535) - 0.02296 * x)
    dn_dt = 3.9e-5
    if abs(temperature_k - T_REF_K) > 1e-9:
        no += dn_dt * (temperature_k - T_REF_K)
        ne += dn_dt * (temperature_k - T_REF_K)
    return MaterialIndexTensor(
        nx=no, ny=ne, nz=no,
        dn_dt_per_k=dn_dt,
        r33_pm_per_v=2.7,
        r13_pm_per_v=1.0,
        n2_m2_per_w=8.9e-19,
        crystal_symmetry="hexagonal_6mm_c_vertical",
        validity_um=(0.40, 5.2),
        source="Wang et al. Opt. Lett. 38, 23 (2013) uniaxial 4H-SiC [no, ne, no]",
        is_anisotropic=True,
    )


def n_3c_sic(wavelength_m: float, temperature_k: float = T_REF_K) -> MaterialIndexTensor:
    """Cubic 3C-SiC isotropic Sellmeier dispersion.

    Source: Shaffer, Appl. Opt. 10, 1034 (1971); Wang et al., Opt. Lett. 38 (2013).
    """
    u = max(_check_wl(wavelength_m), 0.46)
    x = u * u
    n0 = math.sqrt(1.0 + 5.5515 * x / (x - 0.1625 ** 2))
    dn_dt = 3.8e-5
    n = n0 + dn_dt * (temperature_k - T_REF_K)
    return MaterialIndexTensor(
        nx=n, ny=n, nz=n,
        dn_dt_per_k=dn_dt,
        r33_pm_per_v=2.7,  # r_41 in zincblende 3C-SiC
        n2_m2_per_w=6.0e-19,
        crystal_symmetry="zincblende_43m",
        validity_um=(0.48, 5.0),
        source="Shaffer 1971 / Wang Opt. Lett. 2013 (Cubic 3C-SiC)",
        is_anisotropic=False,
    )


# ==============================================================================
# 5. Thin-Film Lithium Niobate (LiNbO3 / TFLN: Z-cut & X-cut)
# ==============================================================================

def _linbo3_no_ne(wavelength_m: float, temperature_k: float = T_REF_K) -> tuple[float, float]:
    """Congruent Lithium Niobate (LiNbO3) ordinary & extraordinary indices.

    Source: Zelmon, Small & Jundt, JOSA B 14, 3319 (1997) (valid 0.4 - 5.0 um).
    """
    u = max(_check_wl(wavelength_m), 0.38)
    x = u * u
    no = math.sqrt(
        max(
            1.0
            + 2.6734 * x / (x - 0.01764)
            + 1.2290 * x / (x - 0.05914)
            + 12.614 * x / (x - 474.60),
            1.0,
        )
    )
    ne = math.sqrt(
        max(
            1.0
            + 2.9804 * x / (x - 0.02047)
            + 0.5981 * x / (x - 0.0666)
            + 8.9543 * x / (x - 416.08),
            1.0,
        )
    )
    dt = temperature_k - T_REF_K
    no += 0.40e-5 * dt
    ne += 3.70e-5 * dt
    return no, ne


def n_linbo3_zcut(wavelength_m: float, temperature_k: float = T_REF_K) -> MaterialIndexTensor:
    """Z-cut Thin-Film Lithium Niobate (TFLN): optic Z-axis vertical `[no, ne, no]`.

    In Z-cut TFLN rings, cylindrical symmetry is preserved around 360 deg:
      - TM modes see n_e and strong vertical Pockels r_33 = 30.9 pm/V
      - TE modes see n_o and vertical Pockels r_13 = 9.6 pm/V.
    """
    no, ne = _linbo3_no_ne(wavelength_m, temperature_k)
    return MaterialIndexTensor(
        nx=no, ny=ne, nz=no,
        dn_dt_per_k=3.70e-5,
        r33_pm_per_v=30.9,
        r13_pm_per_v=9.6,
        n2_m2_per_w=1.8e-19,
        crystal_symmetry="trigonal_3m_Zcut_vertical",
        validity_um=(0.40, 5.0),
        source="Zelmon et al. JOSA B 1997 (Congruent Z-cut TFLN [no, ne, no])",
        is_anisotropic=True,
    )


def n_linbo3_xcut(
    wavelength_m: float,
    temperature_k: float = T_REF_K,
    inplane_propagation_angle_deg: float = 0.0,
) -> MaterialIndexTensor:
    """X-cut Thin-Film Lithium Niobate (TFLN): optic Z-axis in wafer plane.

    Convention (`inplane_propagation_angle_deg = 0` = Y-propagating straight section,
    standard for X-cut TFLN push-pull modulators & racetrack straight arms):
      - Horizontal x-axis is crystal Z-axis (`n_x = n_e`, enabling TE mode `r_33 = 30.9 pm/V`!)
      - Vertical y-axis is crystal X-axis (`n_y = n_o`)
      - Propagation z-axis is crystal Y-axis (`n_z = n_o`).
    For arbitrary in-plane propagation angle `phi` (e.g. along a bend), the in-plane
    transverse extraordinary-ordinary index ellipse gives:
      1 / n_horiz(phi)^2 = cos^2(phi) / n_e^2 + sin^2(phi) / n_o^2.
    """
    no, ne = _linbo3_no_ne(wavelength_m, temperature_k)
    phi = math.radians(inplane_propagation_angle_deg)
    c2 = math.cos(phi) ** 2
    s2 = math.sin(phi) ** 2
    nx_eff = 1.0 / math.sqrt(c2 / (ne * ne) + s2 / (no * no))
    nz_eff = 1.0 / math.sqrt(s2 / (ne * ne) + c2 / (no * no))
    return MaterialIndexTensor(
        nx=nx_eff, ny=no, nz=nz_eff,
        dn_dt_per_k=3.70e-5 * c2 + 0.40e-5 * s2,
        r33_pm_per_v=30.9,
        r13_pm_per_v=9.6,
        n2_m2_per_w=1.8e-19,
        crystal_symmetry="trigonal_3m_Xcut_inplane",
        validity_um=(0.40, 5.0),
        source="Zelmon et al. JOSA B 1997 (Congruent X-cut TFLN, TE sees r33 along straight Y-arm)",
        is_anisotropic=True,
    )


# ==============================================================================
# 6. Active Phase-Change Materials (Low-Loss Chalcogenide GSST)
# ==============================================================================

def n_gsst_pcm(wavelength_m: float, state: str = "amorphous") -> MaterialIndexTensor:
    """Published Ge2Sb2Se4Te1 (GSST) low-loss optical phase-change material model.

    Source: Zhang et al., Nature Communications 10, 4279 (2019).
    """
    u = _check_wl(wavelength_m)
    n_amorphous = 3.32 - 0.025 * np.clip(u - 1.55, 0.0, 4.0)
    if state == "amorphous":
        return MaterialIndexTensor(
            nx=float(n_amorphous), ny=float(n_amorphous), nz=float(n_amorphous),
            kx=0.0, ky=0.0, kz=0.0,
            dn_dt_per_k=5.0e-5,
            validity_um=(1.5, 10.0),
            source="Zhang et al. Nat. Commun. 2019 (Amorphous GSST low-loss PCM)",
            is_anisotropic=False,
        )
    if state == "crystalline":
        # Crystalline GSST: n_c ~ 5.08 (k_c ~ 0.35 at 1.55 um, dropping to ~0.015 in Mid-IR)
        nc = 5.08 - 0.04 * np.clip(u - 1.55, 0.0, 4.0)
        kc = 0.35 * math.exp(-max(u - 1.55, 0.0) / 0.85) + 0.015
        return MaterialIndexTensor(
            nx=float(nc), ny=float(nc), nz=float(nc),
            kx=float(kc), ky=float(kc), kz=float(kc),
            dn_dt_per_k=8.0e-5,
            validity_um=(1.5, 10.0),
            source="Zhang et al. Nat. Commun. 2019 (Crystalline GSST PCM)",
            is_anisotropic=False,
        )
    raise ValueError(f"Unknown PCM state '{state}'; expected 'amorphous' or 'crystalline'")


# Published GSST phase-change material model above


# ==============================================================================
# 7. Unified Material Catalog & Lookup API for UI / Scripting
# ==============================================================================

MATERIAL_CATALOG: dict[str, dict] = {
    "Si": {
        "name": "Silicon (c-Si, SOI)",
        "category": "Group IV",
        "default_band_nm": 1550.0,
        "typical_loss_db_cm": 1.5,
        "fn": lambda wl, t=T_REF_K: n_si_crystalline(wl, t, fixed_1550_index=False),
    },
    "a-Si": {
        "name": "Amorphous Silicon (a-Si:H)",
        "category": "Group IV",
        "default_band_nm": 1550.0,
        "typical_loss_db_cm": 3.0,
        "fn": n_asi_hydrogenated,
    },
    "Si3N4": {
        "name": "Silicon Nitride (LPCVD Si3N4)",
        "category": "Nitride",
        "default_band_nm": 1550.0,
        "typical_loss_db_cm": 0.15,
        "fn": n_sin_lpcvd,
    },
    "SiRich_SiNx": {
        "name": "Silicon-Rich Nitride (SRN SiNx)",
        "category": "Nitride",
        "default_band_nm": 1550.0,
        "typical_loss_db_cm": 0.80,
        "fn": n_sirich_sinx,
    },
    "4H-SiC": {
        "name": "4H-Silicon Carbide (4H-SiC c-cut)",
        "category": "Carbide",
        "default_band_nm": 1550.0,
        "typical_loss_db_cm": 0.30,
        "fn": n_4h_sic_anisotropic,
    },
    "3C-SiC": {
        "name": "3C-Silicon Carbide (Cubic 3C-SiC)",
        "category": "Carbide",
        "default_band_nm": 1550.0,
        "typical_loss_db_cm": 0.80,
        "fn": n_3c_sic,
    },
    "AlN": {
        "name": "Aluminum Nitride (c-axis AlN)",
        "category": "III-Nitride",
        "default_band_nm": 1550.0,
        "typical_loss_db_cm": 0.60,
        "fn": lambda wl, t=T_REF_K: n_aln_film(wl, t),
    },
    "ScAlN_10": {
        "name": "Sc0.10Al0.90N (10% Sc-doped AlN)",
        "category": "III-Nitride",
        "default_band_nm": 1550.0,
        "typical_loss_db_cm": 1.20,
        "fn": lambda wl, t=T_REF_K: n_scaln_film(wl, t, sc_fraction=0.10),
    },
    "ScAlN_20": {
        "name": "Sc0.20Al0.80N (20% Sc-doped AlN)",
        "category": "III-Nitride",
        "default_band_nm": 1550.0,
        "typical_loss_db_cm": 1.80,
        "fn": lambda wl, t=T_REF_K: n_scaln_film(wl, t, sc_fraction=0.20),
    },
    "ScAlN_30": {
        "name": "Sc0.30Al0.70N (30% Sc-doped AlN)",
        "category": "III-Nitride",
        "default_band_nm": 1550.0,
        "typical_loss_db_cm": 2.50,
        "fn": lambda wl, t=T_REF_K: n_scaln_film(wl, t, sc_fraction=0.30),
    },
    "LN_Zcut": {
        "name": "Lithium Niobate (TFLN Z-cut)",
        "category": "Ferroelectric",
        "default_band_nm": 1550.0,
        "typical_loss_db_cm": 0.10,
        "fn": n_linbo3_zcut,
    },
    "LN_Xcut": {
        "name": "Lithium Niobate (TFLN X-cut, Y-prop)",
        "category": "Ferroelectric",
        "default_band_nm": 1550.0,
        "typical_loss_db_cm": 0.10,
        "fn": lambda wl, t=T_REF_K: n_linbo3_xcut(wl, t, inplane_propagation_angle_deg=0.0),
    },
    "Ge": {
        "name": "Germanium (c-Ge Mid-IR)",
        "category": "Group IV",
        "default_band_nm": 4200.0,
        "typical_loss_db_cm": 2.0,
        "fn": n_ge_crystalline,
    },
    "Al2O3": {
        "name": "Alumina / Sapphire (Al2O3)",
        "category": "Dielectric",
        "default_band_nm": 1550.0,
        "typical_loss_db_cm": 0.20,
        "fn": n_al2o3_sapphire,
    },
    "SiO2": {
        "name": "Fused Silica (SiO2 BOX/Clad)",
        "category": "Dielectric",
        "default_band_nm": 1550.0,
        "typical_loss_db_cm": 0.01,
        "fn": n_sio2_sellmeier,
    },
    "GSST_amorphous": {
        "name": "GSST PCM (Amorphous Low-Loss)",
        "category": "Phase-Change",
        "default_band_nm": 1550.0,
        "typical_loss_db_cm": 0.50,
        "fn": lambda wl, t=T_REF_K: n_gsst_pcm(wl, state="amorphous"),
    },
    "GSST_crystalline": {
        "name": "GSST PCM (Crystalline High-Index)",
        "category": "Phase-Change",
        "default_band_nm": 1550.0,
        "typical_loss_db_cm": 150.0,
        "fn": lambda wl, t=T_REF_K: n_gsst_pcm(wl, state="crystalline"),
    },
    "Air": {
        "name": "Air / Vacuum (n = 1.0)",
        "category": "Cladding",
        "default_band_nm": 1550.0,
        "typical_loss_db_cm": 0.0,
        "fn": n_air,
    },
}


def get_material_fn(
    material_key: str,
    *,
    sc_fraction: float | None = None,
    custom_n: float | None = None,
    custom_k: float = 0.0,
    custom_dn_dt: float = 1.0e-5,
    custom_r33_pm_v: float = 0.0,
) -> Callable[[float, float], MaterialIndexTensor]:
    """Return `(wavelength_m, temperature_k) -> MaterialIndexTensor` callable for any catalog or custom material."""
    if material_key == "Custom" or custom_n is not None:
        n_base = float(2.0 if custom_n is None else custom_n)

        def _custom_fn(wl_m: float, temp_k: float = T_REF_K) -> MaterialIndexTensor:
            _ = _check_wl(wl_m)
            n_val = n_base + custom_dn_dt * (temp_k - T_REF_K)
            return MaterialIndexTensor(
                nx=n_val, ny=n_val, nz=n_val,
                kx=custom_k, ky=custom_k, kz=custom_k,
                dn_dt_per_k=custom_dn_dt,
                r33_pm_per_v=custom_r33_pm_v,
                source=f"User Custom Material (n={n_base:.4f}, k={custom_k:.4g})",
                is_anisotropic=False,
            )

        return _custom_fn

    if material_key.startswith("ScAlN") and sc_fraction is not None:
        x_sc = float(sc_fraction)
        return lambda wl_m, temp_k=T_REF_K: n_scaln_film(wl_m, temp_k, sc_fraction=x_sc)

    if material_key not in MATERIAL_CATALOG:
        raise KeyError(f"Unknown material '{material_key}'. Available: {list(MATERIAL_CATALOG)}")
    return MATERIAL_CATALOG[material_key]["fn"]


def evaluate_material_dispersion_table(
    material_key: str,
    wavelength_min_nm: float = 450.0,
    wavelength_max_nm: float = 4500.0,
    num_points: int = 120,
    temperature_k: float = T_REF_K,
    sc_fraction: float | None = None,
) -> dict:
    """Evaluate dispersion curves (nx, ny, nz, ng_x, ng_y) across a wavelength span."""
    fn = get_material_fn(material_key, sc_fraction=sc_fraction)
    # Clip range safely to material validity window
    probe = fn(1.55e-6, temperature_k)
    vmin_nm = max(wavelength_min_nm, probe.validity_um[0] * 1e3 * 1.02)
    vmax_nm = min(wavelength_max_nm, probe.validity_um[1] * 1e3 * 0.99)
    if vmax_nm <= vmin_nm:
        vmin_nm, vmax_nm = probe.validity_um[0] * 1e3 * 1.05, probe.validity_um[1] * 1e3 * 0.98

    wls_nm = np.linspace(vmin_nm, vmax_nm, num_points)
    nx_arr, ny_arr, nz_arr, kx_arr = [], [], [], []
    for w_nm in wls_nm:
        t = fn(float(w_nm) * 1e-9, temperature_k)
        nx_arr.append(t.nx)
        ny_arr.append(t.ny)
        nz_arr.append(t.nz)
        kx_arr.append(t.kx)

    nx_np = np.asarray(nx_arr, dtype=float)
    ny_np = np.asarray(ny_arr, dtype=float)
    dnx_dl = np.gradient(nx_np, wls_nm)
    dny_dl = np.gradient(ny_np, wls_nm)
    ngx_np = nx_np - wls_nm * dnx_dl
    ngy_np = ny_np - wls_nm * dny_dl

    ref_1550 = fn(1.55e-6 if probe.validity_um[0] <= 1.55 <= probe.validity_um[1] else (0.5 * (vmin_nm + vmax_nm) * 1e-9), temperature_k)
    return {
        "material_key": material_key,
        "display_name": MATERIAL_CATALOG.get(material_key, {}).get("name", material_key),
        "wavelength_nm": np.round(wls_nm, 3).tolist(),
        "nx": np.round(nx_np, 6).tolist(),
        "ny": np.round(ny_np, 6).tolist(),
        "nz": np.round(nz_arr, 6).tolist(),
        "kx": np.round(kx_arr, 6).tolist(),
        "ng_x": np.round(ngx_np, 6).tolist(),
        "ng_y": np.round(ngy_np, 6).tolist(),
        "properties_at_ref": ref_1550.to_dict(),
    }
