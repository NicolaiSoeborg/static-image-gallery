# static-image-gallery

Simple program to create a gallery with images hosted on Azure Storage Account (think S3, can easily be extended to use S3 instead<!-- I'll happily accept a PR!-->).

Requirements:
 * `jhead` binary in `$PATH`
 * `pip3 install Jinja2 azure-storage-blob azure-identity`
 * Create an Azure Blob Account with a folder called `public/` and copy the `ACCOUNT_KEY` into `gallery.py`
 * Fill out `pics.tsv` (use `sort-tsv.py` to sort by date)
 * Run `gallery.py` and host the content of `html/` somewhere public
