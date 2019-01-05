import networkx as nx

def adjust_graph(G,path,demand_nodes,assignments):
    all_edges = G.edges()
    edge_sizes = set()
    upper_bounds = []
    for i in range(len(path)):
        edge_sizes.add(G.edges[path[i]]['weight'])
        upper_bound = None
        if path[i][0] in demand_nodes:
            upper_bound = demand_nodes[path[i][0]]
        if path[i][1] in demand_nodes:
            upper_bound = demand_nodes[path[i][1]]

        upper_bounds.append(upper_bound)
        edge_sizes.add(upper_bound - G.edges[path[i]]['weight'])
    min_edge = min(edge_sizes)

    cycle_addition = []
    cycle_subtraction = []
    for i in range(len(path)):
        edge_weight = G.edges[path[i]]['weight']
        cycle_addition.append(edge_weight + ((-1)**i)*min_edge)
        cycle_subtraction.append(edge_weight + ((-1)**(i+1))*min_edge)

    #import pdb;pdb.set_trace()
    nodes_to_remove = set()
    new_weights = []
    for i in range(len(path)):
        if (cycle_subtraction[i] == 0 or cycle_subtraction[i] == upper_bounds[i]):
            new_weights = cycle_subtraction
            break
        if (cycle_addition[i] == 0 or cycle_addition[i] == upper_bounds[i]):
            new_weights = cycle_addition
            break
    cnt = 0
    for i in range(len(path)):
        G.edges[path[i]]['weight'] = new_weights[i]
        print(path[i])
        if new_weights[i] ==0:
            G.remove_edge(*path[i])
            cnt+=1
        if new_weights[i] == upper_bounds[i]:
            cnt+=1
            G.remove_edge(*path[i])
            if path[i][0] in demand_nodes:
                assignments[path[i][0]] = path[i][1]
            if path[i][1] in demand_nodes:
                assignments[path[i][1]] = path[i][0]

    return cnt

def augmenting_path(G,demand_nodes, assignments):
    reduced_elements = 0
    while 1:
        try:
            cycle = nx.find_cycle(G) #Done arbitrarily. Maybe better to select one specifically?
            reduced_elements+=adjust_graph(G,cycle,demand_nodes, assignments)
            print("Cycle: "+str(cycle))
        except nx.NetworkXNoCycle:
            break
    for i in G.nodes(): # Done arbitrarily. Maybe select one specifically?
        if G.degree(i) == 1:
            path = list(nx.dfs_edges(G,source=i))
            print("Path "+str(path))
            reduced_elements+=adjust_graph(G,path,demand_nodes, assignments)
            break
    return reduced_elements

G = nx.DiGraph()
node_demand = {'a':4,'b':4,'c':4,'d':4,'e':4}#,'f':10,'g':10,'h':10}
total_demand = 0
total_supply = 0
max_demand = 0
max_supply = 0
node_supply = {'x':55,'y':5,'z':5}#,'zz':10}
connection_list = {'a':['x','y'], 'b':['x','y'],'c':['y','z'], 'd':['y','z']}#,'f':['zz'],'g':['zz'],'h':['zz']}


for i in node_demand:
    G.add_node(i,demand=node_demand[i]*-1)
    total_demand+=node_demand[i]
    if node_demand[i] > max_demand:
        max_demand = node_demand[i]
for i in node_supply:
    G.add_node(i,demand=node_supply[i])
    total_supply+=node_supply[i]
    if node_supply[i] > max_supply:
        max_supply = node_supply[i]

# Supply slack used if there is too much demand and not enough supply. Represents infeasibility
# Demand slack used if there is more supply than demand. This does not constitue infeasibility, but availability in the supply nodes
        
if total_supply>total_demand:
    G.add_node('demand_slack',demand = -1*(total_demand+total_supply)+ total_demand - total_supply) #Add total_demand + total_supply incase all nodes disconnected. This means supply_slack is feeding all the supply nodes and demand_slack is feeding all the demand nodes
    G.add_node('supply_slack',demand = total_demand+total_supply )
