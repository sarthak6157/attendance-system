services:
  - type: web
    name: smart-attendance-system
    env: python
    region: singapore          # closest to India
    plan: free
    rootDir: backend
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: SECRET_KEY
        generateValue: true    # Render auto-generates a secure random key
      - key: PYTHON_VERSION
        value: 3.11.0
