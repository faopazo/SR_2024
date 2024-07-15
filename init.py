import sqlite3
import os
import pandas as pd

import whoosh as wh
from whoosh import fields
from whoosh import index
from whoosh import qparser

THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))

con = sqlite3.connect(os.path.join(THIS_FOLDER, "data/data.db"))
df_vin= pd.read_sql_query("SELECT * FROM vinos", con)
con.close()

df_vin[["id_vino","vino","bodega","varietal","region"]] = df_vin[["id_vino","vino","bodega","varietal","region"]].fillna(" ")

# TODO: ver field_boost en wh.fields
schema = wh.fields.Schema(
    id_vino=wh.fields.ID(stored=True),
    bodega=wh.fields.ID(),
    varietal=wh.fields.ID(),
    region=wh.fields.ID()
)

ix = wh.index.create_in("indexdir", schema)

writer = ix.writer()
for index, row in df_vin.iterrows():
    writer.add_document(id_vino=row["id_vino"],
                        bodega=row["bodega"],
                        varietal=row["varietal"],
                        region=row["region"]
    )
writer.commit()


terminos = [wh.query.Term("varietal", "Malbec"), wh.query.Term("varietal", "Chardonnay")]
query = wh.query.Or(terminos)

with ix.searcher() as searcher:
    results = searcher.search(query, terms=True)
    for r in results:
        print(r)