else:
    G.add_node('demand_slack',demand = -1*(total_demand+total_supply) )
    G.add_node('supply_slack',demand = (total_demand+total_supply)- total_supply + total_demand)

G.add_edge('demand_slack','supply_slack',weight = -1*max_supply,capacity=total_demand+total_supply) #might this cause numerical issues?
#print(total_supply,total_demand)
#print(nx.get_node_attributes(G,'demand'))
for i in connection_list:
    for j in connection_list[i]:
        G.add_edge(i,j,weight=node_supply[j]*-1,capacity = node_demand[i]) #may help get more integer solutions?

for i in node_supply:
    G.add_edge('demand_slack',i, weight = 10, capacity = node_supply[i])

for j in node_demand:
    G.add_edge(j,'supply_slack', weight = 10, capacity = node_demand[j]) #Costs of all real edges are negative


#G.add_node('unassigned',demand=0)
#for i in node_demand:
#    G.add_edge(i,'unassigned',weight=10000,capacity=node_demand[i])
#for j in node_supply:
#    G.add_edge('unassigned',j,weight=10000,capacity=node_supply[j])

flow_cost,flow_dict = nx.network_simplex(G)

print(flow_dict)
supply_slack = {'supply_slack':{}}
demand_slack = {'demand_slack':flow_dict['demand_slack']}

print("Fractional assignments:")
for i in sorted(node_demand.keys()):
    print(i,flow_dict[i])
    if 'supply_slack' in flow_dict[i]: #If there's too much demand
        supply_slack['supply_slack'][i] =flow_dict[i]['supply_slack']
print(supply_slack)
print(demand_slack)
print()

assignments = {} #map demands to supplies
simple_assignments = {} 
for i in node_demand.keys():
    max_assignment = -1
    simple_element = None
    for j in flow_dict[i]:
        if flow_dict[i][j] > max_assignment:
            max_assignment = flow_dict[i][j]
            simple_element = j
    if simple_element == 'supply_slack':
        simple_assignments[i] = 'unassigned'
    else:
        simple_assignments[i] = simple_element


G2 = nx.Graph()
for i in node_demand:
    for j in flow_dict[i]:
        if j== 'supply_slack' and flow_dict[i][j] >0:
            assignments[i] = 'unassigned'
            break
        if flow_dict[i][j] == node_demand[i]:
            assignments[i] = j
            break
    if i not in assignments:
        for j in flow_dict[i]:
            if j!='supply_slack' and flow_dict[i][j]!=0:
                G2.add_edge(i,j, weight=flow_dict[i][j]) #for simplicity keep the edges integer

while 1:
    reduced = augmenting_path(G2,node_demand,assignments)
    if reduced == 0:
        break

if len(assignments)!= len(node_demand):
    print("Successfully assigned all demand nodes")
else:
    for i in node_demand:
        if i not in assignments:
            print(i+" not assigned")

allocation_amounts = {}
simple_allocation_amounts = {}
for i in node_supply.keys():
    allocation_amounts[i] = 0
    simple_allocation_amounts[i] = 0

print("Augmentation assignment:")
for i in node_demand.keys():
    if assignments[i] == 'unassigned':
        print(i+ " not assigned")
    else:
        allocation_amounts[assignments[i]] += node_demand[i]
        print(i+ "-> "+assignments[i])
for i in node_supply.keys():
    if node_supply[i] !=0:
        print(i+" at "+str(allocation_amounts[i]) + " ("+str(100*round(allocation_amounts[i]/float(node_supply[i]),3))+"%)")

print("\n")
print("Simple assignment:")
for i in node_demand.keys():
    if simple_assignments[i] == 'unassigned':
        print(i+ " not assigned")
    else:
        simple_allocation_amounts[simple_assignments[i]] += node_demand[i]
        print(i+ "-> "+simple_assignments[i])
for i in node_supply.keys():
    if node_supply[i] !=0:
        print(i+" at "+str(simple_allocation_amounts[i]) + " ("+str(100*round(simple_allocation_amounts[i]/float(node_supply[i]),3))+"%)")

