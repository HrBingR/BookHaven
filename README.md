## NOTE
The BookHaven application is still very much under development.

While the backend has mostly reached feature-parity (for now) the frontend is still very out of date as I was focusing primarily on the backend.

My plan going forward is to start focusing on the frontend, but as a result of all of the changes done to the backend, this README is very much out of date,
and will likely result in failed deployments if used in its current state.

The README will be updated, but likely only once the frontend has reached feature-parity with the backend.

The same goes for the compose and .env example files.

# BookHaven
## Table of Contents
1. [What the Application Does]()
2. [Features]()
3. [Deployment]()
    - [Docker]()
    - [Local]()
    - [Development]()

4. [Building the Application]()


## What the Application Does
This web application allows users to read eBooks in the EPUB format directly in their browser. Designed for convenience and accessibility, it features a responsive interface optimized for both desktop and mobile use. Users can browse their eBook collection, read books with adjustable font sizes, and pick up where they left off thanks to automatic progress saving. Additionally, the app allows users to download eBooks directly onto their devices.  

Built using a modern tech stack, the frontend leverages React with the react-reader library to render and display EPUB files seamlessly in the browser, while the backend operates on Python Flask with Gunicorn as the web server. The application provides smooth animations, a clean UI, and robust performance—offering a great reading experience for all users.
## Features
- **Fast and Lightweight**
Built with React and Flask, the app provides excellent performance and a responsive, smooth experience on any device.
- **Read eBooks in the Browser**
Users can access and read their EPUB-formatted eBooks directly without any additional software.
- **Download eBooks**
Easily download a copy of any eBook in the collection to your device.
- **Non-Destructive Metadata Editing**
Changes to eBook metadata (e.g., title, author, series) are stored in the database, leaving the original EPUB files untouched.
- **Home Page with Alphabetical Sorting**
Books are sorted first alphabetically by their author and then by series, offering a clean and intuitive browsing experience.
- **Powerful Search**
The search feature on the home page allows users to filter their library by author, book title, or series, helping locate specific content quickly.
- **Author Page with Intuitive Navigation**
A dedicated author page organizes authors into a clickable alphabetical grid. Users can click on a letter to expand its list of authors, navigate to an author's page, and view their books sorted alphabetically by series and standalone titles.
- **Responsive Design**
Fully optimized for both desktop and mobile devices, ensuring a seamless experience across screen sizes.
- **Fluid Animations**
Smooth and visually pleasing animations enhance navigation and interaction with the application.
- **React Reader Integration**
Uses the react-reader library to render EPUB files in the browser, supporting adjustable font sizes and progress saving.
- **Modern Backend**
Python Flask is used as the backend framework, coupled with Gunicorn as the lightweight web server for efficient request handling.
- **Supports Multiple Databases**
Compatible with MySQL, PostgreSQL, or SQLite for storing metadata.

## Deployment
### Docker
Follow these steps to deploy the application with Docker Compose:
1. **Download Configuration Files**

Download or clone the repository to get `compose.yml.example` and `.env.example`.
2. **Rename the Example Files**
``` bash
   mv compose.yml.example compose.yml
   mv .env.example .env
```
3. **Customize the `.env` File**

Edit `.env` to configure essential settings:

    - **BASE_DIRECTORY**: Path to your eBooks directory.
    - **BASE_URL**: URL where your app will be accessible.
    - **DB_TYPE**: Database engine (e.g., mysql, sqlite, postgres).
    - _Other DB_ settings_* for your database configuration.

4. **Start the Application**

Run the following command:
``` bash
   docker compose up -d
```
This starts the `epub-reader` and MySQL containers.
5. **Access the Application**

Open your browser and navigate to the `BASE_URL` you configured (default is `http://localhost:5000`).
6. **Stopping the Application**

To stop the service:
``` bash
   docker compose down
```

### Local
To run the application locally (without Docker):
1. Clone the repository:
``` bash
   git clone https://github.com/HrBingR/epubdl.git
```
1. **Set up the Backend**:
``` bash
   cd epubdl/backend
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
```
2. **Create a `.env` file**: Add the following minimum options:
``` plaintext
   BASE_DIRECTORY=/path/to/ebooks
   BASE_URL=http://127.0.0.1
   DB_TYPE=mysql  # or sqlite, postgres
   DB_USER=username  # Omit for SQLite
   DB_PASSWORD=secure_password  # Omit for SQLite
   DB_HOST=host  # Omit for localhost or SQLite
   DB_PORT=port  # Defaults: 3306 for MySQL, 5432 for PostgreSQL
```
3. **Start the Backend**:
``` bash
   gunicorn -w 1 -b 0.0.0.0:5000 main:app
```
4. **Set up the Frontend**:
``` bash
   cd ../frontend
   npm install
   npm run build
```
5. **Access the Application**:

Open your browser to `http://127.0.0.1:5000`.

### Development
The steps for development are similar to running locally, but with a slight change for easier debugging:
1. After setting up the backend, run:
``` bash
   cd ../frontend
   npm install
   npm run dev
```
2. Access the development server at:
``` plaintext
   http://localhost:5173
```
This allows for live updates during development instead of needing to rebuild.
## Building the Application
To build the application for production:
1. **Build the Frontend**:
``` bash
   cd frontend
   npm run build
```
2. **Build the Docker Image**:

In the root project directory (epubdl), run:
``` bash
   docker build -t tag:version .
```
Replace `tag:version` with your preferred image name and version (e.g., `epub-reader:1.0.0`).
