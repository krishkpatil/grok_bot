# AI-Powered Video Script Generator

A web application that enables users to dynamically generate AI-powered video scripts using the [x.ai API](https://x.ai/api). The application features a dynamic input field that supports text input, file uploads (documents and images), and links, providing an enhanced prompt for generating scripts.

---

## Table of Contents
- [Objective](#objective)
- [Features](#features)
- [Bonus Features](#bonus-features)
- [Setup](#setup)
- [Usage](#usage)
- [Limitations](#limitations)
- [Technologies Used](#technologies-used)
- [Future Enhancements](#future-enhancements)

---

## Objective
To build a responsive, user-friendly web application that allows users to:
- Enter prompts for generating scripts.
- Upload files (e.g., `.txt`, `.pdf`, images) and extract meaningful text to improve the AI prompt.
- Use external links to fetch metadata or content.
- Generate and display AI-powered scripts dynamically using the [x.ai API](https://x.ai/api).
- Save and retrieve previously generated scripts.

---

## Features
### Core Features
1. **Dynamic Input Field**:
   - Supports text input, file uploads, and link integration.
   - Parses text from uploaded files (e.g., `.txt`, `.pdf`).
   - Optionally extracts text from images using OCR (if enabled).

2. **Script Generation**:
   - Uses the [x.ai API](https://x.ai/api) to generate AI-powered video scripts.
   - Dynamically displays generated scripts below the input field.

3. **Script Management**:
   - Save generated scripts for future use.
   - View saved scripts in a paginated and searchable library.

4. **Responsive Design**:
   - Fully responsive UI built with TailwindCSS, ensuring usability on both desktop and mobile devices.

---

## Bonus Features
1. **Interactive File Parsing**:
   - Allows users to preview and edit extracted content from uploaded files before appending it to the prompt.

2. **Pagination and Search**:
   - Provides a script library with pagination and search functionality for saved scripts.

3. **Multi-Language Support**:
   - Users can generate scripts in various languages by selecting a language option.

4. **Export Options**:
   - Enables users to download generated scripts as `.txt` or `.pdf` files.

---

## Setup

### Prerequisites
1. Python 3.x installed on your system.
2. Django framework installed (`pip install django`).
3. [x.ai API](https://x.ai/api) key for script generation.
4. TailwindCSS (CDN integration or installed locally).
5. `PyPDF2` library for PDF parsing (`pip install pypdf2`).
6. (Optional) OCR library for image text extraction, such as `Tesseract` (`pip install pytesseract`).

---

### Steps to Run Locally

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/krishkpatil/grok_bot/
   cd grok_bot
