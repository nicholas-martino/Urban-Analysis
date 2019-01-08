# -*- coding: utf-8 -*-
"""
Created on Tue Jan  8 13:52:23 2019

@author: nicholas-martino
"""

import os
import sys
import time
import pyproj
import osmnx as ox
import numpy as np
import pandas as pd
import geopandas as gpd
import geopandas_osm.osm
from functools import partial
from shapely.ops import transform


def land_use (place_name, path):
    start_time = time.clock()
    
    # Define variables and create directories
    file_path = os.path.join(path, place_name)
    filename_bld = os.path.join(path, place_name,"land_buildings.shp")
    place_gdf = ox.gdf_from_place(place_name)
    polygon = place_gdf['geometry'].iloc[0]
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    np.set_printoptions(threshold=sys.maxsize)

    # Download building, amenities and zones
    print ("Land - "+place_name)
    place_centroid = polygon.centroid
    project = partial(
            pyproj.transform,
            pyproj.Proj(init='epsg:4326'), # source coordinate system
            pyproj.Proj(init='epsg:3786')) # destination coordinate system
    place_centroid = transform(project, place_centroid) 
    buffer=place_centroid.buffer(1800)
    project = partial(
            pyproj.transform,
            pyproj.Proj(init='epsg:3786'), # source coordinate system
            pyproj.Proj(init='epsg:4326')) # destination coordinate system
    buffer = transform(project, buffer)   
    bld_raw = ox.create_buildings_gdf(buffer)
    bld_raw['fid'] = bld_raw.index
    bld = bld_raw    
    poi = ox.create_poi_gdf(buffer)
    lus = geopandas_osm.osm.query_osm('way', buffer, recurse='down', tags='landuse')    
    lus_ch = gpd.GeoDataFrame(lus.convex_hull)
    lus_ch.rename(columns={0:'geometry'},inplace=True)
    lus = pd.DataFrame(lus)
    lus = lus.join(lus_ch,how='left',lsuffix='_l',rsuffix='_r')
    lus.rename(columns={'geometry_r':'geometry'},inplace=True)
    lus = gpd.GeoDataFrame(lus)
    
    # Clean and join data
    lus.rename(columns={'landuse':'use_zones'},inplace=True)
    lus.rename(columns={'geometry':'geometry'},inplace=True)
    bld = gpd.sjoin(bld,lus,how="left",op='intersects',lsuffix='_l',rsuffix='_r')
    poi.rename(columns={'amenity':'use_points'},inplace=True)
    poi.rename(columns={'geometry':'geometry'},inplace=True)
    poi = poi[['use_points','geometry','nodes']]
    bld = gpd.sjoin(bld,poi,how="left",op='intersects')
      
    # Estimate the height of buildings
    bld.rename(columns={'building:part':'bp'},inplace=True)    
    bld.rename(columns={'building:levels__l':'bl'},inplace=True)
    bld.rename(columns={'building:levels':'bl'},inplace=True)
    bld.rename(columns={'building__l':'building'},inplace=True)
    bld.rename(columns={'height__l':'height'},inplace=True)
    bld.rename(columns={'amenity__l':'amenity_build'},inplace=True)
    bld.rename(columns={'amenity':'amenity_build'},inplace=True)
    bld['bl'] = (pd.to_numeric(bld['bl'], errors='coerce',downcast='integer'))*4
    bld.bl = bld.bl.replace(np.nan,4)
    bld['height'] = pd.to_numeric((bld['height']), errors='coerce',downcast='integer')
    bld.height = bld.height.replace(np.nan,4)
    l_height = (bld.bl==4)&(bld.height>4)
    conditions = [l_height]
    choices = [bld.height]
    bld['height_est'] = np.select(conditions, choices, default=bld.bl)

    # Classify probable building uses
    building_null = bld.building.isnull()|(bld.building == 'yes')|(bld.building == 'roof')
    bld['use_building'] = np.where (building_null, bld.amenity_build, bld.building)
    def reclassify_uses (series1):
        def replace_values (series2,to_search,to_change):
            series2 = series2.replace(to_search,value=to_change)
            return series2
        cull_furniture = ['toilets','bench','drinking_water','waste_basket',
                          'bicycle_parking','telephone','parking_entrance','waste_disposal',
                          'fountain','parking','atm','grass','car_sharing','post_box',
                          'bicycle_rental','nan','clock','terrace']
        cull_residential = ['apartments','hotel','house','residential']
        cull_commercial = ['car_wash','casino','commercial','fast_food','food_court',
                           'fuel','greenhouse','office','pharmacy','retail','service',
                           'bureau_de_change','chiropractor','car_rental','dentist',
                           'language_school','veterinary','retail','cafe','internet_cafe',
                           'bicycle_repair_station','music_school']
        cull_institutional = ['bank','chapel','church','college','conference_centre',
                              'courthouse','hospital','place_of_worship','police',
                              'public_building','fire_station','research_institute',
                              'townhall','university','post_office','embassy','driving_school']
        cull_entertainment = ['bar','grandstand','nightclub','restaurant','dojo',
                              'stadium','theatre','cinema','pub','ice_cream','spa']
        cull_industrial = ['construction','data_center','garage','industrial',
                           'recycling','storage','train_station','warehouse','brownfield',
                           'railway','ferry_terminal']
        cull_civic = ['arts_centre','clinic','community_centre','library','school','bus_station',
                      'shelter','toilets','social_centre','social_facility','childcare','doctors']
        series1 = replace_values (series1,cull_furniture,"nan")
        series1 = replace_values (series1,cull_residential,"residential")
        series1 = replace_values (series1,cull_commercial,"commercial")
        series1 = replace_values (series1,cull_institutional,"institutional")
        series1 = replace_values (series1,cull_entertainment,"entertainment")
        series1 = replace_values (series1,cull_industrial,"industrial")
        series1 = replace_values (series1,cull_civic,"civic")    
        return series1
    bld.use_points = reclassify_uses (bld.use_points)
    bld.use_building = reclassify_uses (bld.use_building)
    bld.use_zones = reclassify_uses (bld.use_zones)
    bld = bld.fillna(value='-')

    # Aggregate joined data and calculate areas
    bld = bld.to_crs(epsg=3786)     
    bld['area'] = bld['geometry'].area
    bld = bld.to_crs(epsg=4326)   
    bld['volume'] = bld['area']*bld['height_est']
    bld = bld[['fid','area','height_est','volume','use_building','use_points','use_zones','geometry']]
    def f(x):
     return pd.Series(dict(area = x['area'].mean(), 
                           height = x['height_est'].mean(),
                           volume = x['volume'].mean(),
                           use_building = "%s" % ' , '.join(x['use_building']),
                           use_points = "%s" % ' , '.join(x['use_points']),
                           use_zones = "%s" % ' , '.join(x['use_zones'])))
    bld = bld.groupby('fid').apply(f)
    bld['fid'] = bld.index
    bld = bld.join(bld_raw,on='fid',how='left',rsuffix='_r')
    bld = gpd.GeoDataFrame(bld)
    bld.crs = {'init' :'epsg:4326'}
    bld['uses'] = bld['use_building']+' , '+bld['use_points']

    # Estimate use areas per building
    def count_residential (row):
        if ("residential" in row['uses']): 
            return int(row['uses'].count("residential"))
        elif ("residential" not in row['uses'])&("residential" in row['use_zones']):
            return int(1)
        else:
            return np.nan
    bld['n_residential'] = bld.apply (lambda row: count_residential (row), axis=1)
    bld = bld.fillna(value=0)
    def count_nonresidential (use_type):
        def count_row (row):
            if (use_type in row['uses']): 
                return int(row['uses'].count(use_type))
            else:
                return np.nan
        bld["n_"+use_type] = bld.apply (lambda row: count_row (row), axis=1)
        return bld
    bld = count_nonresidential ("commercial")
    bld = count_nonresidential ("institutional")
    bld = count_nonresidential ("entertainment")
    bld = count_nonresidential ("industrial")
    bld = count_nonresidential ("civic")
    bld = bld.fillna(value=0)
    def a_residential (row):
        if (row['n_residential']>0)&((row['n_commercial']>0)|(row['n_entertainment']>0)|(row['n_civic']>0))&(row['height']>=4): 
            return row['area'] * (row['height'] - 2)
        elif ((row['n_residential']>0)&(row['n_commercial']==0)&(row['n_entertainment']==0)&(row['n_civic']==0)):
            return row['volume']
        else:
            return np.nan    
    bld['a_residential'] = bld.apply (lambda row: a_residential (row), axis=1)
    bld['n_nonresidential'] = bld['n_commercial']+bld['n_entertainment']+bld['n_civic']+bld['n_industrial']+bld['n_institutional']
    def a_nonresidential (use_type):
        def a_row (row):
            if (row['n_residential']==0)&(row['n_nonresidential']>0): 
                return (row["n_"+use_type]/row['n_nonresidential'])*row['volume']
            else:
                return np.nan
        bld["a_"+use_type] = bld.apply (lambda row: a_row (row), axis=1)
        return bld
    bld = a_nonresidential ("commercial")
    bld = a_nonresidential ("institutional")
    bld = a_nonresidential ("entertainment")
    bld = a_nonresidential ("industrial")
    bld = a_nonresidential ("civic")
    bld['a_nonresidential'] = bld['a_commercial']+bld['a_entertainment']+bld['a_civic']+bld['a_industrial']+bld['a_institutional']
    bld = bld.fillna(value=0)
    
    # Simplify land uses
    mixed = (bld['n_residential']>0)&((bld['n_commercial']>0)|(bld['n_entertainment']>0)|(bld['n_civic']>0)) 
    residential = (bld['n_residential']>0)&(bld['n_commercial']==0)&(bld['n_entertainment']==0)&(bld['n_civic']==0)
    industrial = (bld['n_residential']==0)&(bld['n_nonresidential']!=0)&(bld['n_industrial']>=(bld['n_nonresidential']/2))
    institutional = (bld['n_residential']==0)&(bld['n_nonresidential']!=0)&(bld['n_institutional']>=(bld['n_nonresidential']/2))
    entertainment = (bld['n_residential']==0)&(bld['n_nonresidential']!=0)&(bld['n_entertainment']>=(bld['n_nonresidential']/2))
    civic = (bld['n_residential']==0)&(bld['n_nonresidential']!=0)&(bld['n_civic']>=(bld['n_nonresidential']/2))
    commercial = (bld['n_residential']==0)&(bld['n_nonresidential']!=0)&(bld['n_commercial']>=(bld['n_nonresidential']/2))
    unknown = (bld['n_residential']==0)&(bld['n_nonresidential']==0)
    conditions = [mixed,residential,commercial,institutional,entertainment,industrial,civic,unknown]
    choices = ["mixed","residential","commercial","institutional","entertainment","industrial","civic","unknown"]
    bld['use'] = np.select(conditions, choices)    
    bld.plot(column='use')
        
    # Pick columns and export shapefile               
    bld = bld[['fid','area','height','volume','use_building','use_points','use_zones',
               'geometry','a_residential','a_commercial','a_institutional','a_entertainment',
               'a_industrial','a_civic','a_nonresidential','use']]
    bld = bld.to_crs(epsg=3395)     
    bld.to_file(driver='ESRI Shapefile',filename=filename_bld,crs_wkt='3395')
    return print("--- %s minutes ---" %((time.clock()-start_time)/60))

root_folder = 'C:\MEGA\OSMnx'
land_use ("Vila dos Atletas, Rio de Janeiro, Brazil",root_folder)
land_use ("Milton Wong Plaza, Vancouver, Canada",root_folder)