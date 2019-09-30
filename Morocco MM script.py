# The goal of this script is to create an accessibility index.
# The inputs include point feature classes for villages, health centers, and schools
# There is also a network dataset that contains the previously mentioned feature class as well as the road network
# This tool will create 4 indicators of spatial accessibility from villages to services (i.e. health centers and schools)
# These are 1. total network length (schools and health)  2. Euclidean distance to nearest school
# 3. Euclidean distance to nearest health center  4. Euclidean distance between village and main road
# There are reasons that these indicators were chosen but that isn't important right now
# Using the values calculated from these 4 indicators, the tool will create a composite index representing each village's accessibility
# However, the composite field is made up of 'meaningless' numbers so I then relassified the index into 4 categories of
# no, low, average and high accessibility.
# Creating these classes for each village is the primary deliverable of this tool
# The tool also creates a map at the end but the mapping module is terrible so the map should not be used very seriously

# to run on different computer, output_dir must be changed to where the data is on line 291
# to run with different data, change data at bottom (starting on line 299) and
# change commune variable on line 252



# functions

# this function takes a network dataset, creates closest facility routes and exports those routes as feature classes
# the output gives me the network lengths from villages to services aka indicator #1
def export_routes(network, facility_layer, final_path, field1):
   
    try:
        # set environment settings
        arcpy.CheckOutExtension("Network")
    
        # local variables
        layer_name = "ClosestFacility1"
        impedance = "Length"
        facilities = os.path.join(arcpy.env.workspace, "Network_Items", facility_layer)
        incidents = os.path.join(arcpy.env.workspace, "Network_Items", "NearAitOuassif")
        output_layer_file = os.path.join(output_dir, layer_name + ".lyr")
    
        # this is the tool that creates the route layer
        # it is using road length to make its decisions and allows for u-turns
        result_object = arcpy.na.MakeClosestFacilityLayer(network, layer_name, 
                                                          impedance, "TRAVEL_TO",
                                                          "", 1, "",
                                                          "ALLOW_UTURNS")
    
        # Get the layer object from the result object. The closest facility layer can
        # now be referenced using the layer object.
        layer_object = result_object.getOutput(0)
    
        # Get the names of all the sublayers within the closest facility layer.
        sublayer_names = arcpy.na.GetNAClassNames(layer_object)
        # Stores the layer names that we will use later
        facilities_layer_name = sublayer_names["Facilities"]
        incidents_layer_name = sublayer_names["Incidents"]
    
        # Load the villages as Facilities using the default field mappings and
        # search tolerance
        field_mappings = arcpy.na.NAClassFieldMappings(layer_object,
                                                        facilities_layer_name)
        field_mappings["Name"].mappedFieldName = field1
        
        arcpy.na.AddLocations(layer_object, facilities_layer_name,
                                facilities, field_mappings, "")
    
        # Load the schools as Incidents. Map the Name property from the NOM field
        #using field mappings
        field_mappings2 = arcpy.na.NAClassFieldMappings(layer_object,
                                                        incidents_layer_name)
        field_mappings2["Name"].mappedFieldName = "DOUAR"
        arcpy.na.AddLocations(layer_object, incidents_layer_name, incidents,
                              field_mappings2, "")
    
        # Solve the closest facility layer
        arcpy.na.Solve(layer_object)
    
        # Save the solved closest facility layer as a layer file on disk
        layer_object.saveACopy(output_layer_file)
        
        # Create variable containing list of sublayers
        sublayers = arcpy.mapping.ListLayers(layer_object)
        
        # Copy the Routes sublayer into a new feature class
        arcpy.management.CopyFeatures(sublayers[4], final_path)
    
        print "export_routes completed successfully"
        
            
    except Exception as e:
        # If an error occurred, print line number and error message
        import sys
        tb = sys.exc_info()[2]
        print("An error occured on line %i" % tb.tb_lineno)
        print(str(e))


