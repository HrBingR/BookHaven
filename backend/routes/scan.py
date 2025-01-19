from flask import Blueprint, jsonify
from functions.tasks.scan import scan_library_task

scan_bp = Blueprint('scan_bp', __name__)

@scan_bp.route('/scan-library', methods=['POST'])
def trigger_scan_manually():
    scan_library_task.delay()
    return jsonify({"message": "Library scan initiated."}), 200