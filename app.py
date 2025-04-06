from flask import Flask, request, jsonify, render_template
import logging
import os
from dotenv import load_dotenv
import user_recommender
import x_research_agent
import youtube_research_agent
import editor_agent
import json

# Load environment variables
load_dotenv(override=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default-secret-key")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/workflow', methods=['POST'])
def start_workflow():
    """Start a complete content research and creation workflow."""
    try:
        data = request.json
        workflow_type = data.get('type', '')
        category = data.get('category', '').strip()
        num_accounts = int(data.get('num_accounts', 5))
        
        if not category:
            return jsonify({
                'status': 'error',
                'message': 'Please enter a category'
            }), 400
        
        # Split category into multiple filters
        categories = [c.strip() for c in category.split() if c.strip()]
        if len(categories) > 5:
            return jsonify({
                'status': 'error',
                'message': 'Please use at most 5 category filters for best results'
            }), 400
        
        try:
            if workflow_type == 'recommend':
                # Find relevant accounts
                accounts = user_recommender.find_accounts(categories, num_accounts=num_accounts)
                if not accounts:
                    return jsonify({
                        'status': 'error',
                        'message': 'No accounts found matching your criteria. Try adjusting your search.'
                    }), 404
                
                return jsonify({
                    'status': 'success',
                    'accounts': accounts
                })
                
            elif workflow_type == 'research':
                # Research content
                research = x_research_agent.research_topics(categories)
                return jsonify({
                    'status': 'success',
                    'research': research
                })
                
            elif workflow_type == 'full':
                # Full workflow
                accounts = user_recommender.find_accounts(categories, num_accounts=num_accounts)
                if not accounts:
                    return jsonify({
                        'status': 'error',
                        'message': 'No accounts found matching your criteria. Try adjusting your search.'
                    }), 404
                
                research = x_research_agent.research_topics(categories)
                content = editor_agent.improve_content(research)
                
                return jsonify({
                    'status': 'success',
                    'accounts': accounts,
                    'research': research,
                    'content': content
                })
            
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid workflow type'
                }), 400
                
        except Exception as e:
            logger.error(f"Error in workflow: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
            
    except Exception as e:
        logger.error(f"Error parsing request: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Invalid request format'
        }), 400

@app.route('/api/recommend', methods=['POST'])
def recommend_accounts():
    """Find relevant social media accounts."""
    data = request.json
    platform = data.get('platform')
    category = data.get('category', '').strip()
    num_accounts = int(data.get('num_accounts', 10))
    
    if not category:
        return jsonify({
            'status': 'error',
            'message': 'Please enter a category'
        }), 400
    
    if not (1 <= num_accounts <= 20):
        return jsonify({
            'status': 'error',
            'message': 'Number of accounts must be between 1 and 20'
        }), 400
    
    try:
        logger.info(f"Starting recommendation search for {platform} in category: {category}")
        
        # Get initial recommendations from ChatGPT
        recommendations = user_recommender.get_chatgpt_recommendations(platform, [category], num_accounts)
        accounts = user_recommender.parse_recommendations(recommendations)
        
        # Enrich data based on platform
        if platform == 'X':
            accounts = user_recommender.enrich_x_data(accounts, categories=[category], num_accounts=num_accounts)
        else:
            accounts = user_recommender.enrich_youtube_data(accounts)
        
        if not accounts:
            logger.warning(f"No accounts found for category: {category}")
            return jsonify({
                'status': 'error',
                'message': 'No accounts found. Try a broader category or different keywords.'
            }), 404
        
        logger.info(f"Found {len(accounts)} accounts for {platform} in category: {category}")
        return jsonify({
            'status': 'success',
            'accounts': accounts
        })
    except Exception as e:
        logger.error(f"Error in recommend_accounts: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/research', methods=['POST'])
def research_content():
    """Research content from specific accounts or topics."""
    data = request.json
    platform = data.get('platform', 'X')
    query = data.get('query', '').strip()
    usernames = data.get('usernames', [])
    
    if not query and not usernames:
        return jsonify({
            'status': 'error',
            'message': 'Please provide a query or usernames to research'
        }), 400
    
    try:
        results = {}
        if platform == 'X':
            results = x_research_agent.run_x_research(query=query, usernames=usernames)
        elif platform == 'youtube':
            results = youtube_research_agent.run_youtube_agent(usernames)
            
        return jsonify({
            'status': 'success',
            'results': results
        })
    except Exception as e:
        logger.error(f"Error in research: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/edit', methods=['POST'])
def edit_content():
    """Edit and improve content using the editor agent."""
    data = request.json
    allow_emojis = data.get('allow_emojis', False)
    
    try:
        editor_agent.run_editor(allow_emojis=allow_emojis)
        
        # Load edited posts
        with open(editor_agent.EDITED_POSTS_FILE, 'r') as f:
            edited_posts = json.load(f)
        
        return jsonify({
            'status': 'success',
            'posts': edited_posts.get('edited_posts', [])
        })
    except Exception as e:
        logger.error(f"Error in editing: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5009)
