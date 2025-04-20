# app/utils/country_mapping.py

"""
Utility module for mapping between database country names and GeoJSON country names.
This handles translation between different naming conventions used in different data sources.
"""

# Dictionary mapping from database country names to GeoJSON country names
DB_TO_GEOJSON = {
    "US": "United States of America",
    "USA": "United States of America",
    "England": "United Kingdom",
    "UK": "United Kingdom",
    "Serbia": "Republic of Serbia",
    # Add more if needed
    # "Country Name in DB": "Country Name in GeoJSON"
}

# Reverse mapping from GeoJSON to database (auto-genererad)
GEOJSON_TO_DB = {v: k for k, v in DB_TO_GEOJSON.items()}


def get_geojson_country_name(db_country_name: str) -> str:
    """
    Convert a database country name to its GeoJSON equivalent.

    Args:
        db_country_name: Country name as stored in the database

    Returns:
        The GeoJSON-compatible country name or the original if no mapping exists
    """
    return DB_TO_GEOJSON.get(db_country_name, db_country_name)


def get_db_country_name(geojson_country_name: str) -> str:
    """
    Convert a GeoJSON country name to its database equivalent.

    Args:
        geojson_country_name: Country name as used in GeoJSON files

    Returns:
        The database-compatible country name or the original if no mapping exists
    """
    return GEOJSON_TO_DB.get(geojson_country_name, geojson_country_name)
