# -*- coding: utf-8 -*-
"""
Created on Fri Jan 18 12:30:59 2019

@author: nicholas-martino
nicholas.martino@hotmail.com
"""

from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsProcessing,QgsProcessingAlgorithm,QgsProcessingParameterFeatureSource,QgsProcessingParameterVectorLayer,QgsProcessingParameterNumber,QgsProcessingException,QgsFeatureSink,QgsProcessingParameterFeatureSink)
import processing


class Walkability(QgsProcessingAlgorithm):

    initial_points = 'initial_points'    
    analysed_radius = 'analysed_radius'
    aggregation_scale = 'aggregation_scale'     
    street_network = 'street_network'
    intersections = 'intersections'
    bcaa_fabric = 'bcaa_fabric'
    sample_input ='sample_input'
    sample_output = 'sample_output'
    source = 'source'
     
    def __init__(self):
        super().__init__()

    def name(self):
        return "Urban Walkability"

    def tr(self, text):
        return QCoreApplication.translate("Urban Walkability", text)

    def displayName(self):
        return self.tr("Urban Walkability")

    def group(self):
        return self.tr("Urban Walkability")

    def groupId(self):
        return "Urban Walkability"

    def shortHelpString(self):
        return self.tr(
'''The algorithm calculates walkability-related measurements for sample features located at the surroundings of certain points in space, based on data classified by the British Columbia Assessment Authority (https://www.bcassessment.ca/). Be sure to input all layers with the same coordinate reference system. 
INPUTS:
Initial Point(s) = A point layer to define which features from the Sample will be analysed;
Analysed Radius = A network radius from the Initial Point(s) that will define which Sample features will be analysed;
Aggregation Scale = A network radius from each Sample feature thtat will define which BCAA Fabric Layer features will be aggregate for the analysis;
Street Network = A line layer that will define the street network to search features;
Intersections = A point layer for analysing the intersection density of the network;
BCAA Fabric Layer = A polygon layer based on the British Columbia Asssessment Authority land fabric data;
Sample = Any geometry layer that will be used as sample units for the analysis.
OUTPUTS:
res = Area of residential use aggregated based on the defined scale.
ret = Area of retail use aggregated based on the defined scale.
off = Area of office use aggregated based on the defined scale.
ins = Area of institutional use aggregated based on the defined scale.
ent = Area of entertainment use aggregated based on the defined scale.
intersection_density = (Number of intersections) / (Sum of the length of the street network lines within the analysed radius)
residential_density = (Number of bedrooms) / (Residential area)
retail_far = (Retail area) / (Sum of retail, office and entertainment areas)
land_use_mix = Logarithmic land use mix index as defined by Frank (2010)
job_density = (Sum of retail and office areas) / (Total built area)
lfw = Walkability measure mostly based on the index developed by Frank (2010). (2 * Intersection density) + Retail floor area ratio + Residential density + Land use mix; 
pnw = Potential neighborhood walkability measure conceptually based on indicators related to a "social performativity of space" (Marcus 2010). Accessibility (intersection density) + Density (residential density) + Diversity (Simpson's index of land use diversity);                         
Nicholas Martino. nicholas.martino@hotmail.com''')

    def helpUrl(self):
        return "https://qgis.org"

    def createInstance(self):
        return type(self)()

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer(
            self.initial_points,
            self.tr("Initial Point(s)"),
            [QgsProcessing.TypeVectorPoint], None, False))
        self.addParameter(QgsProcessingParameterNumber(
            self.analysed_radius, 
            self.tr("Analysed Radius"), 
            QgsProcessingParameterNumber.Double,
            QVariant(800)))
        self.addParameter(QgsProcessingParameterNumber(
            self.aggregation_scale, 
            self.tr("Aggregation Scale"), 
            QgsProcessingParameterNumber.Double,
            QVariant(1000)))
        self.addParameter(QgsProcessingParameterVectorLayer(
            self.street_network,
            self.tr("Street Network"),            
            [QgsProcessing.TypeVectorAnyGeometry], None, False))
        self.addParameter(QgsProcessingParameterVectorLayer(
            self.intersections,
            self.tr("Intersections"),            
            [QgsProcessing.TypeVectorPoint], None, False))
        self.addParameter(QgsProcessingParameterVectorLayer(
            self.bcaa_fabric,
            self.tr("BCAA Fabric Layer"), 
            [QgsProcessing.TypeVectorPolygon], None, False))        
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.sample_input,
            self.tr("Sample"),
            [QgsProcessing.TypeVectorAnyGeometry], None, False))
        self.addParameter(QgsProcessingParameterFeatureSink(
            self.sample_output,
            self.tr("Walkability")))

    def processAlgorithm(self, parameters, context, feedback):
        initial_points = self.parameterAsVectorLayer(parameters, self.initial_points, context)
        analysed_radius = self.parameterAsDouble(parameters, self.analysed_radius,context)
        aggregation_scale = self.parameterAsDouble(parameters, self.aggregation_scale,context)        
        street_network = self.parameterAsVectorLayer(parameters, self.street_network, context)
        intersections = self.parameterAsVectorLayer(parameters, self.intersections, context)
        bcaa_fabric = self.parameterAsVectorLayer(parameters, self.bcaa_fabric, context)
        sample_input = self.parameterAsVectorLayer(parameters, self.sample_input, context)
        #output_path = self.parameterAsOutputLayer(parameters, self.sample_output, context)

        # Analyze network reach         
        outputs1 = {}
        outputs1['qgis:serviceareafromlayer_2']=processing.run('qgis:serviceareafromlayer', 
               {'INPUT':street_network,'START_POINTS':initial_points,'STRATEGY':0,
                'TRAVEL_COST':analysed_radius,'DIRECTION_FIELD':None,'VALUE_FORWARD':'',
                'VALUE_BACKWARD':'','VALUE_BOTH':'','DEFAULT_DIRECTION':2,'SPEED_FIELD':None,
                'DEFAULT_SPEED':5,'TOLERANCE':0,'INCLUDE_BOUNDS':False,'OUTPUT_LINES':'memory:'})
        #results['network_analysis']=outputs['qgis:serviceareafromlayer_2']['OUTPUT_LINES']
        outputs1['qgis:minimumboundinggeometry_1']=processing.run('qgis:minimumboundinggeometry',
               {'INPUT':outputs1['qgis:serviceareafromlayer_2']['OUTPUT_LINES'],'OUTPUT':'memory:','TYPE':3}, context=context, feedback=feedback)
        outputs1['native:extractbylocation_1']=processing.run('native:extractbylocation', 
               {'INPUT':sample_input,'INTERSECT':outputs1['qgis:minimumboundinggeometry_1']['OUTPUT'],'PREDICATE':0,'OUTPUT':'memory:'}, context=context, feedback=feedback)
        #source = outputs1['native:extractbylocation_1']['OUTPUT']


        outputs = {}
        outputs['native:addautoincrementalfield_1']=processing.run('native:addautoincrementalfield', {'FIELD_NAME':"id_elements",'INPUT':outputs1['native:extractbylocation_1']['OUTPUT'],'SORT_ASCendING':True,'FIELD_NAME':"id_elements",'SORT_NULLS_FIRST':False,'START':1,'OUTPUT':'memory:'}, context=context, feedback=feedback)
        outputs['native:centroids_1']=processing.run('native:centroids', {'ALL_PARTS':False,'INPUT':outputs['native:addautoincrementalfield_1']['OUTPUT'],'OUTPUT':'memory:'}, context=context, feedback=feedback)
        outputs['qgis:serviceareafromlayer_1']=processing.run('qgis:serviceareafromlayer', {'DEFAULT_DIRECTION':2,'DEFAULT_SPEED':5, 'INCLUDE_BOUNDS':True, 'INPUT':street_network, 'START_POINTS':outputs['native:centroids_1']['OUTPUT'],'STRATEGY':0,'TOLERANCE':5,'TRAVEL_COST':aggregation_scale,'OUTPUT_LINES':'memory:'}, context=context, feedback=feedback)
        outputs['qgis:fieldcalculator_2']=processing.run('qgis:fieldcalculator', {'FIELD_LENGTH':10,'FIELD_NAME':"buffer_length",'FIELD_PRECISION':2,'FIELD_TYPE':0, 'FORMULA':'$length', 'INPUT':outputs['qgis:serviceareafromlayer_1']['OUTPUT_LINES'],'NEW_FIELD':True,'OUTPUT':'memory:'}, context=context, feedback=feedback)
        outputs['qgis:minimumboundinggeometry_2']=processing.run('qgis:minimumboundinggeometry', {'INPUT':outputs['qgis:fieldcalculator_2']['OUTPUT'],'TYPE':3,'OUTPUT':'memory:'}, context=context, feedback=feedback)
        
        # Eliminate close intersections
        outputs['native:extractbylocation_3']=processing.run('native:extractbylocation', {'INPUT':intersections,'INTERSECT':outputs['qgis:minimumboundinggeometry_2']['OUTPUT'],'PREDICATE':0,'OUTPUT':'memory:'}, context=context, feedback=feedback)
        #results['old-intersections']=outputs['native:extractbylocation_3']['OUTPUT']
        outputs['native:extractbylocation_2']=processing.run('native:extractbylocation', {'INPUT':bcaa_fabric,'INTERSECT':outputs['qgis:minimumboundinggeometry_2']['OUTPUT'],'PREDICATE':0,'OUTPUT':'memory:'}, context=context, feedback=feedback)
        outputs['qgis:fieldcalculator_25']=processing.run('qgis:fieldcalculator', {'FIELD_LENGTH':254,'FIELD_NAME':"PROPERTY_ID_string",'FIELD_PRECISION':10,'FIELD_TYPE':2,'FORMULA':"PROPERTY_ID",'INPUT':outputs['native:extractbylocation_2']['OUTPUT'],'NEW_FIELD':True,'OUTPUT':'memory:'}, context=context, feedback=feedback)
        outputs['native:buffer_1']=processing.run('native:buffer', {'DISSOLVE':True,'DISTANCE':10,'end_CAP_STYLE':0,'INPUT':outputs['native:extractbylocation_3']['OUTPUT'],'JOIN_STYLE':0,'MITER_LIMIT':2,'SEGMENTS':5,'OUTPUT':'memory:'}, context=context, feedback=feedback)
        outputs['native:multiparttosingleparts_1']=processing.run('native:multiparttosingleparts', {'INPUT':outputs['native:buffer_1']['OUTPUT'],'OUTPUT':'memory:'}, context=context, feedback=feedback)
        #results['buffer-intersections']=outputs['native:multiparttosingleparts_1']['OUTPUT']
        
         # Reclassify land uses from BC assessment data        
        outputs['qgis:fieldcalculator_11']=processing.run('qgis:fieldcalculator', {'FIELD_LENGTH':30,'FIELD_NAME':"use",'FIELD_PRECISION':0,'FIELD_TYPE':2, 
        'FORMULA':'''case 
        when "PRIMARY_ACTUAL_USE" = '000 - Single Family Dwelling' OR "PRIMARY_ACTUAL_USE"  = '030 - Strata-Lot Residence (Condominium)' OR "PRIMARY_ACTUAL_USE" = '032 - Residential Dwelling with Suite' OR "PRIMARY_ACTUAL_USE" = '033 - Duplex, Non-Strata Side by Side or Front / Back' OR "PRIMARY_ACTUAL_USE" = '034 - Duplex, Non-Strata Up / Down' OR "PRIMARY_ACTUAL_USE" = '035 - Duplex, Strata Side by Side' OR "PRIMARY_ACTUAL_USE" = '036 - Duplex, Strata Front / Back' OR "PRIMARY_ACTUAL_USE" = '039 - Row Housing (Single Unit Ownership)' OR "PRIMARY_ACTUAL_USE" = '041 - Duplex, Strata Up / Down' OR "PRIMARY_ACTUAL_USE" = '047 - Triplex' OR "PRIMARY_ACTUAL_USE" = '050 - Multi-Family (Apartment Block)' OR "PRIMARY_ACTUAL_USE" = '052 - Multi-Family (Garden Apartment & Row Housing)' OR "PRIMARY_ACTUAL_USE" = '053 - Multi-Family (Conversion)' OR "PRIMARY_ACTUAL_USE" = '054 - Multi-Family (High-Rise)' OR "PRIMARY_ACTUAL_USE" = '055 - Multi-Family (Minimal Commercial)' OR "PRIMARY_ACTUAL_USE" = '056 - Multi-Family (Residential Hotel)' OR "PRIMARY_ACTUAL_USE" = '057 - Stratified Rental Townhouse' OR "PRIMARY_ACTUAL_USE" = '058 - Stratified Rental Apartment (Frame Construction)' OR "PRIMARY_ACTUAL_USE" = '059 - Stratified Rental Apartment (Hi-Rise Construction)' OR "PRIMARY_ACTUAL_USE" = '060 - 2 Acres Or More (Single Family Dwelling, Duplex)' OR "PRIMARY_ACTUAL_USE" = '285 - Seniors Licensed Care' OR "PRIMARY_ACTUAL_USE" = '286 - Seniors Independent & Assisted Living' then 'residential' 
        when "PRIMARY_ACTUAL_USE" = '001 - Vacant Residential Less Than 2 Acres' OR "PRIMARY_ACTUAL_USE" = '051 - Multi-Family (Vacant)' OR "PRIMARY_ACTUAL_USE" = '201 - Vacant IC&I' OR "PRIMARY_ACTUAL_USE" = '421 - Vacant' OR "PRIMARY_ACTUAL_USE" = '422 - IC&I Water Lot (Vacant)' OR "PRIMARY_ACTUAL_USE" = '601 - Civic, Institutional & Recreational (Vacant)' then 'vacant' 
        when "PRIMARY_ACTUAL_USE" = '020 - Residential Outbuilding Only' OR"PRIMARY_ACTUAL_USE" = '029 - Strata Lot (Parking Residential)' OR "PRIMARY_ACTUAL_USE" = '043 - Parking (Lot Only, Paved Or Gravel-Res)' OR "PRIMARY_ACTUAL_USE" = '219 - Strata Lot (Parking Commercial)' OR "PRIMARY_ACTUAL_USE" = '260 - Parking (Lot Only, Paved Or Gravel-Com)' OR "PRIMARY_ACTUAL_USE" = '262 - Parking Garage' OR "PRIMARY_ACTUAL_USE" = '490 - Parking Lot Only (Paved Or Gravel)' then 'parking' 
        when "PRIMARY_ACTUAL_USE" = '002 - Property Subject To Section 19(8)' OR "PRIMARY_ACTUAL_USE" = '070 - 2 Acres Or More (Outbuilding)' OR "PRIMARY_ACTUAL_USE" = '190 - Other' OR "PRIMARY_ACTUAL_USE" = '200 - Store(S) And Service Commercial' OR "PRIMARY_ACTUAL_USE" = '205 - Big Box' OR "PRIMARY_ACTUAL_USE" = '216 - Commercial Strata-Lot' OR "PRIMARY_ACTUAL_USE" = '220 - Automobile Dealership' OR "PRIMARY_ACTUAL_USE" = '222 - Service Station' OR "PRIMARY_ACTUAL_USE" = '224 - Self-Serve Service Station' OR "PRIMARY_ACTUAL_USE" = '226 - Car Wash' OR "PRIMARY_ACTUAL_USE" = '227 - Automobile Sales (Lot)' OR "PRIMARY_ACTUAL_USE" = '228 - Automobile Paint Shop, Garages, Etc.' OR "PRIMARY_ACTUAL_USE" = '230 - Hotel' OR "PRIMARY_ACTUAL_USE" = '232 - Motel & Auto Court' OR "PRIMARY_ACTUAL_USE" = '233 - Individual Strata Lot (Hotel/Motel)' OR "PRIMARY_ACTUAL_USE" = '237 - Bed & Breakfast Operation 4 Or More Units' OR "PRIMARY_ACTUAL_USE" = '239 - Bed & Breakfast Operation Less Than 4 Units' OR "PRIMARY_ACTUAL_USE" = '240 - Greenhouses And Nurseries (Not Farm Class)' OR "PRIMARY_ACTUAL_USE" = '257 - Fast Food Restaurants' OR "PRIMARY_ACTUAL_USE" = '258 - Drive-In Restaurant' OR "PRIMARY_ACTUAL_USE" = '288 - Sign Or Billboard Only' then 'other' 
        when "PRIMARY_ACTUAL_USE" = '120 - Vegetable & Truck' OR "PRIMARY_ACTUAL_USE" = '170 - Poultry' OR "PRIMARY_ACTUAL_USE" = '180 - Mixed' then 'agriculture' 
        when "PRIMARY_ACTUAL_USE" = '202 - Store(S) And Living Quarters' OR "PRIMARY_ACTUAL_USE" = '209 - Shopping Centre (Neighbourhood)' OR "PRIMARY_ACTUAL_USE" = '211 - Shopping Centre (Community)' OR "PRIMARY_ACTUAL_USE" = '212 - Department Store - Stand Alone' OR "PRIMARY_ACTUAL_USE" = '213 - Shopping Centre (Regional)' OR "PRIMARY_ACTUAL_USE" = '214 - Retail Strip' OR "PRIMARY_ACTUAL_USE" = '215 - Food Market' OR "PRIMARY_ACTUAL_USE" = '225 - Convenience Store/Service Station' then 'retail' 
        when "PRIMARY_ACTUAL_USE" = '203 - Stores And/Or Offices With Apartments' OR "PRIMARY_ACTUAL_USE" = '204 - Store(S) And Offices' OR "PRIMARY_ACTUAL_USE" = '208 - Office Building (Primary Use)' then 'office' 
        when "PRIMARY_ACTUAL_USE" = '250 - Theatre Buildings' OR "PRIMARY_ACTUAL_USE" = '254 - Neighbourhood Pub' OR "PRIMARY_ACTUAL_USE" = '256 - Restaurant Only' OR "PRIMARY_ACTUAL_USE" = '266 - Bowling Alley' OR "PRIMARY_ACTUAL_USE" = '270 - Hall (Community, Lodge, Club, Etc.)' OR "PRIMARY_ACTUAL_USE" = '280 - Marine Facilities (Marina)' OR "PRIMARY_ACTUAL_USE" = '600 - Recreational & Cultural Buildings (Includes Curling' OR "PRIMARY_ACTUAL_USE" = '610 - Parks & Playing Fields' OR "PRIMARY_ACTUAL_USE" = '612 - Golf Courses (Includes Public & Private)' OR "PRIMARY_ACTUAL_USE" = '654 - Recreational Clubs, Ski Hills' then 'entertainment' 
        when "PRIMARY_ACTUAL_USE" = '210 - Bank' OR "PRIMARY_ACTUAL_USE" = '620 - Government Buildings (Includes Courthouse, Post Office' OR "PRIMARY_ACTUAL_USE" = '625 - Garbage Dumps, Sanitary Fills, Sewer Lagoons, Etc.' OR "PRIMARY_ACTUAL_USE" = '630 - Works Yards' OR "PRIMARY_ACTUAL_USE" = '634 - Government Research Centres (Includes Nurseries &' OR "PRIMARY_ACTUAL_USE" = '640 - Hospitals (Nursing Homes Refer To Commercial Section).' OR "PRIMARY_ACTUAL_USE" = '642 - Cemeteries (Includes Public Or Private).' OR "PRIMARY_ACTUAL_USE" = '650 - Schools & Universities, College Or Technical Schools' OR "PRIMARY_ACTUAL_USE" = '652 - Churches & Bible Schools' then 'institutional' 
        when "PRIMARY_ACTUAL_USE" = '217 - Air Space Title' OR "PRIMARY_ACTUAL_USE" = '272 - Storage & Warehousing (Open)' OR "PRIMARY_ACTUAL_USE" = '273 - Storage & Warehousing (Closed)' OR "PRIMARY_ACTUAL_USE" = '274 - Storage & Warehousing (Cold)' OR "PRIMARY_ACTUAL_USE" = '275 - Self Storage' OR "PRIMARY_ACTUAL_USE" = '276 - Lumber Yard Or Building Supplies' OR "PRIMARY_ACTUAL_USE" = '400 - Fruit & Vegetable' OR "PRIMARY_ACTUAL_USE" = '401 - Industrial (Vacant)' OR "PRIMARY_ACTUAL_USE" = '402 - Meat & Poultry' OR "PRIMARY_ACTUAL_USE" = '403 - Sea Food' OR "PRIMARY_ACTUAL_USE" = '404 - Dairy Products' OR "PRIMARY_ACTUAL_USE" = '405 - Bakery & Biscuit Manufacturing' OR "PRIMARY_ACTUAL_USE" = '406 - Confectionery Manufacturing & Sugar Processing' OR "PRIMARY_ACTUAL_USE" = '408 - Brewery' OR "PRIMARY_ACTUAL_USE" = '414 - Miscellaneous (Food Processing)' OR "PRIMARY_ACTUAL_USE" = '419 - Sash & Door' OR "PRIMARY_ACTUAL_USE" = '423 - IC&I Water Lot (Improved)' OR "PRIMARY_ACTUAL_USE" = '425 - Paper Box, Paper Bag, And Other Paper Remanufacturing.' OR "PRIMARY_ACTUAL_USE" = '428 - Improved' OR "PRIMARY_ACTUAL_USE" = '429 - Miscellaneous (Forest And Allied Industry)' OR "PRIMARY_ACTUAL_USE" = '449 - Miscellaneous (Mining And Allied Industries)' OR "PRIMARY_ACTUAL_USE" = '452 - Leather Industry' OR "PRIMARY_ACTUAL_USE" = '454 - Textiles & Knitting Mills' OR "PRIMARY_ACTUAL_USE" = '456 - Clothing Industry' OR "PRIMARY_ACTUAL_USE" = '458 - Furniture & Fixtures Industry' OR "PRIMARY_ACTUAL_USE" = '460 - Printing & Publishing Industry' OR "PRIMARY_ACTUAL_USE" = '462 - Primary Metal Industries (Iron & Steel Mills,' OR "PRIMARY_ACTUAL_USE" = '464 - Metal Fabricating Industries' OR "PRIMARY_ACTUAL_USE" = '466 - Machinery Manufacturing (Excluding Electrical)' OR "PRIMARY_ACTUAL_USE" = '470 - Electrical & Electronics Products Industry' OR "PRIMARY_ACTUAL_USE" = '472 - Chemical & Chemical Products Industries' OR "PRIMARY_ACTUAL_USE" = '474 - Miscellaneous & (Industrial Other)' OR "PRIMARY_ACTUAL_USE" = '476 - Grain Elevators' OR "PRIMARY_ACTUAL_USE" = '478 - Docks & Wharves' OR "PRIMARY_ACTUAL_USE" = '500 - Railway' OR "PRIMARY_ACTUAL_USE" = '505 - Marine & Navigational Facilities (Includes Ferry' OR "PRIMARY_ACTUAL_USE" = '510 - Bus Company, Including Street Railway' OR "PRIMARY_ACTUAL_USE" = '520 - Telephone' OR "PRIMARY_ACTUAL_USE" = '530 - Telecommunications (Other Than Telephone)' OR "PRIMARY_ACTUAL_USE" = '560 - Water Distribution Systems' OR "PRIMARY_ACTUAL_USE" = '580 - Electrical Power Systems (Including Non-Utility' then 'industrial' 
        else NULL end''',
        'INPUT':outputs['qgis:fieldcalculator_25']['OUTPUT'],'OUTPUT':'memory:','NEW_FIELD':True}, context=context, feedback=feedback)
        outputs['native:centroids_2']=processing.run('native:centroids', {'INPUT':outputs['native:multiparttosingleparts_1']['OUTPUT'],'OUTPUT':'memory:'}, context=context, feedback=feedback)
        outputs['qgis:fieldcalculator_12']=processing.run('qgis:fieldcalculator', {'FIELD_LENGTH':10,'FIELD_NAME':"area",'FIELD_PRECISION':2,'FIELD_TYPE':0,
        'FORMULA':'''case
        when "TOTAL_FINISHED_AREA" IS NOT NULL then "TOTAL_FINISHED_AREA"
        when "STRATA_UNIT_AREA" IS NOT NULL then "STRATA_UNIT_AREA"
        when "GROSS_LEASABLE_AREA" IS NOT NULL then "GROSS_LEASABLE_AREA" 
        when "GROSS_BUILDING_AREA" IS NOT NULL then "GROSS_BUILDING_AREA" 
        else 0 end''',
        'INPUT':outputs['qgis:fieldcalculator_11']['OUTPUT'],'NEW_FIELD':True,'OUTPUT':'memory:'}, context=context, feedback=feedback)
    
        # Calculate areas per land use
        outputs['native:addautoincrementalfield_2']=processing.run('native:addautoincrementalfield', {'FIELD_NAME':"id_intersections", 'INPUT':outputs['native:centroids_2']['OUTPUT'],'SORT_ASCendING':True,'SORT_NULLS_FIRST':False,'START':1,'OUTPUT':'memory:'}, context=context, feedback=feedback)
        #results['new-intersections']=outputs['native:addautoincrementalfield_2']['OUTPUT']
        outputs['qgis:fieldcalculator_3']=processing.run('qgis:fieldcalculator', {'FIELD_LENGTH':10,'FIELD_NAME':"res",'FIELD_PRECISION':2,'FIELD_TYPE':0,'FORMULA':'''case when "use" = 'residential' then "area" else 0 end''','INPUT':outputs['qgis:fieldcalculator_12']['OUTPUT'],'NEW_FIELD':True,'OUTPUT':'memory:'}, context=context, feedback=feedback)
        outputs['qgis:fieldcalculator_4']=processing.run('qgis:fieldcalculator', {'FIELD_LENGTH':10,'FIELD_NAME':"ret",'FIELD_PRECISION':2,'FIELD_TYPE':0,'FORMULA':'''case when "use" = 'retail' then "area" else 0 end''','INPUT':outputs['qgis:fieldcalculator_3']['OUTPUT'],'NEW_FIELD':True,'OUTPUT':'memory:'}, context=context, feedback=feedback)
        outputs['qgis:snapgeometries_2']=processing.run('qgis:snapgeometries', {'BEHAVIOR':3,'INPUT':outputs['native:addautoincrementalfield_2']['OUTPUT'],'REFERENCE_LAYER':street_network,'TOLERANCE':100,'OUTPUT':'memory:'}, context=context, feedback=feedback)
        outputs['qgis:fieldcalculator_5']=processing.run('qgis:fieldcalculator', {'FIELD_LENGTH':10,'FIELD_NAME':"off",'FIELD_PRECISION':2,'FIELD_TYPE':0,'FORMULA':'''case when "use" = 'office' then "area" else 0 end''','INPUT':outputs['qgis:fieldcalculator_4']['OUTPUT'],'NEW_FIELD':True,'OUTPUT':'memory:'}, context=context, feedback=feedback)
        outputs['qgis:fieldcalculator_6']=processing.run('qgis:fieldcalculator', {'FIELD_LENGTH':10,'FIELD_NAME':"ins",'FIELD_PRECISION':2,'FIELD_TYPE':0,'FORMULA':'''case when "use" = 'institutional' then "area" else 0 end''','INPUT':outputs['qgis:fieldcalculator_5']['OUTPUT'],'NEW_FIELD':True,'OUTPUT':'memory:'}, context=context, feedback=feedback)
        outputs['native:buffer_3']=processing.run('native:buffer', {'DISSOLVE':False,'DISTANCE':2,'end_CAP_STYLE':0,'INPUT':outputs['qgis:snapgeometries_2']['OUTPUT'],'JOIN_STYLE':0,'MITER_LIMIT':2,'SEGMENTS':5,'OUTPUT':'memory:'}, context=context, feedback=feedback)
        outputs['qgis:joinbylocationsummary_2']=processing.run('qgis:joinbylocationsummary', {'DISCARD_NONMATCHING':False,'INPUT':outputs['qgis:fieldcalculator_2']['OUTPUT'],'JOIN':outputs['native:buffer_3']['OUTPUT'],'JOIN_FIELDS':"id_intersections",'PREDICATE':0,'SUMMARIES':0,'OUTPUT':'memory:'}, context=context, feedback=feedback)
        outputs['qgis:fieldcalculator_17']=processing.run('qgis:fieldcalculator', {'FIELD_LENGTH':10,'FIELD_NAME':"ent",'FIELD_PRECISION':2,'FIELD_TYPE':0,'FORMULA':'''case when "use" = 'entertainment' then "area" else 0 end''','INPUT':outputs['qgis:fieldcalculator_6']['OUTPUT'],'NEW_FIELD':True,'OUTPUT':'memory:'}, context=context, feedback=feedback)
        aggregates = [{'input':'area','aggregate':'sum','delimiter':',','name':'area','type':6,'length':10,'precision':2},
                      {'input':'NUMBER_OF_BEDROOMS','aggregate':'sum','delimiter':',','name':'bedrooms','type':6,'length':10,'precision':0},
                      {'input':'res','aggregate':'sum','delimiter':',','name':'res','type':6,'length':10,'precision':2},
                      {'input':'ret','aggregate':'sum','delimiter':',','name':'ret','type':6,'length':10,'precision':2},
                      {'input':'off','aggregate':'sum','delimiter':',','name':'off','type':6,'length':10,'precision':2},
                      {'input':'ins','aggregate':'sum','delimiter':',','name':'ins','type':6,'length':10,'precision':2},
                      {'input':'ent','aggregate':'sum','delimiter':',','name':'ent','type':6,'length':10,'precision':2}]      
        outputs['qgis:aggregate_1']=processing.run('qgis:aggregate',{'GROUP_BY':"PROPERTY_ID",'INPUT':outputs['qgis:fieldcalculator_17']['OUTPUT'],'AGGREGATES':aggregates,'OUTPUT':'memory:'}, context=context, feedback=feedback)       
        outputs['native:centroids_3']=processing.run('native:centroids', {'ALL_PARTS':False,'INPUT':outputs['qgis:aggregate_1']['OUTPUT'],'OUTPUT':'memory:'}, context=context, feedback=feedback)
        outputs['qgis:snapgeometries_1']=processing.run('qgis:snapgeometries', {'BEHAVIOR':3,'INPUT':outputs['native:centroids_3']['OUTPUT'],'REFERENCE_LAYER':street_network,'TOLERANCE':100,'OUTPUT':'memory:'}, context=context, feedback=feedback)
        outputs['native:buffer_2']=processing.run('native:buffer', {'DISSOLVE':False,'DISTANCE':3,'end_CAP_STYLE':0,'INPUT':outputs['qgis:snapgeometries_1']['OUTPUT'],'JOIN_STYLE':0,'MITER_LIMIT':2,'SEGMENTS':3,'OUTPUT':'memory:'}, context=context, feedback=feedback)
        
        # Join data in a single layer
        outputs['qgis:joinbylocationsummary_3']=processing.run('qgis:joinbylocationsummary', {'DISCARD_NONMATCHING':False,'INPUT':outputs['qgis:fieldcalculator_2']['OUTPUT'],'JOIN':outputs['native:buffer_2']['OUTPUT'],'JOIN_FIELDS':'''bedrooms;area;res;ret;off;ins;ent''','PREDICATE':0,'SUMMARIES':5,'OUTPUT':'memory:'}, context=context, feedback=feedback)
        outputs['native:joinattributestable_2']=processing.run('native:joinattributestable', {'DISCARD_NONMATCHING':False,'FIELD':"id_elements",'FIELDS_TO_COPY':"id_intersections_count",'FIELD_2':"id_elements",'INPUT':outputs['qgis:joinbylocationsummary_3']['OUTPUT'],'INPUT_2':outputs['qgis:joinbylocationsummary_2']['OUTPUT'],'METHOD':1,'OUTPUT':'memory:'}, context=context, feedback=feedback)
        outputs['native:joinattributestable_1']=processing.run('native:joinattributestable', {'DISCARD_NONMATCHING':False, 'FIELD':"id_elements", 'FIELD_2':"id_elements",'INPUT':outputs['native:addautoincrementalfield_1']['OUTPUT'],'INPUT_2':outputs['native:joinattributestable_2']['OUTPUT'],'METHOD':1,'OUTPUT':'memory:'}, context=context, feedback=feedback)
        outputs['qgis:fieldcalculator_26']=processing.run('qgis:fieldcalculator', {'FIELD_LENGTH':10,'FIELD_NAME':"intersection_count",'FIELD_PRECISION':4,'FIELD_TYPE':0,'FORMULA':'''to_real("id_intersections_count")''','INPUT':outputs['native:joinattributestable_1']['OUTPUT'],'NEW_FIELD':True,'OUTPUT':'memory:'}, context=context, feedback=feedback)
        
        # Calculate scores and index
        outputs['qgis:fieldcalculator_8']=processing.run('qgis:fieldcalculator', {'FIELD_LENGTH':10,'FIELD_NAME':"intersection_density",'FIELD_PRECISION':4,'FIELD_TYPE':0,'FORMULA':'''"intersection_count"/("buffer_length"/1000)''','INPUT':outputs['qgis:fieldcalculator_26']['OUTPUT'],'NEW_FIELD':True,'OUTPUT':'memory:'}, context=context, feedback=feedback)
        outputs['qgis:fieldcalculator_1']=processing.run('qgis:fieldcalculator', {'FIELD_LENGTH':10,'FIELD_NAME':"residential_density",'FIELD_PRECISION':4,'FIELD_TYPE':0,'FORMULA':'''"bedrooms_sum"/("res_sum"/10000)''','INPUT':outputs['qgis:fieldcalculator_8']['OUTPUT'],'NEW_FIELD':True,'OUTPUT':'memory:'}, context=context, feedback=feedback)
        outputs['qgis:fieldcalculator_7']=processing.run('qgis:fieldcalculator', {'FIELD_LENGTH':10,'FIELD_NAME':"job_density",'FIELD_PRECISION':4,'FIELD_TYPE':0,'FORMULA':'''("ret_sum"+"off_sum")/"area_sum"''','INPUT':outputs['qgis:fieldcalculator_1']['OUTPUT'],'NEW_FIELD':True,'OUTPUT':'memory:'}, context=context, feedback=feedback)
        outputs['qgis:fieldcalculator_9']=processing.run('qgis:fieldcalculator', {'FIELD_LENGTH':10,'FIELD_NAME':"land_use_mix",'FIELD_PRECISION':4,'FIELD_TYPE':0,
        'FORMULA':'''((
        ((("res_sum")/("res_sum"+"ret_sum"+"off_sum"+"ins_sum"+"ent_sum"))
        * (ln(("res_sum")/("res_sum"+"ret_sum"+"off_sum"+"ins_sum"+"ent_sum"))))+
        (((("ret_sum")/("res_sum"+"ret_sum"+"off_sum"+"ins_sum"+"ent_sum")))
        * (ln(("ret_sum")/("res_sum"+"ret_sum"+"off_sum"+"ins_sum"+"ent_sum"))))+
        ((("off_sum")/("res_sum"+"ret_sum"+"off_sum"+"ins_sum"+"ent_sum"))
        * (ln(("off_sum")/("res_sum"+"ret_sum"+"off_sum"+"ins_sum"+"ent_sum"))))+
        ((("ins_sum")/("res_sum"+"ret_sum"+"off_sum"+"ins_sum"+"ent_sum"))
        * (ln(("ins_sum")/("res_sum"+"ret_sum"+"off_sum"+"ins_sum"+"ent_sum"))))+
        ((("ent_sum")/("res_sum"+"ret_sum"+"off_sum"+"ins_sum"+"ent_sum"))
        * (ln(("ent_sum")/("res_sum"+"ret_sum"+"off_sum"+"ins_sum"+"ent_sum"))))
        )/ln(5))*-1''',
        'INPUT':outputs['qgis:fieldcalculator_7']['OUTPUT'],'NEW_FIELD':True,'OUTPUT':'memory:'}, context=context, feedback=feedback)
        outputs['qgis:fieldcalculator_23']=processing.run('qgis:fieldcalculator', {'FIELD_LENGTH':10,'FIELD_NAME':"use_diversity_simpson",'FIELD_PRECISION':4,'FIELD_TYPE':0,
        'FORMULA':'''(("res_sum"*( "res_sum" -1))+("ret_sum"*( "ret_sum" -1))+("off_sum"*( "off_sum" -1))+("ins_sum"*( "ins_sum" -1))+("ent_sum"*( "ent_sum" -1)))/(("area_sum")*("area_sum"-1))''',
        'INPUT':outputs['qgis:fieldcalculator_9']['OUTPUT'],'NEW_FIELD':True,'OUTPUT':'memory:'}, context=context, feedback=feedback)
        outputs['qgis:fieldcalculator_13']=processing.run('qgis:fieldcalculator', {'FIELD_LENGTH':10,'FIELD_NAME':"z_intersection_density",'FIELD_PRECISION':3,'FIELD_TYPE':0,
        'FORMULA':'''(("intersection_density"-mean("intersection_density"))/stdev("intersection_density"))''',
        'INPUT':outputs['qgis:fieldcalculator_23']['OUTPUT'],'NEW_FIELD':True,'OUTPUT':'memory:'}, context=context, feedback=feedback)
        outputs['qgis:fieldcalculator_14']=processing.run('qgis:fieldcalculator', {'FIELD_LENGTH':10,'FIELD_NAME':"z_use_diversity",'FIELD_PRECISION':3,'FIELD_TYPE':0,
        'FORMULA':'''(("land_use_mix"-mean("land_use_mix"))/stdev("land_use_mix"))''','INPUT':outputs['qgis:fieldcalculator_13']['OUTPUT'],'NEW_FIELD':True,'OUTPUT':'memory:'}, context=context, feedback=feedback)
        outputs['qgis:fieldcalculator_15']=processing.run('qgis:fieldcalculator', {'FIELD_LENGTH':10,'FIELD_NAME':"z_residential_density",'FIELD_PRECISION':3,'FIELD_TYPE':0,
        'FORMULA':'''(("residential_density"-mean("residential_density"))/stdev("residential_density"))''',
        'INPUT':outputs['qgis:fieldcalculator_14']['OUTPUT'],'NEW_FIELD':True,'OUTPUT':'memory:'}, context=context, feedback=feedback)
        outputs['qgis:fieldcalculator_16']=processing.run('qgis:fieldcalculator', {'FIELD_LENGTH':10,'FIELD_NAME':"z_job_density",'FIELD_PRECISION':3,'FIELD_TYPE':0,
        'FORMULA':'''(("job_density"-mean("job_density"))/stdev("job_density"))''',
        'INPUT':outputs['qgis:fieldcalculator_15']['OUTPUT'],'NEW_FIELD':True,'OUTPUT':'memory:'}, context=context, feedback=feedback)
        outputs['qgis:fieldcalculator_19']=processing.run('qgis:fieldcalculator', {'FIELD_LENGTH':10,'FIELD_NAME':"lfw_index",'FIELD_PRECISION':3,'FIELD_TYPE':0,
        'FORMULA':'''(2*"z_intersection_density")+"z_use_diversity"+"z_residential_density"+"z_job_density"''','INPUT':outputs['qgis:fieldcalculator_16']['OUTPUT'],'NEW_FIELD':True,'OUTPUT':'memory:'}, context=context, feedback=feedback)
        outputs['qgis:fieldcalculator_22']=processing.run('qgis:fieldcalculator', {'FIELD_LENGTH':10,'FIELD_NAME':"z_number_of_intersections",'FIELD_PRECISION':3,'FIELD_TYPE':0,
        'FORMULA':'''(("id_intersections_count"-mean("id_intersections_count"))/stdev("id_intersections_count"))''',
        'INPUT':outputs['qgis:fieldcalculator_19']['OUTPUT'],'NEW_FIELD':True,'OUTPUT':'memory:'}, context=context, feedback=feedback)
        outputs['qgis:fieldcalculator_20']=processing.run('qgis:fieldcalculator', {'FIELD_LENGTH':10,'FIELD_NAME':"z_number_of_bedrooms",'FIELD_PRECISION':3,'FIELD_TYPE':0,
        'FORMULA':'''(("bedrooms_sum"-mean("bedrooms_sum"))/stdev("bedrooms_sum"))''',
        'INPUT':outputs['qgis:fieldcalculator_22']['OUTPUT'],'NEW_FIELD':True,'OUTPUT':'memory:'}, context=context, feedback=feedback)
        outputs['qgis:fieldcalculator_21']=processing.run('qgis:fieldcalculator', {'FIELD_LENGTH':10,'FIELD_NAME':"z_ret",'FIELD_PRECISION':3,'FIELD_TYPE':0,
        'FORMULA':'''(("ret_sum"-mean("ret_sum"))/stdev("ret_sum"))''',
        'INPUT':outputs['qgis:fieldcalculator_20']['OUTPUT'],'NEW_FIELD':True,'OUTPUT':'memory:'}, context=context, feedback=feedback)
        outputs['qgis:fieldcalculator_24']=processing.run('qgis:fieldcalculator', {'FIELD_LENGTH':10,'FIELD_NAME':"z_use_diversity_simpson",'FIELD_PRECISION':4,'FIELD_TYPE':0,
        'FORMULA':'''(("use_diversity_simpson"-mean("use_diversity_simpson"))/stdev("use_diversity_simpson"))''',
        'INPUT':outputs['qgis:fieldcalculator_21']['OUTPUT'],'NEW_FIELD':True,'OUTPUT':'memory:'}, context=context, feedback=feedback)
        outputs['qgis:fieldcalculator_10']=processing.run('qgis:fieldcalculator', {'FIELD_LENGTH':10,'FIELD_NAME':"neighbourhood_vitality",'FIELD_PRECISION':4,'FIELD_TYPE':0,'FORMULA':'''"z_number_of_intersections" + "z_use_diversity" + (("z_number_of_bedrooms" + "z_ret")/2)''','INPUT':outputs['qgis:fieldcalculator_24']['OUTPUT'],'NEW_FIELD':True,'OUTPUT':'memory:'}, context=context, feedback=feedback)

        # Export processing results        
        source = outputs['qgis:fieldcalculator_10']['OUTPUT']
        (sink, dest_id) = self.parameterAsSink(parameters, self.sample_output, context,source.fields(), source.wkbType(), source.sourceCrs())        
        feedback.pushInfo('{}'.format(source.sourceCrs().authid()))
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.sample_output))
        total = 100.0 / source.featureCount() if source.featureCount() else 0
        features = source.getFeatures()
        feedback.pushInfo('Features:{}'.format(source.featureCount()))
        for current, feature in enumerate(features):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break
            # Add a feature in the sink
            sink.addFeature(feature, QgsFeatureSink.FastInsert)
            # Update the progress bar
            feedback.setProgress(int(current * total)) 
        results = {}
        results[self.sample_output] = {dest_id}


        return results       