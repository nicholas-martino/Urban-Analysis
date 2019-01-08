# -*- coding: utf-8 -*-
"""
Created on Tue Jan  8 13:52:23 2019

@author: nicholas-martino

This is an automatic export from QGIS processing model tool for referencing purpuses only, 
it is not executable using python console in QGIS
"""

#Parameters
Centerlines to Segments=name
centerlines=optional vector
crs=crs EPSG:31985
intersectionbuffer=number 5
linesimplificationdouglaspecker=number 7
intersections=output outputVector
segments=output outputVector

#Processing tools
results={}
outputs['native:fixgeometries_1']=processing.run('native:fixgeometries', {'INPUT':parameters['centerlines']}, context=context, feedback=feedback)
outputs['native:extractbyexpression_1']=processing.run('native:extractbyexpression', {'EXPRESSION':$geometry IS NOT NULL,'INPUT':outputs['native:fixgeometries_1']['OUTPUT']}, context=context, feedback=feedback)
outputs['native:reprojectlayer_1']=processing.run('native:reprojectlayer', {'INPUT':outputs['native:extractbyexpression_1']['OUTPUT'],'TARGET_CRS':EPSG:4326}, context=context, feedback=feedback)
outputs['native:splitwithlines_1']=processing.run('native:splitwithlines', {'INPUT':outputs['native:reprojectlayer_1']['OUTPUT'],'LINES':outputs['native:reprojectlayer_1']['OUTPUT']}, context=context, feedback=feedback)
outputs['native:reprojectlayer_2']=processing.run('native:reprojectlayer', {'INPUT':outputs['native:splitwithlines_1']['OUTPUT'],'TARGET_CRS':parameters['crs']}, context=context, feedback=feedback)
outputs['native:simplifygeometries_1']=processing.run('native:simplifygeometries', {'INPUT':outputs['native:reprojectlayer_2']['OUTPUT'],'METHOD':0,'TOLERANCE':parameters['linesimplificationdouglaspecker']}, context=context, feedback=feedback)
outputs['native:reprojectlayer_3']=processing.run('native:reprojectlayer', {'INPUT':outputs['native:simplifygeometries_1']['OUTPUT'],'TARGET_CRS':EPSG:4326}, context=context, feedback=feedback)
outputs['native:explodelines_1']=processing.run('native:explodelines', {'INPUT':outputs['native:reprojectlayer_3']['OUTPUT']}, context=context, feedback=feedback)
outputs['native:extractvertices_1']=processing.run('native:extractvertices', {'INPUT':outputs['native:explodelines_1']['OUTPUT']}, context=context, feedback=feedback)
outputs['native:reprojectlayer_5']=processing.run('native:reprojectlayer', {'INPUT':outputs['native:extractvertices_1']['OUTPUT'],'TARGET_CRS':parameters['crs']}, context=context, feedback=feedback)
outputs['native:removeduplicatevertices_1']=processing.run('native:removeduplicatevertices', {'INPUT':outputs['native:reprojectlayer_5']['OUTPUT'],'TOLERANCE':1e-06,'USE_Z_VALUE':false}, context=context, feedback=feedback)
outputs['native:buffer_1']=processing.run('native:buffer', {'DISSOLVE':true,'DISTANCE':parameters['intersectionbuffer'],'END_CAP_STYLE':0,'INPUT':outputs['native:removeduplicatevertices_1']['OUTPUT'],'JOIN_STYLE':0,'MITER_LIMIT':2,'SEGMENTS':5}, context=context, feedback=feedback)
outputs['native:multiparttosingleparts_1']=processing.run('native:multiparttosingleparts', {'INPUT':outputs['native:buffer_1']['OUTPUT']}, context=context, feedback=feedback)
outputs['native:centroids_1']=processing.run('native:centroids', {'ALL_PARTS':false,'INPUT':outputs['native:multiparttosingleparts_1']['OUTPUT']}, context=context, feedback=feedback)
results['intersections']=outputs['native:centroids_1']['OUTPUT']
outputs['native:buffer_3']=processing.run('native:buffer', {'DISSOLVE':false,'DISTANCE':1,'END_CAP_STYLE':0,'INPUT':outputs['native:centroids_1']['OUTPUT'],'JOIN_STYLE':0,'MITER_LIMIT':2,'SEGMENTS':5}, context=context, feedback=feedback)
outputs['native:buffer_2']=processing.run('native:buffer', {'DISSOLVE':false,'DISTANCE':-0.5,'END_CAP_STYLE':0,'INPUT':outputs['native:buffer_3']['OUTPUT'],'JOIN_STYLE':0,'MITER_LIMIT':2,'SEGMENTS':5}, context=context, feedback=feedback)
outputs['qgis:polygonstolines_1']=processing.run('qgis:polygonstolines', {'INPUT':outputs['native:buffer_3']['OUTPUT']}, context=context, feedback=feedback)
outputs['native:reprojectlayer_6']=processing.run('native:reprojectlayer', {'INPUT':outputs['native:buffer_2']['OUTPUT'],'TARGET_CRS':EPSG:4326}, context=context, feedback=feedback)
outputs['native:reprojectlayer_4']=processing.run('native:reprojectlayer', {'INPUT':outputs['qgis:polygonstolines_1']['OUTPUT'],'TARGET_CRS':EPSG:4326}, context=context, feedback=feedback)
outputs['native:splitwithlines_2']=processing.run('native:splitwithlines', {'INPUT':outputs['native:explodelines_1']['OUTPUT'],'LINES':outputs['native:reprojectlayer_4']['OUTPUT']}, context=context, feedback=feedback)
outputs['native:extractbylocation_1']=processing.run('native:extractbylocation', {'INPUT':outputs['native:splitwithlines_2']['OUTPUT'],'INTERSECT':outputs['native:reprojectlayer_6']['OUTPUT'],'PREDICATE':2}, context=context, feedback=feedback)
outputs['native:reprojectlayer_7']=processing.run('native:reprojectlayer', {'INPUT':outputs['native:extractbylocation_1']['OUTPUT'],'TARGET_CRS':parameters['crs']}, context=context, feedback=feedback)
outputs['qgis:snapgeometries_1']=processing.run('qgis:snapgeometries', {'BEHAVIOR':3,'INPUT':outputs['native:reprojectlayer_7']['OUTPUT'],'REFERENCE_LAYER':outputs['native:centroids_1']['OUTPUT'],'TOLERANCE':1000}, context=context, feedback=feedback)
outputs['native:fixgeometries_2']=processing.run('native:fixgeometries', {'INPUT':outputs['qgis:snapgeometries_1']['OUTPUT']}, context=context, feedback=feedback)
outputs['qgis:extendlines_1']=processing.run('qgis:extendlines', {'END_DISTANCE':0.5,'INPUT':outputs['native:fixgeometries_2']['OUTPUT'],'START_DISTANCE':0.5}, context=context, feedback=feedback)
results['segments']=outputs['qgis:extendlines_1']['OUTPUT']
return results