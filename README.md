# static-image-gallery

Simple program to create a gallery with images hosted on Azure Storage Account (can easily be extended to use S3 instead<!-- I'll happily accept a PR!-->).

Requirements:
 * `jhead` binary in `$PATH`
 * `pip3 install Jinja2 azure-storage-blob azure-identity`
 * Create an Azure Blob Account with a folder called `public/` and add `subscription_id` and `resource group` name in `gallery.py`
 * Assign your account role `Storage Blob Data Contributor` to your account on the Storage Account
 * Fill out `pics.tsv` (use `scripts/sort-tsv.py` to sort by date)
 * Run `gallery.py` and host the content of `html/` somewhere public

## Demo

![Showing index with sections and overview of all images](demo.png)

## FAQ

`This request is not authorized to perform this operation using this permission.` => Try to re-login to az-cli.
