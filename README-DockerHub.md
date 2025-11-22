# BookHaven

![BookHaven Home](https://raw.githubusercontent.com/HrBingR/BookHaven/refs/heads/master/bookhaven_home.png)

## Table of Contents
1. [What the Application Does](#what-the-application-does)
2. [Features](#features)
3. [Deployment](#deployment)
   - [Docker](#docker)
   - [Development](#development)
4. [Building the Application](#building-the-application)
5. [Change log](#change-log)


## What the Application Does
BookHaven scans and manages your local library of EPUB ebooks, and allows you to read and download your ebooks on any of your devices, with a sleek, modern, and responsive interface.

## Features
- **Read eBooks in the Browser**
  Users can access and read their EPUB-formatted eBooks directly without any additional software.
- **Download eBooks**
  Easily download a copy of any eBook in the collection to your device.
- **Non-Destructive Metadata Editing**
  Changes to eBook metadata (e.g., title, author, series) are stored in the database, leaving the original EPUB files untouched.
- **Automatic or Manual Library Scanning**
  Once deployed the app will periodically, on a configurable interval, scan your library for any changes, while also allowing for manual library scans.
- **Home Page with Alphabetical Sorting**
  Books are sorted first alphabetically by their author and then by series, offering a clean and intuitive browsing experience.
- **Powerful Search**
  The search feature on the home page allows users to filter their library by author, book title, or series, helping locate specific content quickly.
- **Filters**
  Basic filters are made available to allow filtering for books marked as favorite, as finished, or books that haven't been marked as finished.
- **Author Page with Intuitive Navigation**
  A dedicated author page organizes authors into a clickable alphabetical grid. Users can click on a letter to expand its list of authors, navigate to an author's page, and view their books sorted alphabetically by series and standalone titles.
- **Supports CloudFlare Access**
  Has a flag to bypass the login screen when making use of CloudFlare Access. See `.env.example` for details.
- **OIDC Support**
  Allows for the configuration of OIDC for new user registration, and for existing users.
- **OPDS Support**
  Use your favorite OPDS-compatible e-reader or app to browse, download, and read books from your library.
- **Uploads**
  Users can now upload ebooks directly via the user interface, with a post-upload form to fix the metadata.
- **Basic RBAC Support**
  Admins can now give users different roles with different levels of access.
- **Book Requests**
  Users can now request specific books they'd like to see on the site. Admins and editors can view and resolve these requests once uploaded/added.

## Requirements

At a minimum to run the application you require:

- A database (MySQL, SQLite, PostgreSQL)
- A Redis instance

For quick and easy deployment the .compose.yml.example defines both of these already.

## Docker
Follow these steps to deploy the application with Docker Compose:

**Download Configuration Files**

Download or clone the repository to get `compose.yml.example` and `.env.example`.

**Rename the Example Files**

``` bash
   mv compose.yml.example compose.yml
   mv .env.example .env
```

**Customize the `.env` File**

Edit `.env` to configure essential settings.

**Start the Application**

Run the following command:
``` bash
   docker compose up -d
```
This starts the `BookHaven`, Redis, and MySQL containers.

**Access the Application**

Open your browser and navigate to the `BASE_URL`:`APP_PORT` you configured (default is `http://localhost:5000`).

**Stopping the Application**

``` bash
   docker compose down
```

## Development
Follow these steps to deploy for development:

**Clone the repository**:

``` bash
   git clone https://github.com/HrBingR/BookHaven.git
   cd BookHaven
```

**Rename the example files**:

```bash
   mv compose.exmaple.yml compose.yml
   mv .env.example .env
```

**Customize the `.env` file**:

Edit `.env` to configure essential settings.

**Modify the `compose.yml` file**:

Change:

```yaml
    epub-reader:
       image: hrbingr/bookhaven:latest
```

To:

```yaml
  epub-reader:
     build:
        context: .
        dockerfile: Dockerfile
```

**Build the container**:
```bash
   docker compose up --build -d
```

**Access the app**:

Access the app on the `BASE_URL` and `APP_PORT` defined in the `.env` file.

## Building the Application
To build the application for production:

**Build the Frontend**:

``` bash
   cd frontend
   npm run build:dev
```

**Build the Docker Image**:

In the root project directory (BookHaven), run:
``` bash
   docker build -t tag:version .
```

Replace `tag:version` with your preferred image name and version (e.g., `bookhaven:1.0.0`).

## Change log:

Note: The below is a highly summarized change-log for all but the latest versions.

For detailed changelog [check Github](https://github.com/HrBingR/BookHaven/blob/master/CHANGELOG.md)

- v1.0.x - v1.3.5
  - Initial Release
  - Added OIDC support
  - Added support for optionally writing metadata to the ePub file, instead of just to the database.
  - Added OPDS support.
  - Updated scan logic - library will now be automatically scanned on start
  - Implemented locking for the scan process to ensure only one scan runs at a time
  - Other minor improvements 
  - Various bug fixes
- v1.4.0 - v1.5.2
  - Added Upload functionality - check .env.example on how to enable and use
  - Added basic role-based access (RBAC)
  - Other minor improvements
  - Various bug fixes
- v.1.6.0
  - Added requests feature for users to request for new books to be added to the site.
- v.1.7.0
  - Updated scanning methodology to store new cover images to disk.
  - Added migrations to remove all existing images from the DB - a shortsighted architectural decision made at project inception - and store them to disk.
  - Added pyvips for rapid image conversion to webp, and image resize to h:300px, to improve performance when serving cover images.
  - Implemented redis caching for media endpoints, reducing the need for slower DB queries for cover image and ebook path retrieval, while maintaining DB fallback.
  - Fixed logic to actually disable OPDS when disabled in config, rather than simply not creating the required Redis instance.
  - Collapsed and streamlined redis DB config & properties to simplify usage.
- v.1.7.1
  - Fixed some logic issues surrounding Redis
- v.1.7.2
  - Fixed a minor bug involving data type mismatches.

## TODO:

- Update tests with latest additions
- Explore support for other formats
- Explore adding more metadata fields for editing