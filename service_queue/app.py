from flask import Flask, request, jsonify
import os
import time
import logging
import json
from tinydb import TinyDB, Query

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('service_queue')

# Create data directory if it doesn't exist
data_dir = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(data_dir, exist_ok=True)

# Queue database for tracking failed operations
queue_db = TinyDB(os.path.join(data_dir, 'queue.json'))

# Simple retry configuration
MAX_RETRIES = 3
RETRY_INTERVAL = 3600  # 1 hour between retries

# ===== Private Helper Functions =====

def _build_error_response(message, status_code=500):
    """Helper function to build error responses"""
    logger.error(message)
    return jsonify({"error": message}), status_code

def _validate_queue_item(item_data):
    """Validate that the queue item has all required fields"""
    required_fields = ['id', 'entity_type', 'data', 'reason']
    for field in required_fields:
        if field not in item_data:
            return False, f"Missing required field: {field}"
    return True, None

def _get_next_retry_time():
    """Calculate the next retry time based on the interval"""
    return time.time() + RETRY_INTERVAL

def _check_existing_item(item_id):
    """Check if an item already exists in the queue"""
    Item = Query()
    return queue_db.search(Item.id == item_id)

def _filter_items(status=None, entity_type=None):
    """Filter queue items by status and/or entity type"""
    if not status and not entity_type:
        return queue_db.all()
        
    Item = Query()
    query_parts = []
    
    if status:
        query_parts.append(Item.status == status)
    if entity_type:
        query_parts.append(Item.entity_type == entity_type)
        
    # Execute query
    if query_parts:
        from functools import reduce
        import operator
        query = reduce(operator.and_, query_parts)
        return queue_db.search(query)
    
    return []

def _get_retry_stats():
    """Get statistics about the queue"""
    total_items = len(queue_db.all())
    
    # Count by status
    Item = Query()
    pending_count = len(queue_db.search(Item.status == 'pending'))
    failed_count = len(queue_db.search(Item.status == 'failed'))
    
    # Count by entity type
    contact_count = len(queue_db.search(Item.entity_type == 'contact'))
    
    # Count by retry count
    retry_0 = len(queue_db.search(Item.retry_count == 0))
    retry_1 = len(queue_db.search(Item.retry_count == 1))
    retry_2 = len(queue_db.search(Item.retry_count == 2))
    retry_3_plus = len(queue_db.search(Item.retry_count >= 3))
        
    return {
        'total': total_items,
        'by_status': {
            'pending': pending_count,
            'failed': failed_count
        },
        'by_entity_type': {
            'contact': contact_count
        },
        'by_retry_count': {
            '0': retry_0,
            '1': retry_1,
            '2': retry_2,
            '3+': retry_3_plus
        }
    }

def _find_items_to_retry():
    """Find items in the queue that are due for retry"""
    current_time = time.time()
    Item = Query()
    return queue_db.search((Item.next_retry <= current_time) & (Item.status == 'pending'))

def _update_retry_count(item_id, success):
    """Update the retry count for an item"""
    Item = Query()
    item = queue_db.get(Item.id == item_id)
    
    if not item:
        return False
    
    if success:
        # Remove item from queue if successful
        queue_db.remove(Item.id == item_id)
        return True
    
    # Update retry count and next retry time
    retry_count = item.get('retry_count', 0) + 1
    
    if retry_count >= MAX_RETRIES:
        # Mark as failed permanently
        queue_db.update({
            'status': 'failed',
            'reason': f"Exceeded maximum retry attempts ({MAX_RETRIES})",
            'last_updated': time.time()
        }, Item.id == item_id)
    else:
        # Schedule next retry
        next_retry = _get_next_retry_time()
        
        queue_db.update({
            'retry_count': retry_count,
            'last_retry': time.time(),
            'next_retry': next_retry,
            'status': 'pending'
        }, Item.id == item_id)
    
    return True

# ===== Public API Endpoints =====

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok', 
        'service': 'service_queue',
        'queue_size': len(queue_db.all())
    })

