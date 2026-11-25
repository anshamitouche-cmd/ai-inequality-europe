# Share of artificial intelligence jobs among all job postings - Data package

This data package contains the data that powers the chart ["Share of artificial intelligence jobs among all job postings"](https://ourworldindata.org/grapher/share-artificial-intelligence-job-postings?v=1&csvType=full&useColumnShortNames=false) on the Our World in Data website. It was downloaded on November 9, 2026.

### Active Filters

A filtered subset of the full data was downloaded. The following filters were applied:

## CSV structure

Each row is an observation for an entity (usually a country or region) at a timepoint.

- "Entity" — the name of the entity, e.g. "United States".
- "Code" — our internal entity code. For most countries this is the [ISO alpha-3](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-3) code, e.g. "USA"; historical and other non-standard entities get a custom code.
- "Year" or "Day" — the timepoint. Annual data has a "Year" column holding an integer year; otherwise a "Day" column holds a date string in the form "YYYY-MM-DD".
- The final column is the data column — the time series that powers the chart. Downloaded with the "full data" option it corresponds to the time series below; with "only selected data visible in the chart" it is transformed depending on the chart type, so the correspondence may be less direct.


## Metadata.json structure

The .metadata.json file contains metadata about the data package. The "charts" key contains information to recreate the chart, like the title, subtitle etc. The "columns" key contains information about each of the columns in the csv, like the unit, timespan covered, citation for the data etc.

## How we process data at Our World in Data

Our World in Data is almost never the original producer of the data - almost all of the data we use has been compiled by others. If you want to re-use data, it is your responsibility to ensure that you adhere to the sources' license and to credit them correctly. Please note that a single time series may have more than one source - e.g. when we stitch together data from different time periods by different producers or when we calculate per capita metrics using population data from a second source.

Preparing this data involves several processing steps. Depending on the data, this can include standardizing country names and world region definitions, converting units, calculating derived indicators such as per capita measures, as well as adding or adapting metadata such as the name or the description given to an indicator.
[Read about our data pipeline](https://docs.owid.io/projects/etl/).

## Detailed information about the data


### Share of artificial intelligence jobs among all job postings
Share of job postings that require at least one AI-related skill, such as machine learning, generative AI, or natural language processing.
Last updated: April 20, 2026  
Next expected update: April 2027  
Date range: 2014–2025  
Unit: %  
Source: Lightcast via AI Index Report (2026) – with minor processing by Our World in Data  

#### How to cite this data

Lightcast via AI Index Report (2026) – with minor processing by Our World in Data

#### What you should know about this data
- A job posting is counted as an AI job if it lists at least one AI-related skill identified by Lightcast. The list of skills is updated each year to reflect new developments.
- The definition is broad, covering technical roles as well as areas such as AI ethics and governance.
- The data is based on online job postings and does not include roles that are not advertised online.


## Sources

These are the sources behind the data in this package. Each time series above names the ones it draws on in its citation.

### AI Index Report

The AI Index Report tracks, collates, distills, and visualizes data related to artificial intelligence (AI). The mission is to provide unbiased, rigorously vetted, broadly sourced data to enable policymakers, researchers, executives, journalists, and the general public to develop a more thorough and nuanced understanding of the complex field of AI.

Producer: AI Index Report  
Published: 2026-04-13  
Retrieved on: 2026-04-20  
Retrieved from: https://hai.stanford.edu/assets/files/ai_index_report_2026.pdf  
License: CC BY-ND 4.0 (https://hai.stanford.edu/assets/files/ai_index_report_2026.pdf)  

Citation: Sha Sajadieh, Loredana Fattorini, Raymond Perrault, Yolanda Gil, Vanessa Parli, Lapo Santarlasci, Juan Pava, Nestor Maslej, Russ Altman, Erik Brynjolfsson, Carla Brodley, Jack Clark, Virginia Dignum, Vipin Kumar, James Landay, Terah Lyons, James Manyika, Juan Carlos Niebles, Yoav Shoham, Elham Tabassi, Russell Wald, Toby Walsh, Dan Weld. “The AI Index 2026 Annual Report,” AI Index Steering Committee, Institute for Human-Centered AI, Stanford University, Stanford, CA, April 2026.

    