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
