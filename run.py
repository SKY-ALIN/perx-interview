"""This script starts server."""

from app import Server

if __name__ == "__main__":
    s = Server(host='127.0.0.1', port=8000)
    s.run_app()
