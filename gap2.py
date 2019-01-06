import networkx as nx
        

def generalized_assignment_problem(node_demand, node_supply,connection_list,overload_supplies=False,overload_threshold = None, risky = False):
    """ 
    A solution to the unweighted generalized assignment problem.
    Uses the network simplex algorithm to get an LP relaxation.
    A 2-approximation (on supply overloads) is then used to recover a non-fractional assignment.
    Algorithm based on this theory:
    https://theory.stanford.edu/~jvondrak/CS369P/lec12.pdf
    but also deals with unassigned nodes.

    A heuristic of weighting edges by the supply value is used.
    Options exist to allocate demands by connecting to overloaded supplies

    Parameters
    ----------
    node_demand: dict
        The demand nodes (or jobs). Job i must be entirely assigned to one supply with amount node_demand[i]
        node_demand[i] assumed to be integer for convergence of network simplex

    node_supply: dict
        The supply nodes (or machines). Machine j can have any number of jobs attached with at most node_supply[j] allocated
        node_supply[i] assumed to be integer for convergence of network simplex

    connection_list: dict
        A dictionary that maps the supply nodes that demand i can be assigned to

    overload_supplies: float, optional
        A flag indicating whether supply nodes should be overloaded if there exist unassigned jobs

    overload_threshold: float, optional
        The amount that we're willing to overload supply nodes not assigned with the (worst case) 2-approximation ratio

    risky: bool, optional
        A flag to try removing multiple single or two degree supplies simultaneously.
        The correct approach is to resolve the LP each time to speed things up. 
        This may create incorrect solutions.
        However, with the heuristic used this is likely not a problem, since priority assigned to larger supplies
        (Proof required for that theory though...)
    """

    G = nx.DiGraph()
    for i in connection_list:
        for j in connection_list[i]:
            G.add_edge(i,j,weight=node_supply[j]*-1,capacity = node_demand[i]) #A heuristic that may help get more integer solutions?

    for i in node_demand:
        G.add_node(i,demand=node_demand[i]*-1)

    for i in node_supply:
        G.add_node(i,demand=node_supply[i])

    
    original_supply = {i:v for i,v in node_supply.items()}
    original_demand = {i:v for i,v in node_demand.items()}
    closest_supply = {}
    closest_supply_amount = {}
    assignments = {} #map demands to supplies

    while len(node_demand) > 0:
        total_demand = 0
        total_supply = 0
        max_supply = 0
    
        for i in node_demand:
            total_demand+=node_demand[i]
        for i in node_supply:
            total_supply+=node_supply[i]
            if node_supply[i]> max_supply:
                max_supply = node_supply[i]
    
        # Supply slack used if there is too much demand and not enough supply. Represents infeasibility
        # Demand slack used if there is more supply than demand. This does not constitue infeasibility, but availability in the supply nodes

        #Add total_demand + total_supply incase all nodes disconnected.
        #This means supply_slack is feeding all the supply nodes and demand_slack is feeding all the demand nodes
        if total_supply>total_demand:
            G.add_node('demand_slack',demand = -1*(total_demand+total_supply)+ total_demand - total_supply) 
            G.add_node('supply_slack',demand = total_demand+total_supply )
        else:
            G.add_node('demand_slack',demand = -1*(total_demand+total_supply) )
            G.add_node('supply_slack',demand = (total_demand+total_supply)- total_supply + total_demand)
        
        G.add_edge('demand_slack','supply_slack',weight = -1*max_supply,capacity=total_demand+total_supply) #might this cause numerical issues?
    
        #Costs of all real edges are negative so only assigned if no other options
        for i in node_supply:
            G.add_edge('demand_slack',i, weight = 10, capacity = node_supply[i])
        
        for j in node_demand:
            G.add_edge(j,'supply_slack', weight = 10, capacity = node_demand[j]) 

        # Network simplex algorithm used to do the LP relaxation. Should be fast in practice
        flow_cost,flow_dict = nx.network_simplex(G)
        demands_to_remove = []
        supplies_to_remove = []
        remove_supplies = True
    
        # Find closest fractional node assignment in case node is unassigned. Only used if overload_supplies flag is set
        if overload_supplies:
            for i in node_demand:
                for j in flow_dict[i]:
                    if j!="supply_slack":
                        if i not in  closest_supply_amount or flow_dict[i][j] > closest_supply_amount[i]:
                            closest_supply[i] = j
                            closest_supply_amount[i] = flow_dict[i][j]

        # Remove demand node if it's unassigned (i.e. connected to slack supply
        # Remove demand node and edges if it's fully allocated to a supply node
        # Remove edge if LP relaxation assigns it to 0 (not included in optimal
        for i in node_demand:
            for j in flow_dict[i]:
                if j== 'supply_slack' and flow_dict[i][j] >0:
                    remove_supplies = False
                    assignments[i] = 'unassigned'
                    G.remove_node(i)
                    demands_to_remove.append(i)
                    break
                if flow_dict[i][j] == node_demand[i]:
                    remove_supplies = False
                    assignments[i] = j
                    node_supply[j] = node_supply[j]-node_demand[i]
                    G.node[j]['demand'] = G.node[j]['demand']-node_demand[i]
                    G.remove_node(i)
                    demands_to_remove.append(i)
                    break
                if j!= 'supply_slack' and flow_dict[i][j] == 0: #ignore empty edges to slack node
                    remove_supplies = False
                    G.remove_edge(i,j)

        # Only remove supplies if no edges have been removed already
        # Remove supply node if it has a degree of one (i.e. it won't be used since it wasn't fully assigned in the LP)
        # Remove supply node if it has a degree of two and inputs from connected nodes are overloaded
        if remove_supplies:
            # Since it's a digraph we need to specify nodes coming into j for the degree 2 case
            reverse_neighbors = {}
            for i in node_demand:
                for j in G.neighbors(i):
                    if j in reverse_neighbors:
                        reverse_neighbors[j].append(i)
                    else:
                        reverse_neighbors[j] = [i]
            for j in node_supply:
                if G.degree(j) <=2: # Degree needs to be <=1 but we've got a slack node connected to all supplies
                    G.remove_node(j)
                    supplies_to_remove.append(j)
                    if not risky:
                        break
                elif G.degree(j) ==3: # Degree needs to be <=2 but we've got a slack node connected to all supplies
                    total_xin = 0
                    for i in reverse_neighbors[j]:
                        if node_demand[i] != 0: #should always be the case
                            total_xin += flow_dict[i][j]/float(node_demand[i])
                    if total_xin >=1:
                        G.remove_node(j)
                        supplies_to_remove.apend(j)
                        if not risky:
                            break

        # Update supply and demand nodes and prepare for rerun.
        for i in demands_to_remove:
            node_demand.pop(i)
        for i in supplies_to_remove:
            node_supply.pop(i)
        G.remove_node('supply_slack')
        G.remove_node('demand_slack')

    
    allocation_amounts = {}
    for i in original_supply.keys():
        allocation_amounts[i] = 0
    
    print("Assigneed Demands:")
    for i in original_demand.keys():
        if assignments[i] == 'unassigned':
            pass
        else:
            allocation_amounts[assignments[i]] += original_demand[i]
            print(i+ "-> "+assignments[i])
    print()
    print("Non-empty supplies:")
    for i in original_supply.keys():
        if original_supply[i] !=0 and allocation_amounts[i] !=0:
            print(i+" at "+str(allocation_amounts[i]) + " ("+str(round(100*allocation_amounts[i]/float(original_supply[i]),3))+"%)")
    
    print()
    print("Unassigned demands:")
    overloaded_allocation_amounts = {}
    for i in original_demand.keys():
        # closest_supply will only be non-empty if overload_supplies is True
        if assignments[i] == 'unassigned' and i in closest_supply:
            print(i+ " not assigned - closest supply is " + closest_supply[i])
            if closest_supply[i] not in overloaded_allocation_amounts:
                if overload_threshold is None or allocation_amounts[closest_supply[i]] + original_demand[i] < overload_threshold * original_supply[closest_supply[i]]:
                    overloaded_allocation_amounts[closest_supply[i]] = allocation_amounts[closest_supply[i]] + original_demand[i]
                    assignments[i] = closest_supply[i]
            else:
                if overload_threshold is None or overloaded_allocation_amounts[closest_supply[i]] + original_demand[i] < overload_threshold * original_supply[closest_supply[i]]:
                    overloaded_allocation_amounts[closest_supply[i]] = overloaded_allocation_amounts[closest_supply[i]] + original_demand[i]
                    assignments[i] = closest_supply[i]

        # This is used if overload_supplies is False since closest_supply will be empty
        if assignments[i] == 'unassigned' and i not in closest_supply:
            print(i+ " not assigned")
    
    if overload_supplies:
        print()
        print("Supply loading if unassigned demands attached to best candidate within overload threshold {}:".format(overload_threshold))
        for i in overloaded_allocation_amounts:
            print(i+" at "+str(overloaded_allocation_amounts[i]) + " ("+str(round(100*overloaded_allocation_amounts[i]/float(original_supply[i]),3))+"%)")

    return assignments

if __name__ == "__main__":
    node_demand = {'a':4,'b':4,'c':4,'d':4,'e':4,'f':10,'g':10,'h':10}
    node_supply = {'x':55,'y':5,'z':5,'zz':10}
    connection_list = {'a':['x','y'], 'b':['x','y'],'c':['y','z'], 'd':['y','z'],'f':['zz'],'g':['zz'],'h':['zz']}

    generalized_assignment_problem(node_demand,node_supply,connection_list,overload_supplies=True,overload_threshold = 2.0, risky=True)

