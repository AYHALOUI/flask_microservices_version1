import json
import os
import time
from flask import Flask, jsonify, request
from tinydb import TinyDB, Query
import random


app = Flask(__name__)
data_dir = 'data'
os.makedirs(data_dir, exist_ok=True)
queue_db = TinyDB(os.path.join(data_dir, 'aymene.json'))


MAX_RETRIES = 3
RETRY_DELAY = 60


def _get_all_items():
    return queue_db.all()

def _get_item_by_id(item_id):
    Item = Query()
    items = queue_db.search(Item.id == item_id)
    return items[0] if items else None

def _add_item(item_data):
    existing_item = _get_item_by_id(item_data['id'])

    if existing_item:
        return False, 'Item already exists'
    
    if 'status' not in item_data:
        item_data['status'] = 'pending'
    if 'retry_count' not in item_data:
        item_data['retry_count'] = 0
    if 'created_at' not in item_data:
        item_data['created_at'] = time.time()
    if 'next_retry' not in item_data:
        item_data['next_retry'] = time.time()


    queue_db.insert(item_data)
    return True, 'Item added Successfully'

def _remove_item(item_id):
    """Remove an item from the queue"""
    Item = Query()
    result = queue_db.remove(Item.id == item_id)
    return len(result) > 0


def _update_retry_count(item_id, success=False):
    """Update the retry count for an item"""
    item = _get_item_by_id(item_id)
    if not item:
        return False, 'Item not found'
    
    if success:
        Item = Query()
        queue_db.update({
            'status': 'completed',
            'completed_at': time.time()
        }, Item.id == item_id)
        return True, 'Item processed successfully'
    else:
        retry_count = item.get('retry_count', 0) + 1
        if retry_count >= MAX_RETRIES:
            # Maximum retries reached, mark as permanently failed
            Item = Query()
            queue_db.update({
                'status': 'failed',
                'retry_count': retry_count,
                'failed_at': time.time(),
                'failure_reason': 'Maximum retry attempts exceeded'
            }, Item.id == item_id)
        else:
            next_retry = time.time() + RETRY_DELAY
            Item = Query()
            queue_db.update({
                'status': 'pending',
                'retry_count': retry_count,
                'last_retry': time.time(),
                'next_retry': next_retry
            }, Item.id == item_id)
            return True, f"Retry scheduled, attempt {retry_count} of {MAX_RETRIES}"

def _get_items_to_process():
    """Get Items that are ready to be processed"""
    current_time = time.time()
    Item = Query()
    return queue_db.search(
        (Item.status == 'pending') &
        (Item.next_retry <= current_time)
    )

@app.route('/queue', methods=['POST'])
def add_to_queue():
    item_data = request.json

    if not item_data:
        return jsonify({'error': 'No Item data provided'}), 400
    
    if 'id' not in item_data:
        return jsonify({'error': 'Item Id is required'}), 400
    
    if 'data' not in item_data:
        return jsonify({'error': 'Item data is required'}), 400
        
    success, message = _add_item(item_data)

    if success:
        return ({
            'status': 'success',
            'message': message
        })
    else:
        return ({
            'status': 'error',
            'message': message
        })

@app.route('/queue', methods=['GET'])
def get_queue():
    """ Get all items in the queue """
    items = _get_all_items()
    return jsonify({
        'count': len(items),
        'items': items
    })

@app.route('/queue/<item_id>', methods=['GET'])
def get_queue_item(item_id):
    """ Get a specific item from the queue """
    item = _get_item_by_id(item_id)
    if not item:
        return ({
            'error': 'Item not found'
        }), 404
    return item

@app.route('/queue/<item_id>', methods=['DELETE'])
def remove_from_queue(item_id):
    success = _remove_item(item_id)

    if success:
        return ({
            'status': 'success',
            'message': 'Item removed from queue'
        })
    else:
        return ({
            'error': 'Item not found'
        }), 404
     
    
@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'service': 'queue',
        'items_count': _get_all_items()
    })

@app.route('/process', methods=['POST'])
def process_queue():
    """Process items in the queue that are ready"""
    items_to_process = _get_items_to_process()

    if not items_to_process:
        return ({
            'status': 'info',
            'message': 'No Items to process at this time'
        })
    
    results = {
        'total': len(items_to_process),
        'succeeded': 0,
        'failed': 0
    }
   
 
    for item in items_to_process:
        succees = random.choice([True, False])
        update, message = _update_retry_count(item['id'], succees)

        if succees:
            results['succeeded'] += 1
        else:
            results['failed'] += 1
    
    return ({
        'status': 'success',
        'message': f'Processed {results["total"]} items',
        'results': results
    })

