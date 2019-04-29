# -*- coding: utf-8 -*-
"""
Created on Tue Jan  8 13:52:23 2019

@author: nicholas-martino
"""

import os
import time
import igraph
import osmnx as ox
import networkx as nx
import os.path  
import psycopg2
import osgeo.ogr
import shapefile 


def osm2shp (place_name,database_name):
    start_time = time.clock()
    path = 'C:/temp/'
    file_path = os.path.join(path)
    print (place_name+" - Network")
    print("--- %s minutes ---" %((time.clock()-start_time)/60))
    start_time = time.clock()
    # Download graphs
    print ("Downloading graphs ")
    graph_raw_walk = ox.graph_from_place(place_name, network_type='walk')
    graph_raw_bike = ox.graph_from_place(place_name, network_type='bike')
    graph_raw = nx.compose(graph_raw_walk,graph_raw_bike)
    print("--- %s minutes ---" %((time.clock()-start_time)/60))
    start_time = time.clock()
    # Project graphs
    print ("Projecting graphs")
    nxgraph = ox.project_graph(graph_raw)
    print("--- %s minutes ---" %((time.clock()-start_time)/60))
    start_time = time.clock()
    ox.save_graph_shapefile(nxgraph, filename=place_name, folder=file_path,encoding='UTF-8')      
    print("--- %s minutes ---" %((time.clock()-start_time)/60))
    return print ("Done!")


def points2postgis (database_name, table_name):
    database_name = "BC_Vancouver"
    # Import shapefile to postgis database
    print ("Connecting to PostGIS")
    start_time = time.clock()
    connection = psycopg2.connect(host = "localhost",
                                  database = database_name,
                                  user = "postgres",
                                  password = "formaurbana",
                                  port = 5433)
    cursor = connection.cursor()
    r = shapefile.Reader("C:/temp/University Endowment Lands Vancouver, Canada/nodes/nodes.shp")
    fields = r.fields[1:]
    field_string = ""
    table_query = (
    """
    DROP TABLE IF EXISTS network_intersections;
    CREATE TABLE network_intersections (
    id SERIAL,
    PRIMARY KEY (id),
    geom GEOMETRY(Point,26910),
    """)
    for i in range(len(fields)):
        # get the field information
        f = fields[i]
        # get the field name and lowercase it for consistency
        f_name = f[0].lower()
        # add the name to the query and our string list of fields
        table_query += f_name
        field_string += f_name
        # Get the proper type for each field. Note this check
        # is not comprehensive but it convers the types in
        # our sample shapefile.
        if f[1] == "F":
            table_query += " DOUBLE PRECISION"
        elif f[1] == "N":
            table_query += " INTEGER"
        else:
            table_query += " VARCHAR"
        # If this field isn' the last, we'll add a comma
        # and some formatting.
        if i != len(fields)- 1:
            table_query += ","
            table_query += "\n"
            table_query += "                 "
            field_string += ","
        # Close the query on the field.
        else:
            table_query += ")"
            field_string += ",geom"
        print(table_query)
    cursor.execute(table_query)
    connection.commit()    
    shape_records = (shp_rec for shp_rec in r.iterShapeRecords())
    # Loop through the shapefile data and add it to our new table.
    for sr in shape_records:
        # Get our point data.
        shape = sr.shape
        x, y = shape.points[0]
        # Get the attribute data and set it up as
        # a query fragment.
        attributes = ""
        for r in sr.record:
            if type(r) == type("string"):
                r = r.replace("'", "''")
            attributes += "'{}'".format(r)
            attributes += ","        
        # Build our insert query template for this shape record.
        # Notice we are going to use a PostGIS function
        # which can turn a WKT geometry into a PostGIS
        # geometry.
        point_query = """INSERT INTO network_intersections 
                    ({})
                    VALUES ({}
                    ST_GEOMFROMTEXT('POINT({} {})',26910))"""    
        # Populate our query template with actual data.
        format_point_query = point_query.format(field_string,attributes, x, y)
        # Insert the point data
    cursor.execute(format_point_query) 
    # Everything went ok so let's update the database.
    connection.commit()
    # Query to simplify intersections
    simplify_query = """INSERT QUERY"""
    cursor.execute(simplify_query)
    connection.commit()            
    cursor.close()
    connection.close()    
    print("--- %s minutes ---" %((time.clock()-start_time)/60))
    return print ("done!")
    
    
def closeness (database_name, table_name):
    print ("Calculating centrality")
    
    g = igraph.Graph.TupleList(nxgraph.edges(), directed=True)
    closeness = g.closeness(vertices=None, mode=3, cutoff=None, 
                            weights=None, normalized=True)               
    osmid = g.vs.get_attribute_values('name')   
    zipobj = zip(osmid, closeness)
    closeness_dict = dict(zipobj)
    nx.set_node_attributes(nxgraph,closeness_dict,'closeness')
    return print ("done!")



"""


    print ("Calculating centrality")
    g = igraph.Graph.TupleList(nxgraph.edges(), directed=True)
    closeness = g.closeness(vertices=None, mode=3, cutoff=None, 
                            weights=None, normalized=True)               
    osmid = g.vs.get_attribute_values('name')   
    zipobj = zip(osmid, closeness)
    closeness_dict = dict(zipobj)
    nx.set_node_attributes(nxgraph,closeness_dict,'closeness')
       


 shapefile = osgeo.ogr.Open('C:/temp/University Endowment Lands Vancouver, Canada/edges/edges.shp')    
        print (shapefile)
        layer = shapefile.GetLayer(0) 
    
        for i in range(layer.GetFeatureCount()):  
        feature = layer.GetFeature(i)  
        name = feature.GetField("osmid")  
        wkt = feature.GetGeometryRef().ExportToWkt()  
        cur.execute
    
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
    """



#network_analysis("University Endowment Lands Vancouver, Canada","BC_Vancouver")
#network_analysis("Região Metropolitana do Rio de Janeiro, Brazil",root_folder)