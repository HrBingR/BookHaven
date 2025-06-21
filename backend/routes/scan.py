from flask import Blueprint, jsonify
from functions.tasks.scan import scan_library_task
from celery_app import celery

scan_bp = Blueprint('scan_bp', __name__)

@scan_bp.route('/scan-library', methods=['POST'])
def trigger_scan_manually():
    task = scan_library_task.delay()
    return jsonify({"task_id": task.id}), 200

@scan_bp.route('/scan-status/<task_id>', methods=['GET'])
def get_scan_status(task_id):
    result = celery.AsyncResult(task_id)
    return jsonify({"state": result.state}), 200
