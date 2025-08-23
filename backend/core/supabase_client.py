from supabase import create_client, Client
from core.config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Supabase client
supabase_client: Client = None

try:
    if settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY and not settings.SUPABASE_URL.startswith("https://placeholder"):
        supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY
        )
        logger.info("✅ Supabase client initialized successfully")
    else:
        logger.warning("⚠️  Supabase credentials not configured, using placeholder client")
        supabase_client = None
except Exception as e:
    logger.error(f"❌ Failed to initialize Supabase client: {e}")
    supabase_client = None

# Test connection
def test_connection():
    """Test Supabase connection"""
    if not supabase_client:
        logger.warning("⚠️  Supabase client not configured, skipping connection test")
        return False
    try:
        response = supabase_client.table('users').select('count').limit(1).execute()
        logger.info("✅ Supabase connection test successful")
        return True
    except Exception as e:
        logger.error(f"❌ Supabase connection test failed: {e}")
        return False

# Get user by ID
async def get_user_by_id(user_id: str):
    """Get user by ID from Supabase"""
    if not supabase_client:
        logger.warning("⚠️  Supabase client not configured, returning None for user")
        return None
    try:
        response = supabase_client.table('users').select('*').eq('id', user_id).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        logger.error(f"Error getting user by ID: {e}")
        return None

# Verify user exists
async def verify_user_exists(user_id: str) -> bool:
    """Verify if user exists in database"""
    if not supabase_client:
        logger.warning("⚠️  Supabase client not configured, returning False for user verification")
        return False
    try:
        response = supabase_client.table('users').select('id').eq('id', user_id).execute()
        return len(response.data) > 0
    except Exception as e:
        logger.error(f"Error verifying user exists: {e}")
        return False
