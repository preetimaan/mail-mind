#!/bin/bash
# Setup script for mail-mind backend

echo "Setting up mail-mind backend..."

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

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