@app.route('/retry/<item_id>', methods=['POST'])
def retry_item(item_id):
    """Force retry of q specific item"""
    item = _get_item_by_id(item_id)
    if not item:
        return jsonify({
            'error': 'Item not found'
        }), 404
    
    # Set status to pending and reset next_retry to now
    Item = Query()
    queue_db.update({
        'status': 'pending',
        'next_retry': time.time() # Available for immediate processing
    }, Item.id == item_id)

    return jsonify({
        'status': 'success',
        'message': f'Item {item_id} queued for immediate retry'
    })

@app.route('/retry-failed', methods=['POST'])
def retry_all_failed():
    """Retry all failed items"""
    Item = Query()
    failed_items = queue_db.search(Item.status == 'failed')
    if not failed_items:
        return ({
            'status': 'info',
            'message': 'No failed items to retry'
        })
    count = 0
    for item in failed_items:
        queue_db.update({
            'status': 'pending',
            'retry_count': 0,
            'next_retry': time.time(),
            'failure_reason': None
        }, Item.id == item['id'])
        count+=1
    
    return ({
        'status': 'success',
        'message': f'Reset {count} failed items for retry'
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


# from flask import Flask, request, jsonify
# import os
# import time
# import logging
# import json
# from tinydb import TinyDB, Query

# app = Flask(__name__)
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logger = logging.getLogger('service_queue')

# # Create data directory if it doesn't exist
# data_dir = os.path.join(os.path.dirname(__file__), 'data')
# os.makedirs(data_dir, exist_ok=True)

# # Queue database for tracking failed operations
# queue_db = TinyDB(os.path.join(data_dir, 'queue.json'))

# # Simple retry configuration
# MAX_RETRIES = 3
# RETRY_INTERVAL = 3600  # 1 hour between retries

# # ===== Private Helper Functions =====

# def _build_error_response(message, status_code=500):
#     """Helper function to build error responses"""
#     logger.error(message)
#     return jsonify({"error": message}), status_code

# def _validate_queue_item(item_data):
#     """Validate that the queue item has all required fields"""
#     required_fields = ['id', 'entity_type', 'data', 'reason']
#     for field in required_fields:
#         if field not in item_data:
#             return False, f"Missing required field: {field}"
#     return True, None

# def _get_next_retry_time():
#     """Calculate the next retry time based on the interval"""
#     return time.time() + RETRY_INTERVAL

# def _check_existing_item(item_id):
#     """Check if an item already exists in the queue"""
#     Item = Query()
#     return queue_db.search(Item.id == item_id)

# def _filter_items(status=None, entity_type=None):
#     """Filter queue items by status and/or entity type"""
#     if not status and not entity_type:
#         return queue_db.all()
        
#     Item = Query()
#     query_parts = []
    
#     if status:
#         query_parts.append(Item.status == status)
#     if entity_type:
#         query_parts.append(Item.entity_type == entity_type)
        
#     # Execute query
#     if query_parts:
#         from functools import reduce
#         import operator
#         query = reduce(operator.and_, query_parts)
#         return queue_db.search(query)
    
#     return []

# def _get_retry_stats():
#     """Get statistics about the queue"""
#     total_items = len(queue_db.all())
    
#     # Count by status
#     Item = Query()
#     pending_count = len(queue_db.search(Item.status == 'pending'))
#     failed_count = len(queue_db.search(Item.status == 'failed'))
    
#     # Count by entity type
#     contact_count = len(queue_db.search(Item.entity_type == 'contact'))
    
#     # Count by retry count
#     retry_0 = len(queue_db.search(Item.retry_count == 0))
#     retry_1 = len(queue_db.search(Item.retry_count == 1))
#     retry_2 = len(queue_db.search(Item.retry_count == 2))
#     retry_3_plus = len(queue_db.search(Item.retry_count >= 3))
        
#     return {
#         'total': total_items,
#         'by_status': {
#             'pending': pending_count,
#             'failed': failed_count
#         },
#         'by_entity_type': {
#             'contact': contact_count
#         },
#         'by_retry_count': {
#             '0': retry_0,
#             '1': retry_1,
#             '2': retry_2,
#             '3+': retry_3_plus
#         }
#     }

# def _find_items_to_retry():
#     """Find items in the queue that are due for retry"""
#     current_time = time.time()
#     Item = Query()
#     return queue_db.search((Item.next_retry <= current_time) & (Item.status == 'pending'))

# def _update_retry_count(item_id, success):
#     """Update the retry count for an item"""
#     Item = Query()
#     item = queue_db.get(Item.id == item_id)
    
#     if not item:
#         return False
    
#     if success:
#         # Remove item from queue if successful
#         queue_db.remove(Item.id == item_id)
#         return True
    
#     # Update retry count and next retry time
#     retry_count = item.get('retry_count', 0) + 1
    
#     if retry_count >= MAX_RETRIES:
#         # Mark as failed permanently
#         queue_db.update({
#             'status': 'failed',
#             'reason': f"Exceeded maximum retry attempts ({MAX_RETRIES})",
#             'last_updated': time.time()
#         }, Item.id == item_id)
#     else:
#         # Schedule next retry
#         next_retry = _get_next_retry_time()
        
#         queue_db.update({
#             'retry_count': retry_count,
#             'last_retry': time.time(),
#             'next_retry': next_retry,
#             'status': 'pending'
#         }, Item.id == item_id)
    
#     return True

# # ===== Public API Endpoints =====

# @app.route('/health', methods=['GET'])
# def health_check():
#     """Health check endpoint"""
#     return jsonify({
#         'status': 'ok', 
#         'service': 'service_queue',
#         'queue_size': len(queue_db.all())
#     })

# @app.route('/queue', methods=['POST'])
# def add_to_queue():
#     """Add an item to the queue for retry"""
#     try:
#         item_data = request.json
        
#         if not item_data:
#             return _build_error_response('No item data provided', 400)
            
#         # Validate item data
#         valid, error_message = _validate_queue_item(item_data)
#         if not valid:
#             return _build_error_response(error_message, 400)
                
#         # Set initial retry metadata
#         item_data['status'] = 'pending'
#         item_data['queued_at'] = time.time()
#         item_data['retry_count'] = 0
#         item_data['next_retry'] = _get_next_retry_time()
        
#         # Check if item already exists in queue
#         existing_item = _check_existing_item(item_data['id'])
        
#         if existing_item:
#             return jsonify({
#                 'status': 'warning',
#                 'message': 'Item already exists in queue',
#                 'item': existing_item[0]
#             }), 200
            
#         # Add to queue
#         queue_db.insert(item_data)
            
#         return jsonify({
#             'status': 'success',
#             'message': 'Item added to queue successfully',
#             'next_retry': time.ctime(item_data['next_retry'])
#         })
        
#     except Exception as e:
#         logger.error(f"Error adding item to queue: {str(e)}")
#         return _build_error_response(str(e))

# @app.route('/queue', methods=['GET'])
# def get_queue():
#     """Get all items in the queue with optional filtering"""
#     try:
#         status = request.args.get('status')
#         entity_type = request.args.get('entity_type')
        
#         # Filter items
#         items = _filter_items(status, entity_type)
            
#         return jsonify({
#             'count': len(items),
#             'items': items
#         })
        
#     except Exception as e:
#         logger.error(f"Error retrieving queue items: {str(e)}")
#         return _build_error_response(str(e))

# @app.route('/retry', methods=['POST'])
# def process_retries():
#     """Process items in the queue that need to be retried"""
#     try:
#         # Find items that need to be retried
#         items_to_retry = _find_items_to_retry()
        
#         if not items_to_retry:
#             return jsonify({
#                 'status': 'info',
#                 'message': 'No items to retry at this time'
#             })
            
#         retry_results = {
#             'total': len(items_to_retry),
#             'processed': 0,
#             'success': 0,
#             'failed': 0,
#             'max_retries': 0
#         }
        
#         for item in items_to_retry:
#             item_id = item.get('id')
#             retry_count = item.get('retry_count', 0)
            
#             # Check if maximum retries reached
#             if retry_count >= MAX_RETRIES:
#                 # Mark as failed permanently
#                 Item = Query()
#                 queue_db.update({
#                     'status': 'failed',
#                     'reason': 'Exceeded maximum retry attempts'
#                 }, Item.id == item_id)
                
#                 retry_results['max_retries'] += 1
#                 continue
                
#             # Simulate retry operation - in a real implementation, 
#             # this would call the actual service
#             success = False
#             try:
#                 # This is where you would implement the actual retry logic
#                 # For now, we'll just simulate success/failure
#                 import random
#                 success = random.choice([True, False])
                
#                 retry_results['processed'] += 1
                
#                 if success:
#                     # Mark as successful and remove from queue
#                     Item = Query()
#                     queue_db.remove(Item.id == item_id)
#                     retry_results['success'] += 1
#                 else:
#                     # Update retry count
#                     _update_retry_count(item_id, False)
#                     retry_results['failed'] += 1
#             except Exception as e:
#                 logger.error(f"Error processing retry for item {item_id}: {str(e)}")
                
#                 # Update retry count with error
#                 Item = Query()
#                 queue_db.update({
#                     'retry_count': retry_count + 1,
#                     'last_retry': time.time(),
#                     'next_retry': _get_next_retry_time(),
#                     'status': 'pending',
#                     'last_error': str(e)
#                 }, Item.id == item_id)
                
#                 retry_results['failed'] += 1
                
#         return jsonify({
#             'status': 'success',
#             'results': retry_results
#         })
        
#     except Exception as e:
#         logger.error(f"Error processing retries: {str(e)}")
#         return _build_error_response(str(e))

# @app.route('/queue/<item_id>', methods=['GET'])
# def get_queue_item(item_id):
#     """Get a specific item from the queue"""
#     try:
#         items = _check_existing_item(item_id)
        
#         if not items:
#             return _build_error_response('Item not found in queue', 404)
            
#         return jsonify(items[0])
        
#     except Exception as e:
#         logger.error(f"Error retrieving queue item {item_id}: {str(e)}")
#         return _build_error_response(str(e))

# @app.route('/queue/<item_id>', methods=['DELETE'])
# def remove_from_queue(item_id):
#     """Remove an item from the queue"""
#     try:
#         items = _check_existing_item(item_id)
        
#         if not items:
#             return _build_error_response('Item not found in queue', 404)
            
#         Item = Query()
#         queue_db.remove(Item.id == item_id)
        
#         return jsonify({
#             'status': 'success',
#             'message': 'Item removed from queue'
#         })
        
#     except Exception as e:
#         logger.error(f"Error removing queue item {item_id}: {str(e)}")
#         return _build_error_response(str(e))

# @app.route('/stats', methods=['GET'])
# def get_stats():
#     """Get queue statistics"""
#     try:
#         stats = _get_retry_stats()
#         return jsonify(stats)
        
#     except Exception as e:
#         logger.error(f"Error retrieving stats: {str(e)}")
#         return _build_error_response(str(e))

# # NEW ENDPOINT FOR FORCING RETRIES
# @app.route('/force-retry/<item_id>', methods=['POST'])
# def force_retry(item_id):
#     """Force retry of a specific item regardless of its next_retry time"""
#     try:
#         # Check if item exists
#         items = _check_existing_item(item_id)
        
#         if not items:
#             return _build_error_response('Item not found in queue', 404)
            
#         item = items[0]
        
#         # Update the next_retry time to now
#         Item = Query()
#         queue_db.update({
#             'next_retry': time.time() - 1,  # Set to 1 second ago
#             'status': 'pending'             # Ensure status is pending
#         }, Item.id == item_id)
        
#         logger.info(f"Item {item_id} set for immediate retry")
        
#         # Try to process the retry immediately
#         items_to_retry = queue_db.search((Item.id == item_id) & (Item.status == 'pending'))
        
#         if not items_to_retry:
#             return jsonify({
#                 'status': 'warning',
#                 'message': 'Item status updated but not available for retry'
#             })
            
#         item = items_to_retry[0]
#         retry_count = item.get('retry_count', 0)
        
#         # Implement actual retry logic here
#         # For testing purposes, we'll always succeed
#         success = True
        
#         if success:
#             # Remove from queue if successful
#             queue_db.remove(Item.id == item_id)
#             return jsonify({
#                 'status': 'success',
#                 'message': f'Item {item_id} processed successfully and removed from queue'
#             })
#         else:
#             # Update retry count and schedule next retry
#             _update_retry_count(item_id, False)
#             return jsonify({
#                 'status': 'warning',
#                 'message': f'Item {item_id} processing failed, retry count updated'
#             })
        
#     except Exception as e:
#         logger.error(f"Error forcing retry for item {item_id}: {str(e)}")
#         return _build_error_response(str(e))

# # NEW ENDPOINT FOR SETTING ITEM TO FAILED STATUS
# @app.route('/set-failed/<item_id>', methods=['POST'])
# def set_failed(item_id):
#     """Set an item's status to failed, useful for testing the retry-failed endpoint"""
#     try:
#         # Check if item exists
#         items = _check_existing_item(item_id)
        
#         if not items:
#             return _build_error_response('Item not found in queue', 404)
            
#         # Update the status to failed
#         Item = Query()
#         queue_db.update({
#             'status': 'failed'
#         }, Item.id == item_id)
        
#         return jsonify({
#             'status': 'success',
#             'message': f'Item {item_id} status set to failed'
#         })
        
#     except Exception as e:
#         logger.error(f"Error setting item to failed: {str(e)}")
#         return _build_error_response(str(e))

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000, debug=True)