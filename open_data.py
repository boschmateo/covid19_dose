from sodapy import Socrata
import pandas as pd
import numpy as np
from decouple import config
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import logging


class OpenData:
    """
    Class that fetches the "Vacunació per al COVID-19: dosis administrades per municipi" dataset
    (https://analisi.transparenciacatalunya.cat/Salut/Vacunaci-per-al-COVID-19-dosis-administrades-per-m/irki-p3c7)
    and stores for each day and county the number of first vaccine doses that were delivered
    """

    def __init__(self):
        self.client = Socrata("analisi.transparenciacatalunya.cat", None)
        self.engine = create_engine(config("DB_URI"))
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    def create_table(self):
        """
        Method that creates the doses stable specified in the database
        """
        with self.engine.connect() as con:
            # Check if the table already exists
            exists = con.execute("SELECT exists (select 1 from information_schema.tables where table_name ='doses')").fetchone()[0]

            if exists is None: # If the table dos not exists create it.
                con.execute("""
                    CREATE TABLE doses(
                        "DATA" DATE,
                        "COMARCA" TEXT,
                        "RECOMPTE" INTEGER,
                        PRIMARY KEY ("DATA", "COMARCA")
                    )
                """)
                self.logger.log(logging.INFO, "Table doses created")
            else:
                self.logger.log(logging.INFO, "Table doses already exists. Ignoring flag")

    def fetch_all(self):
        """
        Method that finds the last date that there is information in the database (if any).
        Then it proceeds to download and persist the new rows
        """
        self.logger.log(logging.INFO, "Proceeding to fetch ALL the new rows")
        with self.engine.connect() as con:
            # Check the last date the script holds information from.
            # This will allow to obtain only new information in the dataset.
            max_date = con.execute("SELECT MAX(\"DATA\"::date) FROM doses").fetchone()[0]
        self._fetch(max_date)

    def _fetch(self, date):
        """
        Method that given a date fetches the open data portal dataset and persists its information.
        The desired information is grouped by COMARCA and DATA to obtain the aggregate number of RECOMPTE.
        :param date: Nullable. Fetched rows will be grater than given date
        """
        limit = 50000
        offset = 0

        # Get all the new data by paging
        data = self._get_data(date, limit, offset)
        all_rows = data
        while len(data) != 0:
            offset += limit
            data = self._get_data(date, limit, offset)
            all_rows += data

        if len(all_rows) == 0:  # Ignore if there are no new rows
            self.logger.log(logging.INFO, "No new rows found")
        else:   # If there are new rows, group them by DATA and COMARCA and get the total RECOMPTE
            df = pd.DataFrame(all_rows)
            df = df.astype({"DATA": np.datetime64, "RECOMPTE": np.int16})
            df = df.groupby(["DATA", "COMARCA"], as_index=False).agg({"RECOMPTE": "sum"})
            df.to_sql("doses", con=config("DB_URI"), if_exists="append", index=False)

            self.logger.log(logging.INFO, "{} new rows found".format(len(df.index)))

    def _get_data(self, date, limit=50000, offset=0):
        """
        Method that directly fetches from the Open Data portal the desired rows. The query looks like:
            SELECT DATA, COMARCA, RECOMPTE
            FROM irki-p3c7
            WHERE DOSI=1 AND NO_VACUNAT IS NULL AND DATE > date
            LIMIT limit
            OFFSET offset
        :param date: Nullable. Returned rows will be grater than given date
        :param limit: Limit of rows the API endpoint will return
        :param offset: Offset in the rows to allow paging
        :return: Returns a list with a json in each position.
        """
        # The WHERE clausule might have a date restriction
        where = "DOSI=1 AND NO_VACUNAT IS NULL"
        if date is not None:  # If there is a date restriction append it to the query
            where += " AND DATA>'{}'".format(str(date))
        # Get the data
        return self.client.get(
            "irki-p3c7",
            limit=limit,
            offset=offset,
            select="DATA, COMARCA, RECOMPTE",
            where=where,
            order="DATA DESC"
        )