# this function joins two specified tables using OBJECTID as the join field
# this is used to get the lengths for my schools routes and health routes into one feature class along with the village data
# it is used later in the script to combine the point distance indicators into one feature class
# and also to join the accessibility classes I create in pandas with the villages
def table_join(inFeatures, joinTable, outFeature):
    try:       
        # local variables    
        layerName = "village_layer"
        joinField = "OBJECTID"
        
        arcpy.MakeFeatureLayer_management(inFeatures, layerName)
        arcpy.AddJoin_management(layerName, joinField, joinTable, joinField)
        arcpy.CopyFeatures_management(layerName, outFeature)
        
        print "table_join completed successfully."
        
    except Exception as err:
        print(err.args[0])
 
        
# this tool simply measures Euclidean distance between the villages and the specified featuer class
# it is used twice (for schools and health centers)
# this provides the values for indicators #2 and #3
def point_distance(near_features, output_file):
       
     arcpy.Near_analysis("Villages2", near_features)
     arcpy.CopyFeatures_management("Villages2", output_file)
         
     print "point_distance completed sucessfully."
         
     
# due to all the table joins done, the excessive amount of fields was annoying
# this function cleans up the data by deleting unnecessary fields
def delete_field(inFeatures):
    
    # set local variables
    outFeatures = "Villages_Drop"
    dropFields = ["Villages3_Villages1_AitOuassifDuars_Lon", "Villages3_Villages1_AitOuassifDuars_Lat", "Villages3_Villages1_AitOuassifDuars_NEAR_FID", "Villages_Drop_Villages3_Villages1_AitOuassifDuars_NEAR_DIST",
                  "Villages3_Villages1_AitOuassifDuars_NEAR_X", "Villages3_Villages1_AitOuassifDuars_NEAR_Y", "Villages_Drop_Villages3_Villages1_AitOuassifDuars_Z"
                  "Villages3_Villages1_AitOuassifDuars_NEAR_DIST", "Villages3_Villages1_SchoolRoutes_OBJECTID", "Villages3_Villages1_SchoolRoutes_FacilityRank", 
                  "Villages3_Villages1_SchoolRoutes_IncidentCurbApproach", "Villages3_Villages1_SchoolRoutes_FacilityCurbApproach", "Villages3_Villages1_SchoolRoutes_IncidentID",
                  "Villages3_HealthRoutes_OBJECTID", "Villages3_HealthRoutes_FacilityRank", "Villages3_HealthRoutes_IncidentCurbApproach",
                  "Villages3_HealthRoutes_FacilityCurbApproach", "Villages3_HealthRoutes_IncidentID",
                  "Villages4_OBJECTID", "Villages4_Villages1_AitOuassifDuars_DOUAR", "Villages4_Villages1_AitOuassifDuars_Lon"
                  "Villages4_Villages1_AitOuassifDuars_Lat", "Villages4_Villages1_AitOuassifDuars_NEAR_FID", "Villages4_Villages1_AitOuassifDuars_NEAR_DIST",
                  "Villages4_Villages1_AitOuassifDuars_NEAR_X", "Villages4_Villages1_AitOuassifDuars_NEAR_Y", "Villages4_Villages1_AitOuassifDuars_Z",
                  "Villages4_Villages1_SchoolRoutes_OBJECTID", "Villages4_Villages1_SchoolRoutes_FacilityID", "Villages4_Villages1_SchoolRoutes_FacilityRank",
                  "Villages4_Villages1_SchoolRoutes_Name", "Villages4_Villages1_SchoolRoutes_IncidentCurbApproach", "Villages4_Villages1_SchoolRoutes_FacilityCurbApproach",
                  "Villages4_Villages1_SchoolRoutes_IncidentID", "Villages4_Villages1_SchoolRoutes_Total_Length", "Villages4_HealthRoutes_OBJECTID",
                  "Villages4_HealthRoutes_FacilityID", "Villages4_HealthRoutes_FacilityRank", "Villages4_HealthRoutes_Name",
                  "Villages4_HealthRoutes_IncidentCurbApproach", "Villages4_HealthRoutes_FacilityCurbApproach", "Villages4_HealthRoutes_IncidentID",
                  "Villages4_HealthRoutes_Total_Length", "NEAR_FID", "Villages_Drop_Villages4_Villages1_AitOuassifDuars_Lon", "Villages_Drop_Villages4_Villages1_AitOuassifDuars_Lat"]
    
    arcpy.CopyFeatures_management(inFeatures, outFeatures)
    arcpy.DeleteField_management(outFeatures, dropFields)
    
    print "delete_field completed successfully"
    

