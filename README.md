# Thumbnail downloader for Gotthelf digital edition

Downloads images for use in [https://gotthelf-digital.ch/](https://gotthelf-digital.ch/) in production and development.

Runs on demand in production environment and daily in development environment.

It caches a couple thousand images as thumbnails locally from local IIIF and Wikimedia sources.

## Rate limiting notes

This tool tries to comply with Wikimedia [rate limiting policies](https://wikitech.wikimedia.org/wiki/Robot_policy).

As of 2026-09-15:

* It uses a descriptive user agent string that includes the word "Bot" and provides contact information + link to this repository.
* The script is limited to 180 requests per minute and does not request images in parallel.
* The script should follow `Retry-After` header if error 429 is encountered.

It currently does *not*:

* Limit total bandwidth to 25 Mbps.
  * Hopefully this is not a limit we hit with ~3 requests a second.
* Coordinate a common rate limit between multiple running instances.
  * Normally should be limited to 2 instances at most; would fall back to `Retry-After`.
* Use compliant thumbnail sizes instead of full images.
  * Need to clarify that larger image size is not going to interfere with the web application.
  * After that, will switch to downloading a thumbnail.
* Provide a CIDR list for requests.
  * Instructions unclear on format; possibly only done on request from Wikimedia admins?
