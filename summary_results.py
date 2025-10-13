import pandas as pd, glob, re

rows=[]
for f in glob.glob("results/Re/WSS_.txt"):
    Re=int(re.search(r'Re(\d+)', f).group(1))
    with open(f) as fh:
        try: val=float(f.readlines()[-1].split()[-1])
        except: val=None
    rows.append({'Re':Re, 'WSS_avg':val})

pd.DataFrame(rows).sort_values('Re').to_csv('results/WSS_summary.csv', index=False)
print("Saved results/WSS_summary.csv")