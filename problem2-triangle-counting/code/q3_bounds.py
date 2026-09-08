from math import comb


def ceil_div(a, b):
    """Return ceil(a / b), assuming b > 0."""
    if b <= 0:
        raise ValueError("b must be positive")
    return -((-a) // b)


def validate_parameters(n, k, d):
    if n < 9:
        raise ValueError("n must satisfy n >= 9")
    if not (0 <= d <= n - 1):
        raise ValueError("d must satisfy 0 <= d <= n - 1")
    if not (0 <= k <= comb(n, 3)):
        raise ValueError("k must satisfy 0 <= k <= C(n, 3)")


def degree_lower_bounds(n, d):
    """
    Return degree lower bounds imposed by delta(G) >= d and H0.

    Forced edges:
        01, 02, 03, 04, 56, 78.

    The bounds are sorted in descending order because compute_U
    fills coordinates with larger initial lower bounds first.
    """
    if n < 9:
        raise ValueError("n must satisfy n >= 9")
    if not (0 <= d <= n - 1):
        raise ValueError("d must satisfy 0 <= d <= n - 1")

    ell = [max(d, 4)]
    ell.extend([max(d, 1)] * 8)
    ell.extend([d] * (n - 9))

    return sorted(ell, reverse=True)


def handshake_bound(n, d):
    return ceil_div(n * d, 2)


def forced_degree_gap_bound(n, d):
    gap = (
        max(d - 4, 0)
        + 8 * max(d - 1, 0)
        + (n - 9) * d
    )
    return 6 + ceil_div(gap, 2)


def triangle_edge_bound(n, k):
    return ceil_div(3 * k, n - 2)


def triangle_nonforced_edge_bound(n, k):
    return 6 + ceil_div(k, n - 2)


def kk_triangle_max_for_edges(m):
    """
    Kruskal-Katona upper bound for the number of triangles.

    Write m = C(a,2) + b with 0 <= b < a.
    The maximum number of triangles is C(a,3) + C(b,2).
    """
    if m < 0:
        raise ValueError("m must be nonnegative")

    a = 1

    while comb(a + 1, 2) <= m:
        a += 1

    b = m - comb(a, 2)

    if not (0 <= b < a):
        raise RuntimeError("invalid Kruskal-Katona decomposition")

    return comb(a, 3) + comb(b, 2)


def compute_L_KK(n, k):
    """
    Compute the KK lower bound subject to m <= C(n,2).

    Abstractly, the KK lower bound depends on k. The parameter n is
    used here to enforce the edge limit of an n-vertex graph.
    """
    if n < 1:
        raise ValueError("n must be positive")
    if k < 0:
        raise ValueError("k must be nonnegative")

    for m in range(comb(n, 2) + 1):
        if kk_triangle_max_for_edges(m) >= k:
            return m

    return float("inf")


def compute_U(n, d, m, return_vector=False):
    """
    Compute the relaxed maximum

        U(n,d,m) = max sum_i C(x_i,2),

    subject to

        ell_i <= x_i <= n-1,
        sum_i x_i = 2m.

    The maximizing vector need not be graphical.
    """
    if n < 9:
        raise ValueError("n must satisfy n >= 9")
    if not (0 <= d <= n - 1):
        raise ValueError("d must satisfy 0 <= d <= n - 1")
    if not (0 <= m <= comb(n, 2)):
        return None

    ell = degree_lower_bounds(n, d)
    total_degree = 2 * m
    lower_sum = sum(ell)

    if total_degree < lower_sum:
        return None

    if total_degree > n * (n - 1):
        return None

    x = ell[:]
    remaining = total_degree - lower_sum

    # ell is descending, so larger lower bounds are filled first.
    for i in range(n):
        capacity = n - 1 - x[i]
        added = min(remaining, capacity)

        x[i] += added
        remaining -= added

        if remaining == 0:
            break

    if remaining != 0:
        return None

    value = sum(comb(x_i, 2) for x_i in x)

    if return_vector:
        return value, x

    return value


def compute_L_DT(n, k, d):
    """
    Compute

        L_DT(n,k,d) = min {m : U(n,d,m) >= 3k}.
    """
    validate_parameters(n, k, d)

    ell = degree_lower_bounds(n, d)

    first_m = max(
        6,
        ceil_div(sum(ell), 2),
    )

    for m in range(first_m, comb(n, 2) + 1):
        value = compute_U(n, d, m)

        if value is not None and value >= 3 * k:
            return m

    return float("inf")


def compute_lower_bounds(n, k, d):
    """
    Compute the six theoretical lower bounds and their maximum.
    """
    validate_parameters(n, k, d)

    bounds = {
        "handshake":
            handshake_bound(n, d),

        "forced_degree_gap":
            forced_degree_gap_bound(n, d),

        "triangle_edge":
            triangle_edge_bound(n, k),

        "triangle_nonforced_edge":
            triangle_nonforced_edge_bound(n, k),

        "Kruskal_Katona":
            compute_L_KK(n, k),

        "degree_triangle":
            compute_L_DT(n, k, d),
    }

    bounds["combined"] = max(bounds.values())

    return bounds


def print_bounds(n, k, d):
    print("=" * 64)
    print(f"n={n}, k={k}, d={d}")

    bounds = compute_lower_bounds(n, k, d)

    for name, value in bounds.items():
        print(f"{name:28s}: {value}")


def demo():
    print_bounds(9, 11, 3)

    print()

    for m in (14, 15):
        result = compute_U(
            9,
            3,
            m,
            return_vector=True,
        )

        value, vector = result

        print(f"U(9,3,{m}) = {value}")
        print(f"relaxed vector = {vector}")


if __name__ == "__main__":
    demo()
