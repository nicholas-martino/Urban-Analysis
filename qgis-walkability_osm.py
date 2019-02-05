# -*- coding: utf-8 -*-
"""
Created on Tue Jan  8 13:52:23 2019

@author: nicholas-martino

This is an automatic export from QGIS processing model tool for referencing purpuses only, 
it is not executable using python console in QGIS
"""

from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsProcessing,QgsProcessingAlgorithm,QgsProcessingParameterFeatureSource,QgsProcessingParameterVectorLayer,QgsProcessingParameterNumber,QgsProcessingException,QgsFeatureSink,QgsProcessingParameterFeatureSink)
import processing

#Parameters
##SSS_2019-nvi=name
##analyzeddistancem=number 800
##crs=crs EPSG:3395
##initialpoint=vector
##parcels=vector
##segmentos=vector
##streets=vector

##rede_viasnvi_m=output outputVector
##buffers=output outputVector
##joinednetwork=output outputVector
##summarize_land_data=output outputVector
##poligono_dados_agregados=output outputVector
##raio_de_analise=output outputVector
##snappedland=output outputVector


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

        # Analyze network reach 
        outputs = {}
        outputs['native:reprojectlayer_1']=processing.run('native:reprojectlayer', {'INPUT':street_network,'TARGET_CRS':parameters['crs']}, context=context, feedback=feedback)
        outputs['native:reprojectlayer_4']=processing.run('native:reprojectlayer', {'INPUT':initial_points,'TARGET_CRS':parameters['crs']}, context=context, feedback=feedback)
        outputs['native:reprojectlayer_3']=processing.run('native:reprojectlayer', {'INPUT':sample_input,'TARGET_CRS':parameters['crs']}, context=context, feedback=feedback)
        outputs['qgis:serviceareafromlayer_2']=processing.run('qgis:serviceareafromlayer', {
                'DEFAULT_DIRECTION':2,
                'DEFAULT_SPEED':5,
                'INCLUDE_BOUNDS':False,
                'INPUT':outputs['native:reprojectlayer_1']['OUTPUT'],
                'START_POINTS':outputs['native:reprojectlayer_4']['OUTPUT'],
                'STRATEGY':0,'TOLERANCE':0,'TRAVEL_COST':analysed_radius})
        outputs['native:reprojectlayer_2']=processing.run('native:reprojectlayer', {'INPUT':sample_input,'TARGET_CRS':parameters['crs']}, context=context, feedback=feedback)
        outputs['qgis:minimumboundinggeometry_1']=processing.run('qgis:minimumboundinggeometry', {'INPUT':outputs['qgis:serviceareafromlayer_2']['OUTPUT_LINES'],'TYPE':3}, context=context, feedback=feedback)
        outputs['native:extractbylocation_1']=processing.run('native:extractbylocation', {'INPUT':outputs['native:reprojectlayer_2']['OUTPUT'],'INTERSECT':outputs['qgis:minimumboundinggeometry_1']['OUTPUT'],'PREDICATE':0}, context=context, feedback=feedback)
        outputs['native:addautoincrementalfield_1']=processing.run('native:addautoincrementalfield', {'FIELD_NAME':"id_parcels-in",'INPUT':outputs['native:extractbylocation_1']['OUTPUT'],'SORT_ASCENDING':True,'SORT_NULLS_FIRST':False,'START':1}, context=context, feedback=feedback)
        outputs['native:centroids_1']=processing.run('native:centroids', {'ALL_PARTS':True,'INPUT':outputs['native:addautoincrementalfield_1']['OUTPUT']}, context=context, feedback=feedback)
        outputs['qgis:serviceareafromlayer_1']=processing.run('qgis:serviceareafromlayer', {
                'DEFAULT_DIRECTION':2,
                'DEFAULT_SPEED':5,
                'INCLUDE_BOUNDS':True,
                'INPUT':outputs['native:reprojectlayer_1']['OUTPUT'],
                'START_POINTS':outputs['native:centroids_1']['OUTPUT'],
                'STRATEGY':0,'TOLERANCE':5,'TRAVEL_COST':800}, context=context, feedback=feedback)
        outputs['qgis:fieldcalculator_2']=processing.run('qgis:fieldcalculator', {'FIELD_LENGTH':10,'FIELD_NAME':"buffer_length",'FIELD_PRECISION':2,'FIELD_TYPE':0,'FORMULA':"$length",'INPUT':outputs['qgis:serviceareafromlayer_1']['OUTPUT_LINES'],'NEW_FIELD':True}, context=context, feedback=feedback)
        outputs['qgis:minimumboundinggeometry_2']=processing.run('qgis:minimumboundinggeometry', {'INPUT':outputs['qgis:fieldcalculator_2']['OUTPUT'],'TYPE':3}, context=context, feedback=feedback)
        outputs['native:extractbylocation_2']=processing.run('native:extractbylocation', {'INPUT':outputs['native:reprojectlayer_3']['OUTPUT'],'INTERSECT':outputs['qgis:minimumboundinggeometry_2']['OUTPUT'],'PREDICATE':0}, context=context, feedback=feedback)
        outputs['native:centroids_3']=processing.run('native:centroids', {'ALL_PARTS':True,'INPUT':outputs['native:extractbylocation_2']['OUTPUT']}, context=context, feedback=feedback)
        outputs['native:extractbylocation_4']=processing.run('native:extractbylocation', {'INPUT':outputs['native:reprojectlayer_2']['OUTPUT'],'INTERSECT':outputs['qgis:minimumboundinggeometry_2']['OUTPUT'],'PREDICATE':0}, context=context, feedback=feedback)
        outputs['qgis:snapgeometries_1']=processing.run('qgis:snapgeometries', {'BEHAVIOR':3,'INPUT':outputs['native:centroids_3']['OUTPUT'],'REFERENCE_LAYER':outputs['native:reprojectlayer_1']['OUTPUT'],'TOLERANCE':100}, context=context, feedback=feedback)

        outputs['native:buffer_2']=processing.run('native:buffer', {'DISSOLVE':False,'DISTANCE':3,'END_CAP_STYLE':0,'INPUT':outputs['qgis:snapgeometries_1']['OUTPUT'],'JOIN_STYLE':0,'MITER_LIMIT':2,'SEGMENTS':3}, context=context, feedback=feedback)
        outputs['qgis:joinbylocationsummary_3']=processing.run('qgis:joinbylocationsummary', {'DISCARD_NONMATCHING':False,'INPUT':outputs['qgis:fieldcalculator_2']['OUTPUT'],'JOIN':outputs['native:buffer_2']['OUTPUT'],'JOIN_FIELDS':"a_resident;a_commerci;a_institut;a_entertai;a_industri;a_civic;a_nonresid",'PREDICATE':0,'SUMMARIES':5}, context=context, feedback=feedback)

        outputs['qgis:fieldcalculator_11']=processing.run('qgis:fieldcalculator', {'FIELD_LENGTH':10,'FIELD_NAME':"nain",'FIELD_PRECISION':3,'FIELD_TYPE':0,'FORMULA':'''("T1024_Node_Count"^1.2)/"T1024_Total_Depth"''','INPUT':outputs['native:extractbylocation_4']['OUTPUT'],'NEW_FIELD':True}, context=context, feedback=feedback)
        outputs['native:centroids_4']=processing.run('native:centroids', {'ALL_PARTS':True,'INPUT':outputs['qgis:fieldcalculator_11']['OUTPUT']}, context=context, feedback=feedback)
        outputs['native:buffer_3']=processing.run('native:buffer', {'DISSOLVE':False,'DISTANCE':10,'END_CAP_STYLE':0,'INPUT':outputs['native:centroids_4']['OUTPUT'],'JOIN_STYLE':0,'MITER_LIMIT':2,'SEGMENTS':5}, context=context, feedback=feedback)
        outputs['qgis:joinbylocationsummary_1']=processing.run('qgis:joinbylocationsummary', {'DISCARD_NONMATCHING':False,'INPUT':outputs['qgis:joinbylocationsummary_3']['OUTPUT'],'JOIN':outputs['native:buffer_3']['OUTPUT'],'JOIN_FIELDS':"nain;T1024_Node_Count_R800_metric",'PREDICATE':0,'SUMMARIES':6}, context=context, feedback=feedback)
        outputs['native:joinattributestable_1']=processing.run('native:joinattributestable', {'DISCARD_NONMATCHING':False,'FIELD':"id_parcels-in",'FIELD_2':"id_parcels-in",'INPUT':outputs['native:addautoincrementalfield_1']['OUTPUT'],'INPUT_2':outputs['qgis:joinbylocationsummary_1']['OUTPUT'],'METHOD':1}, context=context, feedback=feedback)
        outputs['qgis:fieldcalculator_1']=processing.run('qgis:fieldcalculator', {'FIELD_LENGTH':10,'FIELD_NAME':"residential_density",'FIELD_PRECISION':4,'FIELD_TYPE':0,
               'FORMULA':'''"a_resident_sum"/("a_nonresid_sum"+"a_resident_sum")''','INPUT':outputs['native:joinattributestable_1']['OUTPUT'],'NEW_FIELD':True}, context=context, feedback=feedback)
        outputs['qgis:fieldcalculator_7']=processing.run('qgis:fieldcalculator', {'FIELD_LENGTH':10,'FIELD_NAME':"nres_nind-density",'FIELD_PRECISION':4,'FIELD_TYPE':0,
               'FORMULA':'''("a_commerci_sum"+"a_civic_sum"+"a_entertai_sum")/("a_nonresid_sum"+"a_resident_sum")''','INPUT':outputs['qgis:fieldcalculator_1']['OUTPUT'],'NEW_FIELD':True}, context=context, feedback=feedback)
        outputs['qgis:fieldcalculator_23']=processing.run('qgis:fieldcalculator', {'FIELD_LENGTH':10,'FIELD_NAME':"use_diversity_simpson",'FIELD_PRECISION':4,'FIELD_TYPE':0,
               'FORMULA':'''(("a_resident_sum"*( "a_resident_sum" -1)) + ("a_commerci_sum"*( "a_commerci_sum" -1)) + ("a_civic_sum"*( "a_civic_sum" -1)) + ("a_institut_sum"*( "a_institut_sum" -1)) + ("a_entertai_sum"*( "a_entertai_sum" -1)))/ ((("a_resident_sum")*("a_nonresid_sum"))-1)''',
               'INPUT':outputs['qgis:fieldcalculator_7']['OUTPUT'],'NEW_FIELD':True}, context=context, feedback=feedback)
        outputs['qgis:fieldcalculator_13']=processing.run('qgis:fieldcalculator', {'FIELD_LENGTH':10,'FIELD_NAME':"z_nain",'FIELD_PRECISION':3,'FIELD_TYPE':0,
               'FORMULA':'''(("nain_mean")-mean("nain_mean"))/stdev("nain_mean")''','INPUT':outputs['qgis:fieldcalculator_23']['OUTPUT'],'NEW_FIELD':True}, context=context, feedback=feedback)
        outputs['qgis:fieldcalculator_14']=processing.run('qgis:fieldcalculator', {'FIELD_LENGTH':10,'FIELD_NAME':"z_node_count_r800",'FIELD_PRECISION':3,'FIELD_TYPE':0,
               'FORMULA':'''(("T1024_Node_Count_R800_metric_mean")-mean("T1024_Node_Count_R800_metric_mean"))/stdev("T1024_Node_Count_R800_metric_mean")''','INPUT':outputs['qgis:fieldcalculator_13']['OUTPUT'],'NEW_FIELD':True}, context=context, feedback=feedback)
        outputs['qgis:fieldcalculator_15']=processing.run('qgis:fieldcalculator', {'FIELD_LENGTH':10,'FIELD_NAME':"z_residential_density",'FIELD_PRECISION':3,'FIELD_TYPE':0,
               'FORMULA':'''(("residential_density"-mean("residential_density"))/stdev("residential_density"))''','INPUT':outputs['qgis:fieldcalculator_14']['OUTPUT'],'NEW_FIELD':True}, context=context, feedback=feedback)
        outputs['qgis:fieldcalculator_16']=processing.run('qgis:fieldcalculator', {'FIELD_LENGTH':10,'FIELD_NAME':"z_nres_nind-density",'FIELD_PRECISION':3,'FIELD_TYPE':0,
               'FORMULA':'''(("nres_nind-density"-mean("nres_nind-density"))/stdev("nres_nind-density"))''','INPUT':outputs['qgis:fieldcalculator_15']['OUTPUT'],'NEW_FIELD':True}, context=context, feedback=feedback)
        outputs['qgis:fieldcalculator_24']=processing.run('qgis:fieldcalculator', {'FIELD_LENGTH':10,'FIELD_NAME':"z_use_diversity_simpson",'FIELD_PRECISION':4,'FIELD_TYPE':0,
               'FORMULA':'''(("use_diversity_simpson"-mean("use_diversity_simpson"))/stdev("use_diversity_simpson"))''',
               'INPUT':outputs['qgis:fieldcalculator_16']['OUTPUT'],'NEW_FIELD':True}, context=context, feedback=feedback)
        outputs['qgis:fieldcalculator_10']=processing.run('qgis:fieldcalculator', {'FIELD_LENGTH':10,'FIELD_NAME':"acessibilidade",'FIELD_PRECISION':4,'FIELD_TYPE':0,
               'FORMULA':("z_nain"+"z_node_count_r800")/2,'INPUT':outputs['qgis:fieldcalculator_24']['OUTPUT'],'NEW_FIELD':True}, context=context, feedback=feedback)
        outputs['qgis:fieldcalculator_18']=processing.run('qgis:fieldcalculator', {'FIELD_LENGTH':10,'FIELD_NAME':"densidade",'FIELD_PRECISION':3,'FIELD_TYPE':0,
               'FORMULA':'''("z_residential_density"+"z_nres_nind-density")/2''','INPUT':outputs['qgis:fieldcalculator_10']['OUTPUT'],'NEW_FIELD':True}, context=context, feedback=feedback)
        outputs['qgis:fieldcalculator_19']=processing.run('qgis:fieldcalculator', {'FIELD_LENGTH':10,'FIELD_NAME':"nvi",'FIELD_PRECISION':3,'FIELD_TYPE':0,
               'FORMULA':'''"acessibilidade"+"densidade"+"z_use_diversity_simpson"''','INPUT':outputs['qgis:fieldcalculator_18']['OUTPUT'],'NEW_FIELD':True}, context=context, feedback=feedback)
        
        source = outputs['qgis:fieldcalculator_19']['OUTPUT']
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