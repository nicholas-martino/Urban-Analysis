# -*- coding: utf-8 -*-
"""
Created on Tue Jan  8 13:52:23 2019

@author: nicholas-martino
"""

import os
import time
import fiona
import shape
import igraph
import osmnx as ox
import networkx as nx


def network_analysis (place_name,path):
    start_time = time.clock()
    file_path = os.path.join(path, place_name)
    print (place_name+" - Network")
    
    # Download graphs
    print ("1/4 - Downloading graphs ")
    graph_raw_walk = ox.graph_from_place(place_name, network_type='walk')
    graph_raw_bike = ox.graph_from_place(place_name, network_type='bike')
    graph_raw = nx.compose(graph_raw_walk,graph_raw_bike)
    print("--- %s minutes ---" %((time.clock()-start_time)/60))
    start_time = time.clock()
    
    # Project graphs
    print ("2/4 - Projecting graphs")
    nxgraph = ox.project_graph(graph_raw)
    print("--- %s minutes ---" %((time.clock()-start_time)/60))
    start_time = time.clock()
    
    # Calculate centrality measurements
    print ("3/4 - Calculating centrality")
    g = igraph.Graph.TupleList(nxgraph.edges(), directed=True)
    closeness = g.closeness(vertices=None, mode=3, cutoff=None, 
                            weights=None, normalized=True)               
    osmid = g.vs.get_attribute_values('name')   
    zipobj = zip(osmid, closeness)
    closeness_dict = dict(zipobj)
    print("--- %s minutes ---" %((time.clock()-start_time)/60))

    # Export to shapefile      
    print("4/4 - Exporting shapefile")
    nx.set_node_attributes(nxgraph,closeness_dict,'closeness')
    ox.save_graph_shapefile(nxgraph, filename=place_name, folder=file_path, 
                            encoding='UTF-8')   
    print("--- %s minutes ---" %((time.clock()-start_time)/60))
    start_time = time.clock()
    
    
    # Explode and split segments
    edges = nxgraph.edges()

    #nodes = nxgraph.nodes()
    def cut_line_at_points(line, points):

        # First coords of line
        coords = list(line.coords)

        # Keep list coords where to cut (cuts = 1)
        cuts = [0] * len(coords)
        cuts[0] = 1
        cuts[-1] = 1

        # Add the coords from the points
        coords += [list(p.coords)[0] for p in points]    
        cuts += [1] * len(points)        

        # Calculate the distance along the line for each point    
        dists = [line.project(Point(p)) for p in coords]
        # sort the coords/cuts based on the distances
        # see http://stackoverflow.com/questions/6618515/sorting-list-based-on-values-from-another-list    
        coords = [p for (d, p) in sorted(zip(dists, coords))]    
        cuts = [p for (d, p) in sorted(zip(dists, cuts))]          

        # generate the Lines    
        #lines = [LineString([coords[i], coords[i+1]]) for i in range(len(coords)-1)]    
        lines = []        

        for i in range(len(coords)-1):    
            if cuts[i] == 1:    
                # find next element in cuts == 1 starting from index i + 1   
                j = cuts.index(1, i + 1)    
                lines.append(LineString(coords[i:j+1]))            

        return lines
    
    
    
    # Extract and buffer vertices
    print ("Buffering vertices")


   
    # Snap segments to centroids
    
    #Export to GeoPackage
    
    return print ("Done!")


root_folder = 'C:\MEGA\OSMnx'
network("Metro Vancouver, Canada",root_folder)
network("Região Metropolitana do Rio de Janeiro, Brazil",root_folder)