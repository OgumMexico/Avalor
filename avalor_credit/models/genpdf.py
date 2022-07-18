import os
import sys
fecha = sys.argv[1]
name = sys.argv[2]
json = sys.argv[3]

java = "cd /odoo/custom/addons/avalor_credit/models/; java -jar GeneraPDF.jar '"+ fecha +"' '/tmp/" + name +".pdf' "+ json+".txt"
# os.system(term)
os.system(java)
# os.system(java1)