# this function calculates the Euclidean distance between villages and the nearest road feature
# these values are used for indicator #4
def road_distance(inFeatures):
    
    arcpy.Near_analysis(inFeatures, "Network_Items\Roads3")
    arcpy.CopyFeatures_management(inFeatures, "Villages6")
    
    print "road_distance completed successfully"
    

# this function creates the composite index field 
def calculations(in_table):
    
    # local variables
    fieldName = "NetworkDist"
    fieldName2 = "Composite"
    # unlike the other 3 indicators, there is some math involved to get the values for indicator #1
    sql = "((([NEAR_DIST] * 2) + [Villages3_Villages1_SchoolRoutes_Total_Length] + [Villages3_HealthRoutes_Total_Length])/2)"
    # now that we have all 4 indicator values, they are simply added and divided by 4
    # this is just the formula that was decided for this model
    sql2 = "(([NetworkDist] + [Villages3_NEAR_DIST] + [Villages4_NEAR_DIST] + [NEAR_DIST])/4)"
    
    arcpy.AddField_management(in_table, fieldName, "DOUBLE")
    arcpy.CalculateField_management(in_table, fieldName, sql)
    
    arcpy.AddField_management(in_table, fieldName2, "DOUBLE")
    arcpy.CalculateField_management(in_table, fieldName2, sql2)
    
    print "calculations completed successfully"

    
# due to all the table joins done, the excessive amount of fields was annoying
# this function cleans up the data by deleting unnecessary fields     
def delete_field2(inFeatures):
    
    # local variables
    outFeatures = "Villages_Drop2"
    dropFields = ["NearAitOuassif_OBJECTID", "NearAitOuassif_DOUAR", "NearAitOuassif_Lon", "NearAitOuassif_Lat",
                  "NearAitOuassif_NEAR_FID", "NearAitOuassif_NEAR_X", "NearAitOuassif_NEAR_Y", "NEAR_FID", "NEAR_DIST"
                  "Villages_Drop_Villages3_Villages1_AitOuassifDuars_NEAR_DIST", "Villages3_Villages1_AitOuassifDuars_Z",
                  "Villages_Drop_Villages4_Villages1_AitOuassifDuars_Lon", "Villages_Drop_Villages4_Villages1_AitOuassifDuars_Lat"
                  "Villages3_Villages1_AitOuassifDuars_NEAR_DIST", "Villages4_Villages1_AitOuassifDuars_Lon", "Villages4_Villages1_AitOuassifDuars_Lat"]
    
    arcpy.CopyFeatures_management(inFeatures, outFeatures)
    arcpy.DeleteField_management(outFeatures, dropFields)
    
    print "delete_field2 completed successfully"

       
# now the composite field needs to be reclassed into more digestable accessibility categories
# i decided to do this reclassing in pandas so first the dbf needs to be converted into a csv
# the standard table_to_table tool did not work so i found the following code below to do this task in a more roundabout matter       
def dbf2csv(fc, CSVfile):
    
    from os import path as p
    
    fields = [f.name for f in arcpy.ListFields(fc) if f.type <> 'Geometry']
    with open(CSVfile, 'w') as f:
        f.write(','.join(fields)+'\n') #csv headers
        with arcpy.da.SearchCursor(fc, fields) as cursor:
            for row in cursor:
                f.write(','.join([str(r) for r in row])+'\n')
    print 'Created %s Successfully' %p.basename(CSVfile)

    
