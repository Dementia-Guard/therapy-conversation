-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,  -- Unique identifier for the user
    full_name TEXT NOT NULL,   -- User's full name
    birth_date DATE NOT NULL,  -- User's date of birth
    hometown TEXT              -- User's hometown
);

-- User preferences table (hobbies and favorites)
CREATE TABLE IF NOT EXISTS user_preferences (
    user_id TEXT NOT NULL,                 -- Foreign key to users table
    hobby TEXT,                            -- User's hobby
    favorite_color TEXT,                   -- Favorite color
    favorite_food TEXT,                    -- Favorite food
    favorite_song TEXT,                    -- Favorite song
    favorite_movie TEXT,                   -- Favorite movie
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Life events table
CREATE TABLE IF NOT EXISTS life_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Unique identifier for the event
    user_id TEXT NOT NULL,                       -- Foreign key to users table
    event_title TEXT NOT NULL,                   -- Title of the event
    event_date DATE,                             -- Date of the event
    description TEXT,                            -- Description of the event
    emotions TEXT,                               -- Emotions related to the event (JSON array)
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Related people for life events
CREATE TABLE IF NOT EXISTS life_event_people (
    person_id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Unique identifier for the person
    event_id INTEGER NOT NULL,                    -- Foreign key to life_events table
    person_name TEXT NOT NULL,                    -- Name of the related person
    relationship TEXT,                            -- Relationship with the user
    FOREIGN KEY (event_id) REFERENCES life_events(event_id)
);

-- Images with context table
CREATE TABLE IF NOT EXISTS images_with_context (
    image_id INTEGER PRIMARY KEY AUTOINCREMENT,   -- Unique identifier for the image
    user_id TEXT NOT NULL,                        -- Foreign key to users table
    image_base64 TEXT NOT NULL,                   -- Base64 encoded image data
    context_who TEXT,                             -- People in the image (JSON array)
    context_where TEXT,                           -- Location where the image was taken
    context_when DATE,                            -- Date of the event in the image
    event_title TEXT,                             -- Title of the event in the image
    description TEXT,                             -- Description of the image
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
CREATE TABLE IF NOT EXISTS user_conversations (
    conversation_id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Unique identifier for each conversation
    user_id TEXT NOT NULL,                               -- Foreign key to the users table
    user_message TEXT NOT NULL,                          -- The message from the user
    chatbot_response TEXT NOT NULL,                       -- The message from the chatbot
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,        -- Timestamp for when the message was sent
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS user_answers (
    answer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    accuracy TEXT NOT Null,
    question_type TEXT NOT NULL,  -- 'main' or 'sub'
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

