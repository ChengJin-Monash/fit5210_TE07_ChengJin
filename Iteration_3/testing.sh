## ==================== Server ip - 20.11.48.94 ====================

## ==================== Function CV_Builder ====================
# Testing URL --------------------
http://20.11.48.94:8000/generate_cv

# Testing cmd (Linux) --------------------
curl -X POST http://20.11.48.94:8000/generate_cv \
  -H "Content-Type: application/json" \
  -d @test_cv.json


# Testing Json file --------------------
{
    "name": "John Smith",
    "education": [
      {
        "degree_type": "Diploma",
        "degree_name": "Office Administration",
        "institution": "Sydney TAFE",
        "year_start": 1988,
        "year_end": 1990
      }
    ],
    "work_experience": [
      {
        "job_title": "Mailroom Supervisor",
        "organization": "Australia Post",
        "year_start": 1991,
        "year_end": 2005
      },
      {
        "job_title": "Administrative Assistant",
        "organization": "City Council",
        "year_start": 2006,
        "year_end": 2021
      },
      {
        "job_title": "Part-time Data Entry Specialist",
        "organization": "Freelance",
        "year_start": 2022,
        "year_end": 2024
      }
    ]
  }


## Function Chatbot ====================
# Testing URL --------------------
http://20.11.48.94:8001/chat_stream

# Testing cmd (Linux) --------------------
# Chat function
curl -N -X POST http://20.11.48.94:8001/chat_stream   -H "Content-Type: application/json"   -d '{
    "prompt": "who are you?",
    "session_id": "test_user_1"
  }'

curl -N -X POST http://20.11.48.94:8001/chat_stream   -H "Content-Type: application/json"   -d '{
    "prompt": "what question did i just asked you?",
    "session_id": "test_user_1"
  }'

  curl -N -X POST http://20.11.48.94:8001/chat_stream   -H "Content-Type: application/json"   -d '{
    "prompt": "how do i make a coffee?",
    "session_id": "test_user_1"
  }'

  curl -N -X POST http://20.11.48.94:8001/chat_stream   -H "Content-Type: application/json"   -d '{
    "prompt": "how do i find the ai reseurm builder",
    "session_id": "test_user_1"
  }'

# Reset function
# for session_id = test_user_1
curl -X POST http://20.11.48.94:8001/chat_reset   -H "Content-Type: application/json"   -d '{"session_id": "test_user_1"}'

# for reset all session, set session_id = all
curl -X POST http://20.11.48.94:8001/chat_reset   -H "Content-Type: application/json"   -d '{"session_id": "all"}'
