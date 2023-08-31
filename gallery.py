import csv, html
from base64 import b64encode
from datetime import datetime, timezone, timedelta
from functools import cache
from glob import glob
from hashlib import blake2b
from pathlib import Path
from subprocess import call, check_output

import jinja2  # pip3 install Jinja2

# pip3 install azure-storage-blob azure-identity
from azure.storage.blob import BlobServiceClient, BlobSasPermissions, generate_container_sas
from azure.identity import DefaultAzureCredential

blob_service = BlobServiceClient(account_url="https://TODO-INSERT-BLOB-NAME.blob.core.windows.net/", credential=DefaultAzureCredential())
public_container = blob_service.get_container_client("public")
assert public_container.exists()
already_uploaded = set(blob['name'] for blob in public_container.list_blobs())

sas_start_time = datetime.now(timezone.utc)
sas_expiry_time = sas_start_time + timedelta(days=265*5)
# user_sas = blob_service.get_user_delegation_key(sas_start_time, sas_expiry_time)  # <-- max len 7 days :/

template = jinja2.Environment(
    undefined=jinja2.StrictUndefined  # raise on missing vars
).from_string(open("template.html.j2", "rt").read())

ACCOUNT_KEY = "TODO-INSERT-STORAGE-ACCOUNT-KEY-HERE"
SAS_TOKEN = generate_container_sas(
    account_name=public_container.account_name,
    container_name=public_container.container_name,
    account_key=ACCOUNT_KEY,
    permission=BlobSasPermissions(read=True),
    start=sas_start_time,
    expiry=sas_expiry_time,
)

HEIGHT_SMALL = 406
HEIGHT_LARGE = 768
template_vars = {
    'title': 'Gallery',
    'description': "TODO DESC HERE",
    'public_container_url': public_container.url,
    'SAS_TOKEN': SAS_TOKEN,
    'HEIGHT_SMALL': HEIGHT_SMALL,
    'HEIGHT_LARGE': HEIGHT_LARGE,
}


@cache
def file_to_uniqname(fname: str) -> str:
    # This should be Azure Storage safe (no `-`, `_`, `=` or similar in filename)
    with open(fname, 'rb') as fp:
        return b64encode(blake2b(fp.read(), digest_size=12).digest(), altchars=b"AA").decode()

@cache
def get_exif(fname: str) -> str:
    out = check_output(['jhead', fname]).decode()
    out = '\n'.join(out.split('\n')[1:])  # Remove 'File name: full/path' row
    return out

def get_sections(images):
    """ Iterator of [(section_name, link), ...] """
    current_section = None
    for row in images:
        if section := row.get('section'):
            if section != current_section:
                yield section, f"./{file_to_uniqname(row['fname'])}.html"
                current_section = section


