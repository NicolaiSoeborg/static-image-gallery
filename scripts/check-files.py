import csv
from pathlib import Path

with open('pics.tsv', newline='') as fp:
    data = list(csv.DictReader(fp, delimiter='\t'))

with open('pics-cleaned.tsv', 'w', newline='') as fp:
    writer = csv.DictWriter(fp, delimiter='\t', fieldnames=['fname', 'pic_txt', 'section'])
    writer.writeheader()
    for row in data:
        fname = row['fname']
        if Path(fname).is_file():
            writer.writerow(row)
        else:
            print(f"Missing file {fname}")

