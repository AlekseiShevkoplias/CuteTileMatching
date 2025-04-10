FROM python:3.9-windowsservercore

# Install requirements
RUN pip install pyinstaller pygame

# Create working directory
WORKDIR /app

# Copy your application files
COPY . /app/

# Build the executable
CMD pyinstaller --onefile --windowed --add-data "assets;assets" --add-data "config.json;." --name "TileMatchingGame" game.py