import argparse
from itertools import combinations
from math import comb

from ortools.sat.python import cp_model

from bounds import compute_lower_bounds


FORCED_EDGES = {
    (0, 1),
    (0, 2),
    (0, 3),
    (0, 4),
    (5, 6),
    (7, 8),
}


def normalize_edge(u, v):
    if u == v:
        raise ValueError("loops are not allowed")

    return (u, v) if u < v else (v, u)


def check_graph(n, edges, k, d, verbose=True):
    """
    Independently verify a candidate graph.

    Checks endpoints, loops, duplicate edges, forced edges,
    minimum degree, and the number of triangles.
    """
    edge_set = set()

    for u, v in edges:
        if not (0 <= u < n and 0 <= v < n):
            if verbose:
                print("Invalid endpoint:", (u, v))
            return False

        if u == v:
            if verbose:
                print("Loop found:", (u, v))
            return False

        normalized = normalize_edge(u, v)

        if normalized in edge_set:
            if verbose:
                print("Duplicate edge:", (u, v))
            return False

        edge_set.add(normalized)

    missing_forced = FORCED_EDGES - edge_set

    degrees = [0] * n

    for u, v in edge_set:
        degrees[u] += 1
        degrees[v] += 1

    minimum_degree = min(degrees)

    triangle_count = 0

    for a, b, c in combinations(range(n), 3):
        if (
            (a, b) in edge_set
            and (a, c) in edge_set
            and (b, c) in edge_set
        ):
            triangle_count += 1

    valid = (
        not missing_forced
        and minimum_degree >= d
        and triangle_count >= k
    )

    if verbose:
        print("Actual edge count:", len(edge_set))
        print("Degrees:", degrees)
        print("Minimum degree:", minimum_degree)
        print("Triangle count:", triangle_count)
        print("Missing forced edges:", sorted(missing_forced))
        print("Minimum-degree condition:", minimum_degree >= d)
        print("Triangle condition:", triangle_count >= k)
        print("Verified:", valid)

    return valid


def search_at_most(n, k, d, max_edges, time_limit):
    """
    Search for a graph satisfying

        H0 subset of G,
        delta(G) >= d,
        t(G) >= k,
        e(G) <= max_edges.
    """
    model = cp_model.CpModel()
    all_edges = list(combinations(range(n), 2))

    x = {
        edge: model.NewBoolVar(f"x_{edge[0]}_{edge[1]}")
        for edge in all_edges
    }

    for edge in FORCED_EDGES:
        normalized = normalize_edge(*edge)

        if normalized not in x:
            raise ValueError(
                f"forced edge {normalized} is outside the vertex set"
            )

        model.Add(x[normalized] == 1)

    model.Add(sum(x.values()) <= max_edges)

    for v in range(n):
        incident_edges = [
            x[normalize_edge(u, v)]
            for u in range(n)
            if u != v
        ]

        model.Add(sum(incident_edges) >= d)

    triangle_variables = []

    for a, b, c in combinations(range(n), 3):
        ab = x[(a, b)]
        ac = x[(a, c)]
        bc = x[(b, c)]

        triangle = model.NewBoolVar(
            f"triangle_{a}_{b}_{c}"
        )

        triangle_variables.append(triangle)

        model.Add(triangle <= ab)
        model.Add(triangle <= ac)
        model.Add(triangle <= bc)
        model.Add(triangle >= ab + ac + bc - 2)

    model.Add(sum(triangle_variables) >= k)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_search_workers = 8

    status = solver.Solve(model)
    status_name = solver.StatusName(status)

    if status not in (
        cp_model.OPTIMAL,
        cp_model.FEASIBLE,
    ):
        return status_name, None

    edge_list = [
        edge
        for edge in all_edges
        if solver.Value(x[edge]) == 1
    ]

    return status_name, edge_list


