from user_recommender import run_user_recommender
from research_agent import run_research_agent
from content_creator import run_content_creator
from editor_agent import run_editor
from scheduler_agent import schedule

def run_pipeline():
    """Run the complete content generation pipeline."""
    print("\nX/YouTube Content Generation Pipeline")
    print("===================================")
    
    print("\nStep 1: Recommend and approve X/YouTube accounts")
    run_user_recommender()
    
    print("\nStep 2: Research content and get feedback")
    run_research_agent()
    
    print("\nStep 3: Create posts")
    run_content_creator()
    
    print("\nStep 4: Edit posts")
    run_editor()
    
    print("\nStep 5: Schedule posts")
    schedule()
    
    print("\nPipeline complete! Check the following files for results:")
    print("- target_accounts.json: Approved X/YouTube accounts")
    print("- tweets.json: Downloaded X tweets")
    print("- youtube_data.json: Downloaded YouTube data")
    print("- feedback.json: ChatGPT's content analysis")
    print("- raw_posts.json: Generated posts")
    print("- edited_posts.md: Final edited posts")

if __name__ == "__main__":
    run_pipeline()
