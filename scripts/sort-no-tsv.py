from glob import glob
from datetime import datetime
from subprocess import PIPE, run

def file_to_date(fname):
    exif = run(['jhead', fname], check=False, stdout=PIPE).stdout
    if not exif:
        print(f"Has no EXIF: {fname}")
        return
    exif = [line.split(": ", 1) for line in exif.decode().split("\n")]
    # Find this line: `Date/Time    : 2023:07:01 16:50:00`
    exif = [kv[1] for kv in exif if 'Date/Time' in kv[0]]
    if len(exif) != 1:
        print(f'Exactly one line should be found in {fname}: {exif}')
        return
    elif exif[0] == "0000:00:00 00:00:00":
        print(f"Bad EXIF date: {fname}")
        return
    else:
        return datetime.strptime(exif[0], "%Y:%m:%d %H:%M:%S")

def doit():
    for fname in glob("*"):
        ts = file_to_date(fname)
        if ts:
            yield (fname, ts)

for fname, ts in sorted(doit(), key=lambda pair: pair[1]):
    print(f'{ts}: {fname}')
