import pandas as pd
import sqlite3
from catalogues_api_function import calling_catalogues

################################
# Catalogues Into SQL Database
################################
'''
catalogues_into_database: this function will call the efsa's catalogues api through the 'calling_catalogues' function and 
                          will store it ate the 'Catalogues' database.

                          args: 
                                * catalogues_api_key = efsa's catalogues api key. You can get one by this link: https://openapi-portal.efsa.europa.eu/docs/services/catalogues/operations/5aaf7886fcd3c00eccc677da
                                * catalogue_code = code of the catalogue the user wants to get

                          return:
                                * storing the catalogue as a table into the Ctalogues databse
'''
def catalogues_into_dabase(catalogues_api_key, catalogue_code):

    # Connecting to the Catalogues sql database
    conn = sqlite3.connect('CATALOGUES.db')

    # Create a cursor object to insert record, cretate a table, retrieve
    cursor = conn.cursor()

    # Getting the catalogue by calling the function
    catalogue = calling_catalogues(catalogues_api_key, catalogue_code)

    # Storing the catalogue into the Catalogues database
    catalogue.to_sql(f'{catalogue_code}', conn, if_exists='replace', index=False)

    # Commit and close the connection
    conn.commit()
    conn.close()


###############################################################
# Storing the User Data Uploaded into the APP as a SQL Database
###############################################################
'''
user_data_into_database: this function will store, as a sql databse, the data to be enriched which was uploaded into the app.

                          args: 
                                * data_to_be_enriched = csv file with the data to be enriched

                          return:
                                * storing the data to be enriched, uploaded by the user, into a sql database
'''
def user_data_into_database(data_to_be_enriched):
    
    # Reading the data to be enriched
    df = pd.read_excel(data_to_be_enriched)

    # Connecting to the Catalogues sql database
    conn = sqlite3.connect('UsersData.db')

    # Create a cursor object to insert record, cretate a table, retrieve
    cursor = conn.cursor()

    # Storing the catalogue into the Catalogues database
    df.to_sql('DATA_TO_BE_ENRICHED', conn, if_exists='replace')

    # Commit and close the connection
    conn.commit()
    conn.close()