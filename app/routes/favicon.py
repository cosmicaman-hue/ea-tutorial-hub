"""
Favicon and Manifest Routes
Serves consistent Excel Academy favicon and web manifest across all platforms.
"""
from flask import Blueprint, send_file, current_app, send_from_directory
import os

favicon_bp = Blueprint('favicon', __name__)


@favicon_bp.route('/favicon.ico')
def favicon():
    """Serve favicon.ico for browser requests"""
    try:
        return send_from_directory(
            current_app.static_folder,
            'ea-icon.svg',
            mimetype='image/svg+xml'
        )
    except Exception as e:
        print(f"Error serving favicon: {e}")
        # Return a minimal SVG if file not found
        return '''<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">
            <rect width="32" height="32" fill="#1d4ed8"/>
            <text x="16" y="22" text-anchor="middle" font-size="20" fill="#fff" font-weight="bold">EA</text>
        </svg>''', 200, {'Content-Type': 'image/svg+xml'}


@favicon_bp.route('/site.webmanifest')
def webmanifest():
    """Serve web manifest for PWA support"""
    try:
        return send_from_directory(
            current_app.static_folder,
            'offline_manifest.webmanifest',
            mimetype='application/manifest+json'
        )
    except Exception as e:
        print(f"Error serving manifest: {e}")
        # Return a minimal manifest if file not found
        return {
            "name": "EXCEL ACADEMY",
            "short_name": "EA",
            "start_url": "/",
            "display": "standalone",
            "background_color": "#ffffff",
            "theme_color": "#1d4ed8"
        }, 200, {'Content-Type': 'application/manifest+json'}


@favicon_bp.route('/apple-touch-icon.png')
def apple_touch_icon():
    """Serve Apple touch icon"""
    try:
        return send_from_directory(
            current_app.static_folder,
            'ea-icon.svg',
            mimetype='image/svg+xml'
        )
    except Exception as e:
        print(f"Error serving apple touch icon: {e}")
        # Return a minimal SVG if file not found
        return '''<svg xmlns="http://www.w3.org/2000/svg" width="180" height="180" viewBox="0 0 180 180">
            <rect width="180" height="180" fill="#1d4ed8" rx="40"/>
            <text x="90" y="110" text-anchor="middle" font-size="80" fill="#fff" font-weight="bold">EA</text>
        </svg>''', 200, {'Content-Type': 'image/svg+xml'}
