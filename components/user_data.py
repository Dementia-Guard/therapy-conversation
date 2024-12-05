from database.db import get_connection

def save_user_data(user_id, user_data):
    """Save user data to the database."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Save basic user information
        about_me = user_data['about_me']
        cursor.execute("""
        INSERT OR REPLACE INTO users (user_id, full_name, birth_date, hometown)
        VALUES (?, ?, ?, ?)
        """, (user_id, about_me['full_name'], about_me['birth_date'], about_me['hometown']))

        # Save user preferences
        for hobby in about_me['hobbies']:
            cursor.execute("""
            INSERT INTO user_preferences (user_id, hobby, favorite_color, favorite_food, favorite_song, favorite_movie)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, hobby, about_me['favorite_things']['color'], about_me['favorite_things']['food'],
                  about_me['favorite_things']['song'], about_me['favorite_things']['movie']))

        # Save life events
        for event in user_data['life_events']:
            cursor.execute("""
            INSERT INTO life_events (user_id, event_title, event_date, description, emotions)
            VALUES (?, ?, ?, ?, ?)
            """, (user_id, event['event_title'], event['date'], event['description'], json.dumps(event['emotions'])))
            event_id = cursor.lastrowid  # Get the auto-incremented event ID

            for person in event['related_people']:
                name, relationship = person.split(" (")
                relationship = relationship.rstrip(")")
                cursor.execute("""
                INSERT INTO life_event_people (event_id, person_name, relationship)
                VALUES (?, ?, ?)
                """, (event_id, name, relationship))

        # Save images with context
        for image in user_data['images_with_context']:
            cursor.execute("""
            INSERT INTO images_with_context (user_id, image_base64, who, where, when, event_title, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, image['image_base64'], json.dumps(image['context']['who']),
                  image['context']['where'], image['context']['when'], image['context']['event_title'],
                  image['context']['description']))

        conn.commit()
        return {"message": "User data saved successfully"}

    except Exception as e:
        conn.rollback()
        return {"error": str(e)}

    finally:
        conn.close()
