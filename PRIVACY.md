# Privacy Policy — Cinematic Uploader

Last updated: 18 October 2026

Cinematic Uploader is a private automation tool used by its owner to upload
documentary videos produced by the cinematic pipeline in this repository to
the owner's own YouTube channel ("Banyak Tau") via the YouTube Data API v3.

## What data the application accesses

- The application authenticates with the channel owner's own Google account
  using OAuth 2.0 and stores the resulting credentials (client ID, client
  secret, refresh token) as encrypted GitHub Secrets in this repository.
- The application uploads video files, titles, descriptions, tags,
  thumbnails, and caption files created by the owner to the owner's channel.

## What the application does NOT do

- It does not collect, read, sell, or share personal data of any third party.
- It does not access any Google account other than the owner's own account.
- It does not share API credentials or uploaded content with third parties.

## Data retention

OAuth credentials are kept only as GitHub Secrets for as long as the owner
uses this automation, and can be revoked at any time from the owner's Google
Account permissions page.

## Contact

Questions about this policy can be raised via the repository owner through
GitHub (emsabiq-alt).
