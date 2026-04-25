if __name__ == "__main__":
    print("HiddenEdge Engine v1.0 | SB3PM")
# =========================================
# HiddenEdge / SB3PM Advisory & Services Ltd
# Author: Stephan Bals
# © 2026 SB3PM Advisory & Services Ltd
#
# This code is proprietary and confidential.
# Unauthorized use, distribution, or replication is prohibited.
# =========================================

import sqlite3
import os
from collections import defaultdict

BASE_DIR=os.getcwd()
DATABASE_PATH=os.path.join(BASE_DIR,"database","signals.db")

print("")
print("AIJobHunter Transformation Radar")
print("--------------------------------")

conn=sqlite3.connect(DATABASE_PATH)
cursor=conn.cursor()

cursor.execute("""
SELECT partner,client,program,source,score
FROM signals
""")

rows=cursor.fetchall()

clusters=defaultdict(list)

for r in rows:

 partner=r[0]
 client=r[1]
 program=r[2]
 source=r[3]
 score=r[4]

 key=(partner,client,program)

 clusters[key].append(score)

for k,v in clusters.items():

 partner,client,program=k

 sources=len(v)
 score=max(v)

 if sources>=3:
  confidence="HIGH"
 elif sources==2:
  confidence="MEDIUM"
 else:
  confidence="LOW"

 if score<3:
  continue

 print("")
 print("Transformation program detected")
 print("")
 print("Partner:",partner)
 print("Client:",client)
 print("Program:",program)
 print("Sources:",sources)
 print("Confidence:",confidence)

 print("")
 print("Likely upcoming roles")

 if "sap" in program:

  roles=[
  "Program Manager",
  "SAP Architect",
  "PMO Lead",
  "Agile Coach",
  "Product Owner"
  ]

 elif "cloud" in program:

  roles=[
  "Cloud Program Manager",
  "Platform Architect",
  "Agile Coach"
  ]

 else:

  roles=[
  "Transformation Manager",
  "PMO Lead",
  "Product Owner"
  ]

 for r in roles:
  print("-",r)

print("")
print("Radar scan finished")
