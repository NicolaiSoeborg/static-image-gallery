import csv
from datetime import datetime
from subprocess import check_output

def sort_by_exif_date(fname):
    exif = check_output(['jhead', fname]).decode()
    exif = [line.split(": ", 1) for line in exif.split("\n")]
    # Find this line: `Date/Time    : 2023:07:01 16:50:00`
    exif = [kv[1] for kv in exif if 'Date/Time' in kv[0]]
    assert len(exif) == 1, f'Exactly one line should be found: {exif}'
    return datetime.strptime(exif[0], "%Y:%m:%d %H:%M:%S")


with open('pics.tsv', newline='') as fp:
    all_files = list(csv.DictReader(fp, delimiter='\t'))

all_files = sorted(all_files, key=lambda row: sort_by_exif_date(row['fname']))

with open('pics-sorted.tsv', 'w', newline='') as fp:
    writer = csv.DictWriter(fp, delimiter='\t', fieldnames=['fname', 'pic_txt', 'section'])
    writer.writeheader()
    for row in all_files:
        writer.writerow(row)
