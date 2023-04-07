import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil import parser
from waste_collection_schedule import Collection

TITLE = "Tameside Council"
DESCRIPTION = "Tameside Council, UK - Waste Collection"
URL = "https://www.tameside.gov.uk/"

ICON_MAP = {
    "green": "mdi:trash-can-outline",
    "blue": "mdi:package-variant",
    "brown": "mdi:leaf-circle-outline",
    "black": "mdi:bottle-soda-classic-outline",
}

TEST_CASES = {  # Insert arguments for test cases to be used by test_sources.py script
    "Ashton Ikea": {"postcode": "OL6 7TE", "uprn": "10003441923"},
    "Stalybridge Train Station": {"postcode": "SK151RF", "uprn": "100012777124"},
    "Asda Hyde": {"postcode": "SK14 1BD", "uprn": "200002857459"}
}

# Page shows multiple years, get current year for filtering purposes
current_year = datetime.now().year

def get_bin_name(bin):
    if bin == "green":
        return "General Waste"
    elif bin == "blue":
        return "Cardboard"
    elif bin == "brown":
        return "Garden Waste"
    elif bin == "black":
        return "Plastic"

class Source:
    def __init__(self, postcode, uprn: str):
        self._postcode = postcode
        self._uprn = uprn

    def fetch(self):
        # If spaces have been entered in the postcode, replace them with +
        formatted_postcode = self._postcode.replace(" ", "+")
        data = {
            "AdvanceSearch": "Continue",
            "F01_I02_Postcode": formatted_postcode,
            "F01_I03_Street": "F01_I04_Town",
            "history": ",1,3,",
            "F03_I01_SelectAddress": self._uprn + "-" + formatted_postcode
        }

        r = requests.post(
            "https://public.tameside.gov.uk/forms/bin-dates.asp",
            data=data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
        )
        r.raise_for_status()

        entries = []
        # Parse HTML content
        soup = BeautifulSoup(r.content, 'html.parser')

        # Find h3 tag with class "yearHeader" and current year value
        year_header = soup.find(lambda tag: tag.name == "h3" and tag.text == str(current_year))

        # Find the parent of the h3 tag
        parent = year_header.find_parent()

        # Find the table within the parent
        table = parent.find("table")

        # Find all tr tags within the tbody
        months = table.find_all("tr")

        # Iterate through each month
        for month in months:
            # Find the first td within the tr
            month_header = month.find("td", {"class": "month"})
            # Find all td tags within the tr
            days = month.find_all("td", {"class": "day"})

            # Iterate through each day
            for day in days:
                date_str = month_header.text + " " + day.text[:-2] + " " + str(current_year)
                img_tags = day.find_all('img')
                for img in img_tags:
                    bin = img.get('alt')[:-9]
                    entries.append(
                    Collection(
                        date=parser.parse(date_str, dayfirst=True).date(),
                        t=get_bin_name(bin),
                        icon=ICON_MAP.get(bin),
                    )
                )
        return entries