# this function creates the new accessibility categories within pandas
# the data is broken using percentiles (25, 50 75) which was retrieved from the describe method  
def reclass(input_csv, output_csv):

    # reads csv and stores it as pandas dataframe
    df = read_csv(input_csv)
    # this gets me the percentiles i am interested in
    df2 = df.describe()
    # i converted the dataframe to a series so i can more easily access the values i need
    series = df2["Composite"]
    # here i store the values for each percentile break
    twentyfive = series[4]
    fifty = series[5]
    seventyfive = series[6]

    # here i create a new column and the code essentially works like an if statement off of the Composite field
    df["Class"] = twentyfive
    df["Class"][df["Composite"] < twentyfive] = "high accessibility"
    df["Class"][df["Composite"] > twentyfive] = "average accessibility"
    df["Class"][df["Composite"] > fifty] = "low accessibility"
    df["Class"][df["Composite"] > seventyfive] = "no accessibility"
    
    df.to_csv(output_csv)
    
    print "reclass completed successfully"


# due to all the table joins done, the excessive amount of fields was annoying
# this function cleans up the data by deleting unnecessary fields
def delete_field3(inFeatures):
    
    # this is the final feature class created in this tool and therefore
    # i wanted the commune name included and 
    # the commune variable should be changed when running different datasets
    commune = "AitOuassif"
    outFeatures = os.path.join("FINAL" + commune)
    dropFields = ["new_csv5_csv_Field1", "new_csv5_csv_OBJECTID", "new_csv5_csv_Villages3_Villages1_AitOuassifDuars_DOUAR",
                  "new_csv5_csv_Villages3_Villages1_AitOuassifDuars_NEAR_DIST", "new_csv5_csv_Villages3_Villages1_SchoolRoutes_FacilityID",
                  "new_csv5_csv_Villages3_Villages1_SchoolRoutes_Name", "new_csv5_csv_Villages3_Villages1_SchoolRoutes_Total_Length",
                  "new_csv5_csv_Villages3_HealthRoutes_FacilityID", "new_csv5_csv_Villages3_HealthRoutes_Name",
                  "new_csv5_csv_Villages3_HealthRoutes_Total_Length", "new_csv5_csv_Villages3_NEAR_FID",
                  "new_csv5_csv_Villages4_NEAR_DIST", "new_csv5_csv_NEAR_FID", "new_csv5_csv_NEAR_DIST",
                  "new_csv5_csv_NetworkDist", "new_csv5_csv_Composite"]
    
    arcpy.CopyFeatures_management(inFeatures, outFeatures)
    arcpy.DeleteField_management(outFeatures, dropFields)
    
    print "delete_field2 completed successfully"
 

# this function exports a map as a pdf
# warning: this will not work using other datasets
def export_pdf(mxd_file):
    
    # saving the specified mxd file as a variable
    mxd = arcpy.mapping.MapDocument(mxd_file)
    
    # using the mapping module to export to pdf
    # warning: this map will be very ugly
    arcpy.mapping.ExportToPDF(mxd, "Project1.pdf")
    
    del mxd
    
    print "export_pdf completed successfully"
    
    
# settings for stuff outside of functions
# import modules
import os    
import arcpy  
from pandas import read_csv
        
# environment settings
output_dir = r"E:\Programming"
arcpy.env.workspace = os.path.join(output_dir, "Tinghir.mdb")
arcpy.env.overwriteOutput = True

    
# these are the parameters for this particular dataset
# the village name here is AitOuassif
# replace village names when working with different datasets
export_routes("Network_Items\AitOuassif_ND", "NearSchools", "SchoolRoutes", "NOM_ecole")
export_routes("Network_Items\AitOuassif_ND", "NearHealth", "HealthRoutes", "NOM_ETABL")
table_join("Network_Items\AitOuassifDuars", "SchoolRoutes", "Villages1")
table_join("Villages1", "HealthRoutes", "Villages2")
point_distance("Schools_AitOuassif", "Villages3")
point_distance("Health_AitOuassif", "Villages4")
table_join("Villages3", "Villages4", "Villages5")
delete_field("Villages5")
delete_field2("Villages_Drop")
road_distance("Villages_Drop2")
calculations("Villages6")
dbf2csv("Villages6", "new_csv3.csv")
reclass("new_csv3.csv", "new_csv5.csv")
table_join("Villages6", "new_csv5.csv", "Villages7")
delete_field3("Villages7")
export_pdf("Programming1.mxd")