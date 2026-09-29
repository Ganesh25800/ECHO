
class QueriesHelper:

    GET_USER_INTEREST = """
        SELECT * FROM user_interests WHERE user_id = ?
    """

    GET_USER_FACE_EMBEDDINGS = """
        SELECT * FROM face_embeddings WHERE user_id = ? ORDER BY created_at DESC LIMIT 500
    """

    GET_ALL_USER_PROFILES = """
        SELECT * FROM users 
    """

    SEARCH_SYSTEM_WITH_UNIQUE_ID = """
        SELECT 1 FROM systems WHERE system_id = ? LIMIT 1
    """

    ENTER_SYSTEM_LOG = """
        INSERT INTO startup_logs (
            system_id,
            ip_address,
            available_ram_gb,
            available_disk_gb,
            memory_usage,
            disk_usage,
            internet_connected,
            location,
            battery_percentage,
            echo_version,
            started_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """

    ADD_SYSTEM = """
        INSERT INTO systems (
            system_id,
            os,
            total_ram_gb,
            total_disk_gb
        )
        VALUES (?,?,?,?)
    """

    
    CREATE_SYSTEM_TABLE = """
        CREATE TABLE IF NOT EXISTS systems (
            system_id TEXT PRIMARY KEY,
            os TEXT NOT NULL,
            total_ram_gb REAL NOT NULL,
            total_disk_gb REAL NOT NULL
        );
    """

    CREATE_STARTUP_LOGS_TABLE = """
        CREATE TABLE IF NOT EXISTS startup_logs (
            startup_log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            system_id TEXT NOT NULL,
            ip_address TEXT,
            available_ram_gb REAL,
            available_disk_gb REAL,
            memory_usage REAL,
            disk_usage REAL,
            internet_connected INTEGER NOT NULL DEFAULT 0,
            location TEXT,
            battery_percentage REAL,
            echo_version TEXT,
            started_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (system_id)
                REFERENCES systems(system_id)
                ON DELETE CASCADE
        );
    """

    CREATE_USERS_TABLE = """
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            preferred_name TEXT,
            gender TEXT,
            age INTEGER,
            date_of_birth DATE,
            preferred_language TEXT,
            timezone TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """

    CREATE_USER_INTERESTS_TABLE = """
        CREATE TABLE IF NOT EXISTS user_interests (
            interest_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            interest TEXT NOT NULL,
            confidence REAL DEFAULT 1.0,
            source TEXT NOT NULL,
            current_interest INTEGER NOT NULL DEFAULT 1
                CHECK (current_interest IN (0, 1)),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
                REFERENCES users(user_id)
                ON DELETE CASCADE
        );
    """

    CREATE_FACE_EMBEDDINGS_TABLE = """
        CREATE TABLE IF NOT EXISTS face_embeddings (
            embedding_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            embedding TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
                REFERENCES users(user_id)
                ON DELETE CASCADE
        );
    """

    CREATE_CONVERSATIONS_TABLE = """
        CREATE TABLE IF NOT EXISTS conversations (
            conversation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,

            user_input TEXT NOT NULL,
            echo_response TEXT,

            input_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            response_at DATETIME,

            FOREIGN KEY (user_id)
                REFERENCES users(user_id)
                ON DELETE CASCADE
        );
    """

    CREATE_CONVERSATION_STATS_TABLE = """
        CREATE TABLE IF NOT EXISTS conversation_stats (
            stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL UNIQUE,

            input_type TEXT,
            input_category TEXT,
            input_tone TEXT,
            language TEXT,
            language_fluency TEXT,

            input_word_count INTEGER,
            input_token_count INTEGER,
            response_word_count INTEGER,
            response_token_count INTEGER,

            processing_time_ms REAL,
            first_token_time_ms REAL,
            response_completion_time_ms REAL,

            model_used TEXT,

            rag_used INTEGER DEFAULT 0
                CHECK (rag_used IN (0, 1)),

            tools_used INTEGER DEFAULT 0
                CHECK (tools_used IN (0, 1)),

            response_correctness REAL,
            response_confidence REAL,

            user_feedback TEXT,
            user_rating INTEGER,

            response_regenerated INTEGER DEFAULT 0
                CHECK (response_regenerated IN (0, 1)),

            error_occurred INTEGER DEFAULT 0
                CHECK (error_occurred IN (0, 1)),

            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (conversation_id)
                REFERENCES conversations(conversation_id)
                ON DELETE CASCADE
        );
    """

    CREATE_CONVERSATION_EMOTIONS_TABLE = """
        CREATE TABLE IF NOT EXISTS conversation_emotions (
            emotion_id INTEGER PRIMARY KEY AUTOINCREMENT,

            conversation_id INTEGER NOT NULL,

            category TEXT NOT NULL
                CHECK (category IN ('user', 'echo')),

            happy REAL NOT NULL DEFAULT 0.0
                CHECK (happy BETWEEN 0.0 AND 1.0),

            sad REAL NOT NULL DEFAULT 0.0
                CHECK (sad BETWEEN 0.0 AND 1.0),

            anger REAL NOT NULL DEFAULT 0.0
                CHECK (anger BETWEEN 0.0 AND 1.0),

            confused REAL NOT NULL DEFAULT 0.0
                CHECK (confused BETWEEN 0.0 AND 1.0),

            frustrated REAL NOT NULL DEFAULT 0.0
                CHECK (frustrated BETWEEN 0.0 AND 1.0),

            primary_emotion TEXT,

            emotion_confidence REAL
                CHECK (
                    emotion_confidence IS NULL OR
                    emotion_confidence BETWEEN 0.0 AND 1.0
                ),

            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (conversation_id)
                REFERENCES conversations(conversation_id)
                ON DELETE CASCADE
        );
    """