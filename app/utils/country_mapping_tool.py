import json
import os
import sys
from typing import Dict, Set, Tuple
import difflib  # For more sophisticated string matching
from app.db.database import get_db
from app.models.wine import Wine
from app.utils.country_mapping import DB_TO_GEOJSON


# Add project root to path to allow importing from app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


def analyze_country_mappings(geojson_path: str) -> None:
    """
    More detailed analysis of country mappings between DB and GeoJSON.

    Args:
        geojson_path: Path to the GeoJSON file
    """
    # Create a database session
    db_generator = get_db()
    db = next(db_generator)

    try:
        # Get database countries - strip whitespace to be safe
        db_countries = {
            r[0].strip() for r in db.query(Wine.country).distinct().all() if r[0]
        }

        # Debug output
        print(f"Total countries in database: {len(db_countries)}")

        # Get GeoJSON countries
        with open(geojson_path, "r", encoding="utf-8") as f:
            geojson_data = json.load(f)

        geojson_countries = set()
        for feature in geojson_data["features"]:
            if "name" in feature["properties"]:
                # Strip whitespace to be safe
                country_name = feature["properties"]["name"].strip()
                geojson_countries.add(country_name)

        print(f"Total countries in GeoJSON: {len(geojson_countries)}")

        # Get mapped countries from our dictionary
        mapped_db_countries = set(DB_TO_GEOJSON.keys())
        mapped_geojson_countries = set(DB_TO_GEOJSON.values())

        print(f"Countries with explicit mappings: {len(mapped_db_countries)}")

        # Direct matches - countries that have exactly the same name
        direct_matches = db_countries.intersection(geojson_countries)
        print(f"Countries with exact name match: {len(direct_matches)}")

        # Find countries that need explicit mapping
        needs_mapping_db = db_countries - direct_matches - mapped_db_countries
        needs_mapping_geojson = (
            geojson_countries - direct_matches - mapped_geojson_countries
        )

        print(f"\nDatabase countries needing explicit mapping: {len(needs_mapping_db)}")
        print(f"GeoJSON countries without DB match: {len(needs_mapping_geojson)}")

        # For each DB country that needs mapping, suggest best GeoJSON matches
        print("\n=== SUGGESTED MAPPINGS ===")
        suggestions = {}

        for db_country in sorted(needs_mapping_db):
            # Use difflib to find close matches
            matches = difflib.get_close_matches(
                db_country,
                list(needs_mapping_geojson),
                n=3,  # Number of matches to return
                cutoff=0.6,  # Ratio threshold
            )

            if matches:
                # Found potential matches
                suggestions[db_country] = matches
                print(
                    f'    "{db_country}": "{matches[0]}",  # Alternatives: {matches[1:] if len(matches) > 1 else "None"}'
                )
            else:
                # No good matches found - manual intervention needed
                print(
                    f'    "{db_country}": "",  # NO MATCH FOUND - MANUAL MAPPING NEEDED'
                )

        # Print complete existing mapping for reference
        print("\n=== EXISTING MAPPINGS ===")
        for db_country, geo_country in sorted(DB_TO_GEOJSON.items()):
            print(f'    "{db_country}": "{geo_country}",')

    finally:
        # Close the database session
        db_generator.close()


if __name__ == "__main__":
    # Find path to GeoJSON file
    geojson_file = input(
        "Enter the path to your GeoJSON file (e.g., ../wine_frontend/public/data/countries.geo.json): "
    )

    # Remove any quotes that might have been included
    geojson_file = geojson_file.strip("'\"")

    # Check if file exists
    if not os.path.isfile(geojson_file):
        print(f"Error: File '{geojson_file}' not found.")
        sys.exit(1)

    # Run the improved analysis
    try:
        analyze_country_mappings(geojson_file)
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


# Run the script: python -m app.utils.country_mapping_tool
# Add the path to your GeoJSON file when prompted, without quotes.
# Example: /Users/angelicamarker/Desktop/LNU 2023-2026/lnu-ÅK2/courses/1dv027 - webben/WT2/Assignment/wine_frontend/public/data/countries.geo.json
