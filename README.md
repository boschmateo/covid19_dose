# Vacunació per al COVID-19: dosis administrades per municipi

This repository fetches the data from the Open Data dataset [Vacunació per al COVID-19: dosis administrades per municipi](https://analisi.transparenciacatalunya.cat/Salut/Vacunaci-per-al-COVID-19-dosis-administrades-per-m/irki-p3c7).
It fetches for each day and county the number of first vaccines doses delivered and stores it in a PostgreSQL database.
The script is intended to be run each day.


## Requirements

- Python 3 and its requirements listed in `requirements.txt`.
```
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```
- A PostgreSQL database. It is expected to set up a `.env` file with the database URI.
```
echo "DB_URI=postgresql://postgres:postgres@localhost:5432/covid19" >.env
```

Note that the database should be up and running for the script to work. This repository 
also holds a `docker-compose.yml` file that automatically sets up the database.
```
docker-compose -f docker-compose.yml up
```

## Usage

The usage of this repository is straightforward. Be sure to have the desired database up and running or a 
`sqlalchemy.exc.OperationalError` error will be raised.

The script to run is named `doses.py` and only accepts one parameter:
- __--create__: This flag makes the script create a table on the specified 
    database in the `DB_URI` variable inside the `.env` file. Note that if you are already using the database provided 
    in this repository the table is automatically created when setting up the docker container. This flag does 
    not override the current table and if it already exists it is ignored.
    

Example:

```
python3 doses.py --create
```


## Repository structure

The structure of the repository is as follows:

- __setup_scripts__: This folder contains the scripts that will set up the database when using Docker.
- __docker-compose.yml__: File containing the description of the docker containers to create.
- __doses.py__: Main script to be run.
- __open_data.py__: File that contains the main class that handles the logic behind fetching the data, 
    transforming it and persisting it in the database.
- __requirements.txt__: File containing the necessary modules for this script to run.


## How is the data fetched?

The logic for fetching the data is pretty simple.

1. Get the latest date available in the database, if any. This will allow to only fetch new data that is not present in
    the database.

2. Call the API endpoint that will return only the necessary information. Just in case the dataset could be bigger,
 the data is fetch through paging by a limit of 50.000 rows each time.

3. Once we obtain all the new data, it is grouped by DATA and COMARCA and the total of doses is aggregated using the SUM function in the RECOMPTE column.

4. Data is persisted in the database with the next schema. The data is assured to never be duplicated thanks to DATA and COMARCA being its PRIMARY KEY.


![Database schema](img/schema.png)