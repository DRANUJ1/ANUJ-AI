"""
Webhook Server for Anuj Bot
Flask server to handle Telegram webhooks for Render deployment
"""

import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
from threading import Thread
import json

from bot import AnujBot
from config.settings import BOT_TOKEN, WEBHOOK_URL

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize bot
bot_instance = None

def init_bot():
    """Initialize the bot instance"""
    global bot_instance
    try:
        bot_instance = AnujBot()
        logger.info("Bot initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize bot: {e}")
        bot_instance = None

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "message": "Anuj Bot Webhook Server is running",
        "bot_initialized": bot_instance is not None
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming webhook from Telegram"""
    try:
        if not bot_instance:
            logger.error("Bot not initialized")
            return jsonify({"error": "Bot not initialized"}), 500
        
        # Get update from Telegram
        update_data = request.get_json()
        
        if not update_data:
            logger.warning("No update data received")
            return jsonify({"error": "No update data"}), 400
        
        logger.info(f"Received update: {update_data}")
        
        # Process update in background thread
        def process_update():
            try:
                # Create event loop for async processing
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Process the update
                loop.run_until_complete(bot_instance.process_webhook_update(update_data))
                
                loop.close()
            except Exception as e:
                logger.error(f"Error processing update: {e}")
        
        # Start processing in background
        thread = Thread(target=process_update)
        thread.daemon = True
        thread.start()
        
        return jsonify({"status": "ok"})
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/set_webhook', methods=['POST'])
def set_webhook():
    """Set webhook URL for the bot"""
    try:
        if not bot_instance:
            return jsonify({"error": "Bot not initialized"}), 500
        
        webhook_url = request.json.get('webhook_url') if request.json else None
        
        if not webhook_url:
            # Use default webhook URL from settings
            webhook_url = WEBHOOK_URL
        
        if not webhook_url:
            return jsonify({"error": "No webhook URL provided"}), 400
        
        # Set webhook
        success = bot_instance.set_webhook(webhook_url)
        
        if success:
            return jsonify({
                "status": "ok",
                "message": f"Webhook set to {webhook_url}"
            })
        else:
            return jsonify({"error": "Failed to set webhook"}), 500
            
    except Exception as e:
        logger.error(f"Set webhook error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/get_webhook_info', methods=['GET'])
def get_webhook_info():
    """Get current webhook information"""
    try:
        if not bot_instance:
            return jsonify({"error": "Bot not initialized"}), 500
        
        webhook_info = bot_instance.get_webhook_info()
        return jsonify(webhook_info)
        
    except Exception as e:
        logger.error(f"Get webhook info error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/delete_webhook', methods=['POST'])
def delete_webhook():
    """Delete webhook (switch back to polling)"""
    try:
        if not bot_instance:
            return jsonify({"error": "Bot not initialized"}), 500
        
        success = bot_instance.delete_webhook()
        
        if success:
            return jsonify({
                "status": "ok",
                "message": "Webhook deleted successfully"
            })
        else:
            return jsonify({"error": "Failed to delete webhook"}), 500
            
    except Exception as e:
        logger.error(f"Delete webhook error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Initialize bot
    init_bot()
    
    # Get port from environment (Render provides this)
    port = int(os.environ.get('PORT', 5000))
    
    logger.info(f"Starting webhook server on port {port}")
    
    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,
        threaded=True
    )

