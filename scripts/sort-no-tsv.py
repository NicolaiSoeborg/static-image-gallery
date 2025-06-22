from glob import glob
from datetime import datetime
from subprocess import PIPE, run

def file_to_date(fname):
    exif = run(['jhead', fname], check=False, stdout=PIPE).stdout
    if not exif:
        print(f"Not an image?: {fname}")
        exif = run(['exiftool', fname], check=False, stdout=PIPE).stdout
        if not exif:
            return
    
    exif = [line.split(": ", 1) for line in exif.decode().split("\n")]
    # Find this line: `Date/Time    : 2023:07:01 16:50:00`
    ts = [kv[1] for kv in exif if 'Date/Time' in kv[0]]
    if not ts:
        # For "exiftool" output, we might find this instead:
        # Create Date        : 2025:06:01 17:50:19
        ts = [kv[1] for kv in exif if 'Create Date' in kv[0]]

    if len(ts) != 1:
        print(f'Exactly one timestamp should be found in {fname}: {ts}')
        return
    ts = ts[0]
    elif ts == "0000:00:00 00:00:00":
        print(f"Bad EXIF date: {fname}")
        return
    else:
        return datetime.strptime(ts, "%Y:%m:%d %H:%M:%S")

def doit():
    for fname in glob("*"):
        ts = file_to_date(fname)
        if ts:
            yield (fname, ts)

for fname, ts in sorted(doit(), key=lambda kv: kv[1]):
    print(f'{ts}: {fname}')
