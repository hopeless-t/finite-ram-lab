from __future__ import annotations

from dataclasses import dataclass

PAD_SIZE = 256
BLAS_WORKSPACE_BYTES = 32 << 20
GROUPED_CRT_MAX_ELEMENTS = 8192 * 8192
UINT32_MAX = (1 << 32) - 1

# RIKEN-RCCS/GEMMul8 @ 603b52363715796a0af5e4aa1ed8d386349b4251
INT8_REAL_MODULI = (
    256, 255, 253, 251, 247, 241, 239, 233, 229, 227,
    223, 217, 211, 199, 197, 193, 191, 181, 179, 173,
)


def pad(n: int) -> int:
    if type(n) is not int or n < 0:
        raise ValueError("dimension_invalid")
    return PAD_SIZE * ((n + PAD_SIZE - 1) // PAD_SIZE)


def int8_real_crt_groups(num_moduli: int) -> tuple[tuple[int, int], ...]:
    if type(num_moduli) is not int or not 1 <= num_moduli <= len(INT8_REAL_MODULI):
        raise ValueError("num_moduli_invalid")
    groups: list[tuple[int, int]] = []
    first = 0
    while first < num_moduli:
        end = first
        product = 1
        while (
            end < num_moduli
            and end < first + 4
            and product * INT8_REAL_MODULI[end] <= UINT32_MAX
        ):
            product *= INT8_REAL_MODULI[end]
            end += 1
        if end == first:
            raise AssertionError("empty_crt_group")
        groups.append((first, end))
        first = end
    return tuple(groups)


@dataclass(frozen=True)
class Gemmul8Int8RealWorkspace:
    m: int
    n: int
    k: int
    num_moduli: int
    fastmode: bool = True
    enable_skip_scal_a: bool = False
    enable_skip_scal_b: bool = False

    @property
    def m_pad(self) -> int:
        return pad(self.m)

    @property
    def n_pad(self) -> int:
        return pad(self.n)

    @property
    def k_pad(self) -> int:
        return pad(self.k)

    @property
    def size_a(self) -> int:
        return self.k_pad * self.m_pad

    @property
    def size_b(self) -> int:
        # GEMM n_work == n in the source.
        return self.k_pad * self.n

    @property
    def size_c(self) -> int:
        return self.m_pad * self.n

    def _num_low_planes(self, skip_enabled: bool) -> int:
        return self.num_moduli + int(skip_enabled and not self.fastmode)

    @property
    def work_a_bytes(self) -> int:
        low_planes = self._num_low_planes(self.enable_skip_scal_a)
        shift_planes = 2 if self.enable_skip_scal_a and not self.fastmode else 1
        # INT8 low_t = int8_t, shift type = int16_t.
        return (
            PAD_SIZE - 1
            + self.size_a * low_planes
            + 2 * self.m_pad * shift_planes
        )

    @property
    def work_b_bytes(self) -> int:
        low_planes = self._num_low_planes(self.enable_skip_scal_b)
        shift_planes = 2 if self.enable_skip_scal_b and not self.fastmode else 1
        return (
            PAD_SIZE - 1
            + self.size_b * low_planes
            + 2 * self.n_pad * shift_planes
        )

    @property
    def grouped_crt(self) -> bool:
        return self.size_c <= GROUPED_CRT_MAX_ELEMENTS

    @property
    def product_workspace_bytes(self) -> int:
        """Mirror product_workspace<INT8, real>::bytes for GEMM.

        INT8 real source types:
        - low_t = int8_t
        - mid_t = int8_t
        - hi_t = int32_t
        - no FP8 pointer arrays
        - one product plane per modulus
        """
        size_c = self.size_c

        # Accurate mode can use a high-precision norm workspace before products.
        result = 0 if self.fastmode else 4 * size_c + BLAS_WORKSPACE_BYTES

        grouped_size = min(size_c, GROUPED_CRT_MAX_ELEMENTS)
        group_bytes = 4 * grouped_size

        groups = int8_real_crt_groups(self.num_moduli)
        for group_index, (first, end) in enumerate(groups):
            count = end - first
            gap = max(group_bytes, BLAS_WORKSPACE_BYTES)
            candidate = (
                group_index * group_bytes
                + gap
                + 4 * grouped_size * count
            )
            result = max(result, candidate)

        if self.grouped_crt:
            return result

        # Non-grouped path: prior C_mid residues occupy one int8 plane each.
        mid_bytes = size_c
        for i in range(self.num_moduli):
            gap = max(
                BLAS_WORKSPACE_BYTES,
                mid_bytes if i + 1 < self.num_moduli else 0,
            )
            candidate = i * mid_bytes + gap + 4 * size_c
            result = max(result, candidate)

        return result

    @property
    def work_c_bytes(self) -> int:
        return PAD_SIZE - 1 + self.product_workspace_bytes

    @property
    def total_workspace_bytes(self) -> int:
        return self.work_a_bytes + self.work_b_bytes + self.work_c_bytes

    def source_trace(self) -> dict[str, object]:
        groups = int8_real_crt_groups(self.num_moduli)
        return {
            "source_pin": "RIKEN-RCCS/GEMMul8@603b52363715796a0af5e4aa1ed8d386349b4251",
            "backend": "INT8",
            "complex": False,
            "operation": "GEMM",
            "m": self.m,
            "n": self.n,
            "k": self.k,
            "num_moduli": self.num_moduli,
            "fastmode": self.fastmode,
            "grouped_crt": self.grouped_crt,
            "crt_groups": [list(group) for group in groups],
            "a_low_plane_count": self._num_low_planes(self.enable_skip_scal_a),
            "b_low_plane_count": self._num_low_planes(self.enable_skip_scal_b),
            "work_a_bytes": self.work_a_bytes,
            "work_b_bytes": self.work_b_bytes,
            "work_c_bytes": self.work_c_bytes,
            "total_workspace_bytes": self.total_workspace_bytes,
            "source_backed_liveness": {
                "A_lo": "all num_mat planes are allocated before product loop",
                "B_lo": "all num_mat planes are allocated before product loop",
                "C_products": "high product planes are temporary per batch/group",
                "C_reduced": (
                    "prior grouped CRT results remain as uint32 group planes"
                    if self.grouped_crt
                    else "prior modulus residues remain as int8 C_mid planes"
                ),
                "last_group": "kept as high product tail and fused into final CRT when supported",
            },
        }
