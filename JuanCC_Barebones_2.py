# The purpose of this script is to create an accessibility index that shows how long it takes to get to a nearest facility. In this case
# this script is doing this to find the amount of time it takes to get to a hospital in the Ait Ouassif commune. This script will analyze a
# network dataset of roads, as well as point files of villages and a hospital. The output should be a new shapefile, with speeds as a new column
# in the attribute table.
#

import arcpy
from arcpy import env
import os


try:
    
    #This script requires network analyst to run. This will check if it is available and activate it. If not, an error message will pop up.
    if arcpy.CheckExtension("network") == "Available":
        arcpy.CheckOutExtension("network")
    else:
        raise arcpy.ExecuteError("Network Analyst Extension license is not available.")
    
    #Set environment settings. This includes output directory, workspace, overwrite capablities (to re-run tool over previous results)
    output_dir = r'H:\Morocco_Accessibility\AitOuassif\Ait_Ouassif.gdb\Results'
    
    arcpy.env.workspace = r'H:\Morocco_Accessibility\AitOuassif\Ait_Ouassif.gdb'
    
    arcpy.env.overwriteOutput = True
    
    input_gdb = r'H:\Morocco_Accessibility\AitOuassif\Ait_Ouassif.gdb'
    
    #Refers to the road network itself, which needed to be created independently. The network contains road speeds based on their
    # classification (primary, secondary, etc.), a hierarchy which prioritizes some roads over others, and the assumption that the roads
    # are traverssed with a normal car. 
    # This process can be automated, but seems like more troule than it's worth.
    inNetworkDataset = r"H:\Morocco_Accessibility\AitOuassif\Ait_Ouassif.gdb\Roads\AitOuassif_ND"
    
    #What the output will be named
    outNALayerName = "Closest_Hospital"
    
    #The name of the travel mode to use in the analysis. Will result in the amount of time it takes to travel from
    #a village to its nearest hospital. A function of network analysis.
    impedance_Attribute = "Traveltime"
    
    #A list of cost attributes to be accumulated during analysis. Accumulates the specified attribute.
    accumulateAttributeName = ["Meters"]
    
    #Refers to hospitals in this case. Navigates into geodatabase "Facilities" feature data set and locks onto Health_Center_AitOuassif 
    inFacilities = os.path.join(input_gdb, "Facilities", "Health_Center_AitOuassif")
    
    #Refers to hospitals in this case. Navigates into geodatabase "Facilities" feature data set and locks onto AitOuassif_Village
    inIncidents = os.path.join(input_gdb, "Facilities", "AitOuassif_Village")
    
    #Output will be named "Closest_Hospital.lyr" and be placed into the output_dir, which in this case is within the geodatabase.
    outLayerFile = os.path.join(input_gdb, outNALayerName )
    
    # This is the important part. This is the actual function that determines the shortest distance between two points, in this case
    # facilities (Health_Center) and incidents (Villages) based on a specific travel mode ("Travel Time").
    NAResultObject = arcpy.na.MakeClosestFacilityLayer(inNetworkDataset,outNALayerName,
                                                   impedance_Attribute,"TRAVEL_TO",
                                                   "",1,"")
    
    #Get the layer object from the result object. The closest facility layer can
    #now be referenced using the layer object.
    outNALayer = NAResultObject.getOutput(0)
    
    #Get the names of all the sublayers within the closest facility layer.
    subLayerNames = arcpy.na.GetNAClassNames(outNALayer)
    #Stores the layer names that we will use later
    facilitiesLayerName = subLayerNames["Facilities"]
    incidentsLayerName = subLayerNames["Incidents"]
    
    #Load the hospital as Facilities using the default field mappings and search tolerance.
    arcpy.na.AddLocations(outNALayer, facilitiesLayerName, inFacilities, "", "")
    
    #Load the villages as Incidents. Map the Name property from the NOM field
    #using field mappings. #NOM_ETABL is a specific field within the hospital shapefile which contains the name of the hospital.
    #This process tells the script to select values within the NOM field.
    fieldMappings = arcpy.na.NAClassFieldMappings(outNALayer, facilitiesLayerName)
    fieldMappings["Name"].mappedFieldName = "NOM_ETABL"
    arcpy.na.AddLocations(outNALayer, incidentsLayerName, inIncidents,
                          fieldMappings,"")
    
    #Load the villages as Facilities using the default field mappings and search tolerance.!!!
    arcpy.na.AddLocations(outNALayer, incidentsLayerName, inFacilities, "", "")
    
    #Load the villages as Incidents. Map the Name property from the DOUAR field
    #using field mappings. #DOUAR is a specific field within the village shapefile which contains the names of the villages.
    #This process tells the script to select values within the NOM field.
    fieldMappings2 = arcpy.na.NAClassFieldMappings(outNALayer, incidentsLayerName)
    fieldMappings2["Name"].mappedFieldName = "DOUAR"
    arcpy.na.AddLocations(outNALayer, incidentsLayerName, inIncidents,
                          fieldMappings2,"")
    
    #Solve the closest facility layer
    arcpy.na.Solve(outNALayer)
    
    # Save the solved closest facility layer as a layer file on disk
    #outNALayer.saveACopy(outLayerFile)
    
    # Create variable containing list of sublayers
    #sublayers = arcpy.mapping.ListLayers(outNALayer)
    
    #arcpy.management.CopyFeatures(sublayers[4], "health_path")
    
    #Save the solved closest facility layer as a layer file on disk with
    #relative paths
    arcpy.management.SaveToLayerFile(outNALayer,outLayerFile,"RELATIVE")
    
    print "Script completed successfully"
    
except Exception as e:
    # If an error occurred, print line number and error message
    import traceback, sys
    tb = sys.exc_info()[2]
    print "An error occurred on line %i" % tb.tb_lineno
    print str(e)