def search_from_bound(n, k, d, start_bound, time_limit):
    """
    Search cumulative edge bounds beginning at start_bound.

    INFEASIBLE at m excludes all legal graphs with e(G) <= m.
    UNKNOWN or any unhandled status stops the search.
    """
    for m in range(start_bound, comb(n, 2) + 1):
        print()
        print("-" * 64)
        print(f"Searching for a graph with e(G) <= {m}")

        status_name, edge_list = search_at_most(
            n=n,
            k=k,
            d=d,
            max_edges=m,
            time_limit=time_limit,
        )

        print("Solver status:", status_name)

        if status_name in ("OPTIMAL", "FEASIBLE"):
            print("A candidate witness was found.")
            return status_name, m, edge_list

        if status_name == "INFEASIBLE":
            print(
                f"No graph with e(G) <= {m} exists in this model."
            )
            continue

        if status_name == "UNKNOWN":
            print(
                "The search did not finish. No feasibility or "
                "infeasibility conclusion can be made."
            )
        else:
            print(f"Unhandled solver status: {status_name}")

        return status_name, m, None

    return "NOT_FOUND", None, None


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=(
            "Search for a legal graph under cumulative edge bounds."
        )
    )

    parser.add_argument("--n", type=int, default=9)
    parser.add_argument("--k", type=int, default=11)
    parser.add_argument("--d", type=int, default=3)

    parser.add_argument(
        "--lower-bound",
        type=int,
        default=None,
        help=(
            "Initial cumulative edge bound. If omitted, the combined "
            "theoretical lower bound is used."
        ),
    )

    parser.add_argument(
        "--time-limit",
        type=float,
        default=60.0,
        help="Time limit in seconds for each cumulative bound.",
    )

    return parser.parse_args()


def validate_arguments(args):
    if args.n < 9:
        raise ValueError("n must satisfy n >= 9")

    if not (0 <= args.d <= args.n - 1):
        raise ValueError("d must satisfy 0 <= d <= n - 1")

    if not (0 <= args.k <= comb(args.n, 3)):
        raise ValueError("k must satisfy 0 <= k <= C(n,3)")

    if args.time_limit <= 0:
        raise ValueError("time-limit must be positive")

    if args.lower_bound is not None:
        if not (0 <= args.lower_bound <= comb(args.n, 2)):
            raise ValueError(
                "lower-bound must satisfy "
                "0 <= lower-bound <= C(n,2)"
            )


def main():
    args = parse_arguments()
    validate_arguments(args)

    bounds = compute_lower_bounds(
        args.n,
        args.k,
        args.d,
    )

    theoretical_lower_bound = bounds["combined"]

    if args.lower_bound is None:
        search_start = theoretical_lower_bound
    else:
        search_start = args.lower_bound

    print("Parameters")
    print(f"n = {args.n}")
    print(f"k = {args.k}")
    print(f"d = {args.d}")
    print(
        "Combined theoretical lower bound = "
        f"{theoretical_lower_bound}"
    )
    print(f"Search starts at = {search_start}")
    print(
        "Time limit per cumulative bound = "
        f"{args.time_limit} seconds"
    )

    if search_start < theoretical_lower_bound:
        print()
        print(
            "Warning: the selected start is below the known "
            "theoretical lower bound."
        )

    if search_start > theoretical_lower_bound:
        print()
        print(
            "Warning: cumulative bounds between the theoretical "
            "lower bound and the selected start will be skipped."
        )

    status_name, tested_bound, edge_list = search_from_bound(
        n=args.n,
        k=args.k,
        d=args.d,
        start_bound=search_start,
        time_limit=args.time_limit,
    )

    print()
    print("=" * 64)
    print("Final solver status:", status_name)

    if edge_list is None:
        print("No independently verifiable witness was produced.")
        return

    actual_edge_count = len(edge_list)

    print("Tested cumulative bound:", tested_bound)
    print("Actual edge count:", actual_edge_count)
    print("Edges:")
    print(sorted(edge_list))

    print()
    print("Independent verification")

    verified = check_graph(
        n=args.n,
        edges=edge_list,
        k=args.k,
        d=args.d,
        verbose=True,
    )

    if not verified:
        print(
            "The candidate failed independent verification. "
            "Do not use it as an upper bound."
        )
        return

    print()
    print(
        f"Verified upper bound: "
        f"E({args.n},{args.k},{args.d}) <= "
        f"{actual_edge_count}"
    )

    if actual_edge_count == theoretical_lower_bound:
        print(
            f"E({args.n},{args.k},{args.d}) "
            f"= {actual_edge_count}"
        )
    else:
        print(
            f"{theoretical_lower_bound} <= "
            f"E({args.n},{args.k},{args.d}) <= "
            f"{actual_edge_count}"
        )


if __name__ == "__main__":
    main()