@app.route('/queue', methods=['POST'])
def add_to_queue():
    """Add an item to the queue for retry"""
    try:
        item_data = request.json
        
        if not item_data:
            return _build_error_response('No item data provided', 400)
            
        # Validate item data
        valid, error_message = _validate_queue_item(item_data)
        if not valid:
            return _build_error_response(error_message, 400)
                
        # Set initial retry metadata
        item_data['status'] = 'pending'
        item_data['queued_at'] = time.time()
        item_data['retry_count'] = 0
        item_data['next_retry'] = _get_next_retry_time()
        
        # Check if item already exists in queue
        existing_item = _check_existing_item(item_data['id'])
        
        if existing_item:
            return jsonify({
                'status': 'warning',
                'message': 'Item already exists in queue',
                'item': existing_item[0]
            }), 200
            
        # Add to queue
        queue_db.insert(item_data)
            
        return jsonify({
            'status': 'success',
            'message': 'Item added to queue successfully',
            'next_retry': time.ctime(item_data['next_retry'])
        })
        
    except Exception as e:
        logger.error(f"Error adding item to queue: {str(e)}")
        return _build_error_response(str(e))

@app.route('/queue', methods=['GET'])
def get_queue():
    """Get all items in the queue with optional filtering"""
    try:
        status = request.args.get('status')
        entity_type = request.args.get('entity_type')
        
        # Filter items
        items = _filter_items(status, entity_type)
            
        return jsonify({
            'count': len(items),
            'items': items
        })
        
    except Exception as e:
        logger.error(f"Error retrieving queue items: {str(e)}")
        return _build_error_response(str(e))

@app.route('/retry', methods=['POST'])
def process_retries():
    """Process items in the queue that need to be retried"""
    try:
        # Find items that need to be retried
        items_to_retry = _find_items_to_retry()
        
        if not items_to_retry:
            return jsonify({
                'status': 'info',
                'message': 'No items to retry at this time'
            })
            
        retry_results = {
            'total': len(items_to_retry),
            'processed': 0,
            'success': 0,
            'failed': 0,
            'max_retries': 0
        }
        
        for item in items_to_retry:
            item_id = item.get('id')
            retry_count = item.get('retry_count', 0)
            
            # Check if maximum retries reached
            if retry_count >= MAX_RETRIES:
                # Mark as failed permanently
                Item = Query()
                queue_db.update({
                    'status': 'failed',
                    'reason': 'Exceeded maximum retry attempts'
                }, Item.id == item_id)
                
                retry_results['max_retries'] += 1
                continue
                
            # Simulate retry operation - in a real implementation, 
            # this would call the actual service
            success = False
            try:
                # This is where you would implement the actual retry logic
                # For now, we'll just simulate success/failure
                import random
                success = random.choice([True, False])
                
                retry_results['processed'] += 1
                
                if success:
                    # Mark as successful and remove from queue
                    Item = Query()
                    queue_db.remove(Item.id == item_id)
                    retry_results['success'] += 1
                else:
                    # Update retry count
                    _update_retry_count(item_id, False)
                    retry_results['failed'] += 1
            except Exception as e:
                logger.error(f"Error processing retry for item {item_id}: {str(e)}")
                
                # Update retry count with error
                Item = Query()
                queue_db.update({
                    'retry_count': retry_count + 1,
                    'last_retry': time.time(),
                    'next_retry': _get_next_retry_time(),
                    'status': 'pending',
                    'last_error': str(e)
                }, Item.id == item_id)
                
                retry_results['failed'] += 1
                
        return jsonify({
            'status': 'success',
            'results': retry_results
        })
        
    except Exception as e:
        logger.error(f"Error processing retries: {str(e)}")
        return _build_error_response(str(e))

@app.route('/queue/<item_id>', methods=['GET'])
def get_queue_item(item_id):
    """Get a specific item from the queue"""
    try:
        items = _check_existing_item(item_id)
        
        if not items:
            return _build_error_response('Item not found in queue', 404)
            
        return jsonify(items[0])
        
    except Exception as e:
        logger.error(f"Error retrieving queue item {item_id}: {str(e)}")
        return _build_error_response(str(e))

@app.route('/queue/<item_id>', methods=['DELETE'])
def remove_from_queue(item_id):
    """Remove an item from the queue"""
    try:
        items = _check_existing_item(item_id)
        
        if not items:
            return _build_error_response('Item not found in queue', 404)
            
        Item = Query()
        queue_db.remove(Item.id == item_id)
        
        return jsonify({
            'status': 'success',
            'message': 'Item removed from queue'
        })
        
    except Exception as e:
        logger.error(f"Error removing queue item {item_id}: {str(e)}")
        return _build_error_response(str(e))

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get queue statistics"""
    try:
        stats = _get_retry_stats()
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error retrieving stats: {str(e)}")
        return _build_error_response(str(e))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)