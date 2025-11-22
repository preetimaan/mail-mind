#!/bin/bash
# Setup script for mail-mind backend

echo "Setting up mail-mind backend..."

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Download spaCy model (must be done after spacy is installed)
echo "Downloading spaCy English model..."
# Try pip install first (more reliable), fallback to spacy download
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl || {
    echo "Trying alternative download method..."
    python -m spacy download en_core_web_sm || {
        echo "Warning: Failed to download spaCy model automatically."
        echo "You can install it manually with:"
        echo "  pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl"
    }
}

# Create data directory
mkdir -p data

# Generate encryption key if not exists
if [ ! -f .env ]; then
    echo "Generating encryption key..."
    python generate_key.py > .env.tmp
    ENCRYPTION_KEY=$(python generate_key.py | grep "ENCRYPTION_KEY=" | cut -d'=' -f2)
    cat > .env << EOF
# Database
DATABASE_URL=sqlite:///./data/mailmind.db

# Encryption
ENCRYPTION_KEY=$ENCRYPTION_KEY

# Server
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
EOF
    rm .env.tmp
    echo "Created .env file with encryption key"
else
    echo ".env file already exists, skipping key generation"
fi

echo "Setup complete!"
echo "To start the server, run:"
echo "  source venv/bin/activate"
echo "  uvicorn main:app --reload"

