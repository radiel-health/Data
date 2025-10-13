template = open("journal_template.jou").read()
filled = template.replace("MESH_FILE", "lidDrivenCavityFlow.msh") \
                 .replace("VALUE_U", "0.1") \
                 .replace("VALUE_ITERS", "2000") \
                 .replace("VALUE_RE", "10")

with open("run_10.jou", "w") as f:
    f.write(filled)