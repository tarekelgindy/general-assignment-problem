import networkx as nx


def adjust_graph(G,path,demand_nodes,assignments):
    all_edges = G.edges()
    edge_sizes = set()
    all_weights = nx.get_edge_attributes(G,'weight')
    for i in range(len(path)):
        e = path[i]
        if not e in all_weights:
            e = (e[1],e[0])
        edge_sizes.add(all_weights[e])
    min_edge = min(edge_sizes)

    cycle_addition = []
    cycle_subtraction = []
    for i in range(len(path)):
        e = path[i]
        if not e in all_weights:
            e = (e[1],e[0])
        cycle_addition.append(all_weights[e] + ((-1)**i)*min_edge)
        cycle_subtraction.append(all_weights[e] + ((-1)**(i+1))*min_edge)

    nodes_to_remove = set()
    use_subtraction = None #Lock in which augmentation we're using once we find a node to remove
    for i in range(len(path)):
        if cycle_subtraction[i] == 0 and (use_subtraction is None or use_subtraction):
            use_subtraction = True
            nodes_to_remove.add(path[i])
        if cycle_addition[i] == 0 and (use_subtraction is None or not use_subtraction):
            use_subtraction = False
            nodes_to_remove.add(path[i])

    cnt = 0
    for e in nodes_to_remove:
        if e[0] in demand_nodes:
            assignments[e[0]] = e[1]
            cnt+=1
            for tr in G.edges(e[0]):
                G.remove_edge(tr[0],tr[1])
        if e[1] in demand_nodes:
            assignments[e[1]] = e[0]
            cnt+=1
            for tr in G.edges(e[0]):
                G.remove_edge(tr[0],tr[1])
    return cnt

def augmenting_path(G,demand_nodes,assignments):
    reduced_elements = 0
    while 1:
        try:
            cycle = nx.find_cycle(G) #Done arbitrarily. Maybe better to select one specifically?
            reduced_elements+=adjust_graph(G,cycle,demand_nodes,assignments)
            #print("Cycle: "+str(cycle))
        except nx.NetworkXNoCycle:
            break
    for i in G.nodes(): # Done arbitrarily. Maybe select one specifically?
        if G.degree(i) == 1:
            path = list(nx.dfs_edges(G,source=i))
            #print("Path "+str(path))
            reduced_elements+=adjust_graph(G,path,demand_nodes,assignments)
            break
    return reduced_elements

G = nx.DiGraph()
node_demand = {'a':4,'b':4,'c':4,'d':4}
total_demand = 0
total_supply = 0
max_demand = 0
node_supply = {'x':15,'y':5,'z':5}
connection_list = {'a':['x','y'], 'b':['x','y'],'c':['y','z'], 'd':['y','z']}

for i in node_demand:
    G.add_node(i,demand=node_demand[i]*-1)
    total_demand+=node_demand[i]
    if node_demand[i] > max_demand:
        max_demand = node_demand[i]
for i in node_supply:
    G.add_node(i,demand=node_supply[i])
    total_supply+=node_supply[i]
if total_demand != total_supply:
    G.add_node('slack',demand = total_demand-total_supply)

for i in connection_list:
    for j in connection_list[i]:
        G.add_edge(i,j,weight=node_supply[j]*-1,capacity = node_demand[i]) #may help get more integer solutions?

if total_demand< total_supply:
    for i in node_supply:
        G.add_edge('slack',i, weight = 1, capacity = total_supply-total_demand)

if total_demand> total_supply:
    for i in node_supply:
        G.add_edge(i,'slack', weight = 1, capacity = total_demand-total_supply)
flow_cost,flow_dict = nx.network_simplex(G)

print("Fractional assignments:")
for i in sorted(node_demand.keys()):
    print(i,flow_dict[i])
print("\n")

assignments = {} #map demands to supplies
simple_assignments = {} 
for i in node_demand.keys():
    max_assignment = -1
    simple_element = None
    for j in flow_dict[i]:
        if flow_dict[i][j] > max_assignment:
            max_assignment = flow_dict[i][j]
            simple_element = j
    simple_assignments[i] = simple_element


G2 = nx.Graph()
for i in node_demand:
    for j in flow_dict[i]:
        if flow_dict[i][j] == node_demand[i]:
            assignments[i] = j
            for e in G.edges(i):
                G.remove_edge(e[0],e[1])
    if i not in assignments:
        for j in flow_dict[i]:
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
    allocation_amounts[assignments[i]] += node_demand[i]
    print(i+ "-> "+assignments[i])
for i in node_supply.keys():
    if node_supply[i] !=0:
        print(i+" at "+str(allocation_amounts[i]) + " ("+str(100*round(allocation_amounts[i]/float(node_supply[i]),3))+"%)")

print("\n")
print("Simple assignment:")
for i in node_demand.keys():
    simple_allocation_amounts[assignments[i]] += node_demand[i]
    print(i+ "-> "+assignments[i])
for i in node_supply.keys():
    if node_supply[i] !=0:
        print(i+" at "+str(simple_allocation_amounts[i]) + " ("+str(100*round(simple_allocation_amounts[i]/float(node_supply[i]),3))+"%)")