# Move to static file?
with open("html/navigation.js", "wt") as f:
    f.write("""
window.addEventListener('keydown', function(event) {
    const key = event.key;
    const as = Array.from(document.getElementsByTagName("a"));
    if (key === "ArrowRight") as.filter(a => a.accessKey == 'n')[0]?.click();
    if (key === "ArrowLeft") as.filter(a => a.accessKey == 'p')[0]?.click();
});

/*! Image Map Resizer (imageMapResizer.min.js ) - v1.0.10 - 2019-04-10
 *  Desc: Resize HTML imageMap to scaled image.
 *  Copyright: (c) 2019 David J. Bradshaw - dave@bradshaw.net
 *  License: MIT
 */
!function(){"use strict";function r(){function e(){var r={width:u.width/u.naturalWidth,height:u.height/u.naturalHeight},a={width:parseInt(window.getComputedStyle(u,null).getPropertyValue("padding-left"),10),height:parseInt(window.getComputedStyle(u,null).getPropertyValue("padding-top"),10)};i.forEach(function(e,t){var n=0;o[t].coords=e.split(",").map(function(e){var t=1==(n=1-n)?"width":"height";return a[t]+Math.floor(Number(e)*r[t])}).join(",")})}function t(e){return e.coords.replace(/ *, */g,",").replace(/ +/g,",")}function n(){clearTimeout(d),d=setTimeout(e,250)}function r(e){return document.querySelector('img[usemap="'+e+'"]')}var a=this,o=null,i=null,u=null,d=null;"function"!=typeof a._resize?(o=a.getElementsByTagName("area"),i=Array.prototype.map.call(o,t),u=r("#"+a.name)||r(a.name),a._resize=e,u.addEventListener("load",e,!1),window.addEventListener("focus",e,!1),window.addEventListener("resize",n,!1),window.addEventListener("readystatechange",e,!1),document.addEventListener("fullscreenchange",e,!1),u.width===u.naturalWidth&&u.height===u.naturalHeight||e()):a._resize()}function e(){function t(e){e&&(!function(e){if(!e.tagName)throw new TypeError("Object is not a valid DOM element");if("MAP"!==e.tagName.toUpperCase())throw new TypeError("Expected <MAP> tag, found <"+e.tagName+">.")}(e),r.call(e),n.push(e))}var n;return function(e){switch(n=[],typeof e){case"undefined":case"string":Array.prototype.forEach.call(document.querySelectorAll(e||"map"),t);break;case"object":t(e);break;default:throw new TypeError("Unexpected data type ("+typeof e+").")}return n}}"function"==typeof define&&define.amd?define([],e):"object"==typeof module&&"object"==typeof module.exports?module.exports=e():window.imageMapResize=e(),"jQuery"in window&&(window.jQuery.fn.imageMapResize=function(){return this.filter("map").each(r).end()})}();

imageMapResize();""")


images = list(csv.DictReader(open('pics.tsv', newline=''), delimiter='\t'))

for i, image in enumerate(images):
    fname = image['fname']
    images[i]['filesize'] = f"{round(Path(fname).stat().st_size / (1024 * 1024), 2)} MiB"
    images[i]['exif'] = html.escape(get_exif(fname))
    images[i]['pic_orig_name'] = fname.split("/")[-1]
    images[i]['unique_name'] = file_to_uniqname(fname)
    images[i]['ext'] = image['pic_orig_name'].split(".")[-1]
    unique_name_ext = image['unique_name'] + '.' + image['ext']
    print(f"Processing {fname} ({image=}) ({i} of {len(images)})")

    if i > 0:
        images[i]['prev_file'] = images[i-1]['unique_name']
        images[i-1]['next_file'] = images[i]['unique_name']

    for res in [HEIGHT_SMALL, HEIGHT_LARGE]:
        name_res = f"{image['unique_name']}-{res}.{image['ext']}"
        if name_res not in already_uploaded:
            output_path = f"/tmp/gallery/{name_res}"
            print(f'Processing {output_path}')

            blob_client = public_container.get_blob_client(name_res)
            if not blob_client.exists():
                print(f"Creating and uploading {name_res}")
                if not Path.exists(Path(output_path)):
                    quality = 95 if res == HEIGHT_LARGE else 75
                    call(['convert', '-auto-orient', '-strip', '-quality', f'{quality}', '-resize', f'x{res}', fname, output_path])
                with open(output_path, "rb") as data:
                    blob_client.upload_blob(data)

    # ugly hack to get calc converted image offsets for clicking on side of picture
    assert res == HEIGHT_LARGE
    img_details = check_output(['jhead', f"/tmp/gallery/{name_res}"]).decode()
    img_width, img_height = [row for row in img_details.split("\n") if row.startswith("Resolution")][0].split(":")[1].split(" x ")
    images[i]['xy'] = int(img_width), int(img_height)

    if unique_name_ext not in already_uploaded:
        blob_client = public_container.get_blob_client(unique_name_ext)
        assert not blob_client.exists()
        with open(fname, "rb") as data:
            blob_client.upload_blob(data)

template_vars.update({
    'sections': list(get_sections(images)),
    'images': images,
})

with open('html/index.html', 'wt') as f:
    f.write(template.render(is_index=True, **template_vars))

for i, image in enumerate(images):
    with open(f"html/{image['unique_name']}.html", 'wt') as f:
        f.write(template.render(is_index=False, image=image, img_idx=i, **template_vars))
