import argparse
import math
from itertools import combinations
from math import comb

from ortools.sat.python import cp_model

from bounds import compute_lower_bounds
from exact_search import (
    FORCED_EDGES,
    check_graph,
    normalize_edge,
)


def optimize_graph(n, k, d, time_limit, workers):
    """
    Minimize e(G) subject to

        H0 subset of G,
        delta(G) >= d,
        t(G) >= k.
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

    edge_count = sum(x.values())
    model.Minimize(edge_count)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_search_workers = workers

    status = solver.Solve(model)
    status_name = solver.StatusName(status)

    result = {
        "status": status_name,
        "edges": None,
        "objective": None,
        "solver_lower_bound": None,
    }

    if status in (
        cp_model.OPTIMAL,
        cp_model.FEASIBLE,
    ):
        edges = [
            edge
            for edge in all_edges
            if solver.Value(x[edge]) == 1
        ]

        result["edges"] = edges
        result["objective"] = int(
            round(solver.ObjectiveValue())
        )

        result["solver_lower_bound"] = math.ceil(
            solver.BestObjectiveBound() - 1e-9
        )

    return result


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=(
            "Directly minimize the number of edges in a legal graph."
        )
    )

    parser.add_argument("--n", type=int, default=9)
    parser.add_argument("--k", type=int, default=11)
    parser.add_argument("--d", type=int, default=3)

    parser.add_argument(
        "--time-limit",
        type=float,
        default=300.0,
        help="Total solver time limit in seconds.",
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=8,
        help="Number of CP-SAT search workers.",
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

    if args.workers <= 0:
        raise ValueError("workers must be positive")


def main():
    args = parse_arguments()
    validate_arguments(args)

    theoretical_bounds = compute_lower_bounds(
        args.n,
        args.k,
        args.d,
    )

    theoretical_lower_bound = theoretical_bounds["combined"]

    print("Parameters")
    print(f"n = {args.n}")
    print(f"k = {args.k}")
    print(f"d = {args.d}")
    print(
        "Theoretical lower bound = "
        f"{theoretical_lower_bound}"
    )
    print(f"Time limit = {args.time_limit} seconds")
    print(f"Workers = {args.workers}")
    print()

    result = optimize_graph(
        n=args.n,
        k=args.k,
        d=args.d,
        time_limit=args.time_limit,
        workers=args.workers,
    )

    status = result["status"]

    print("Solver status:", status)

    if status == "INFEASIBLE":
        print(
            "The model was declared infeasible. In the stated "
            "parameter range, K_n should be feasible, so inputs "
            "and the model should be checked."
        )
        return

    if status not in ("OPTIMAL", "FEASIBLE"):
        print(
            "The solver produced no witness. "
            "No new upper bound is available."
        )
        return

    edges = result["edges"]
    objective = result["objective"]
    solver_lower_bound = result["solver_lower_bound"]

    print("Solver objective:", objective)
    print("Solver lower bound:", solver_lower_bound)
    print("Edges:")
    print(sorted(edges))
    print()

    verified = check_graph(
        n=args.n,
        edges=edges,
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

    actual_edge_count = len(edges)

    combined_lower_bound = max(
        theoretical_lower_bound,
        solver_lower_bound,
    )

    print()
    print(
        f"Verified upper bound: "
        f"E({args.n},{args.k},{args.d}) <= "
        f"{actual_edge_count}"
    )

    print(
        f"Current lower bound: "
        f"E({args.n},{args.k},{args.d}) >= "
        f"{combined_lower_bound}"
    )

    if status == "OPTIMAL":
        print()
        print(
            "CP-SAT completed the optimization and returned OPTIMAL."
        )
        print(
            f"Computational result: "
            f"E({args.n},{args.k},{args.d}) "
            f"= {actual_edge_count}"
        )

        if actual_edge_count == theoretical_lower_bound:
            print(
                "The witness attains the pure theoretical lower "
                "bound. Hence the equality follows from the "
                "theoretical bound and the verified witness."
            )
        else:
            print(
                "The lower-bound step beyond the theoretical bound "
                "depends on CP-SAT's completed optimality proof."
            )

    elif combined_lower_bound == actual_edge_count:
        print()
        print(
            "The solver lower bound and verified upper bound coincide."
        )
        print(
            f"Computationally, "
            f"E({args.n},{args.k},{args.d}) "
            f"= {actual_edge_count}"
        )

    else:
        print()
        print("Current interval:")
        print(
            f"{combined_lower_bound} <= "
            f"E({args.n},{args.k},{args.d}) <= "
            f"{actual_edge_count}"
        )
        print(
            "The optimization stopped before proving optimality. "
            "Increasing the time limit may tighten the interval."
        )


if __name__ == "__main__":
    main()
