# Steiner Tree Algorithm Alternatives

Developer reference for potential replacements or improvements to the current Kou's metric closure implementation.

## Current Implementation: Kou's Metric Closure Algorithm

**How it works:**
1. Build complete graph on terminals (buildings) using shortest paths through street network
2. Compute MST on this metric closure graph
3. Expand MST edges back to shortest paths in original network
4. Remove cycles and redundant edges

**Pros:** Good quality, handles k-nearest candidates, O(|S||V|²) complexity
**Cons:** Slower for large networks, not exact optimal

## Alternative 1: Multi-Source Dijkstra (Approximation)

**Idea:** Start from all terminals simultaneously, grow shortest-path trees until they meet
**Pros:** Faster (O(|E|+|V|log|V|)), simpler implementation
**Cons:** Lower quality than metric closure, doesn't handle k-nearest candidates
**Use case:** Very large networks (>5000 buildings) where speed is critical

**Implementation sketch:**
```python
def multi_source_steiner(graph, terminals):
    import heapq

    # Priority queue: (distance, node, source_terminal)
    pq = [(0, t, t) for t in terminals]
    heapq.heapify(pq)

    visited = set()
    tree_edges = []

    while pq and len(visited) < len(graph.nodes()):
        dist, node, source = heapq.heappop(pq)

        if node in visited:
            continue

        visited.add(node)
        if node != source:
            tree_edges.append((source, node))

        for neighbor in graph.neighbors(node):
            if neighbor not in visited:
                edge_weight = graph[node][neighbor]['weight']
                heapq.heappush(pq, (dist + edge_weight, neighbor, node))

    return tree_edges
```

## Alternative 2: Exact ILP Formulation (Small Networks)

**Idea:** Formulate as Integer Linear Program, solve with CPLEX/Gurobi
**Pros:** Provably optimal solution
**Cons:** NP-hard, only feasible for <100 terminals, requires commercial solver
**Use case:** Critical infrastructure where optimality is essential and network is small

**Formulation:**
- Binary variable `x_e` for each edge e (1 if in tree, 0 otherwise)
- Minimize: Σ(weight_e × x_e) over all edges
- Constraints:
  - Σ(x_e) = |V| - 1 (tree property)
  - For each terminal pair (s, t): flow(s→t) ≥ 1 (connectivity)
  - Subtour elimination constraints

## Alternative 3: MST with Terminal Preference Heuristic

**Idea:** Weight edges adjacent to terminals higher, then compute standard MST
**Pros:** Very fast (O(|E|log|V|)), simple, often good enough
**Cons:** Heuristic, no quality guarantees, ignores Steiner nodes

**Implementation sketch:**
```python
def terminal_weighted_mst(graph, terminals):
    for u, v, data in graph.edges(data=True):
        base_weight = data['weight']
        if u not in terminals and v not in terminals:
            data['mst_weight'] = base_weight * 1.5
        else:
            data['mst_weight'] = base_weight

    mst = nx.minimum_spanning_tree(graph, weight='mst_weight')
    return mst
```

## Alternative 4: Iterative MST Refinement

**Idea:** Start with Kou's solution, iteratively remove high-cost Steiner nodes
**Pros:** Improves over Kou, still fast
**Cons:** May converge to local minimum

**Steps:**
1. Compute initial Steiner tree with Kou
2. For each Steiner node v with degree=2: check if removing v and connecting neighbors directly reduces cost
3. Repeat until no improvements found

## When to Use Which Algorithm

| Network Size | Terminals | Quality Need | Recommended Algorithm | Expected Runtime |
|-------------|-----------|--------------|----------------------|------------------|
| <500 streets | <50 | Critical | Exact ILP | 1-60 seconds |
| <2000 streets | <500 | High | Kou k=3-5 | 10-120 seconds |
| <2000 streets | <500 | Medium | Kou k=1-3 | 1-30 seconds |
| >5000 streets | >1000 | Medium | Kou k=1 or Mehlhorn | 10-60 seconds |
| >10000 streets | >2000 | Fast | Multi-source Dijkstra | <30 seconds |

## Future Improvements

**Priority 1: Adaptive k selection**
- Auto-detect network density (buildings per street segment)
- Use k=5 for sparse networks, k=1 for dense networks

**Priority 2: Spatial partitioning for large networks**
- Divide network into quadtree/grid cells
- Solve Steiner problem per cell independently, merge at boundaries
- Enables parallelization and linear scaling

**Priority 3: Local search refinement**
- After Kou, apply 2-opt/3-opt moves on Steiner nodes
- Typically 5-15% improvement for marginal cost

**Priority 4: Machine learning guided search**
- Train model to predict good k values based on network features
