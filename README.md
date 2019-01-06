# generalized-assignment-problem
Approximation algorithms for the generalized assignment problem using network simplex
gap.py contains earlier approximations which may exceed the overload approximation factor of 1

gap2.py contains the standard generalized assignment problem 2-approximation algorithm and is the reccommended algorithm to use
It also allows unassignable nodes to be allocated in the case of infeasible solutions by specifying an overload threshold
A shortcut to speed up the algorithm can be set using the risky parameter, which may result in unintentionally overloaded nodes but may reduce the number of simplex resolves required

