import streamlit as st
from groq import Groq
from dotenv import load_dotenv
import os
import sqlite3


# Load API key
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

# If not found in .env, use Streamlit Secrets
if not api_key:
    api_key = st.secrets["GROQ_API_KEY"]

client = Groq(api_key=api_key)




# Database setup

def create_database():

    connection = sqlite3.connect("progress.db")

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS progress(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT UNIQUE
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS scores(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT,
            score INTEGER,
            total INTEGER
        )
        """
    )

    connection.commit()

    connection.close()



def save_topic(topic):

    connection = sqlite3.connect("progress.db")

    cursor = connection.cursor()

    cursor.execute(
        "INSERT OR IGNORE INTO progress(topic) VALUES(?)",
        (topic,)
    )

    connection.commit()

    connection.close()



def get_topics():

    connection = sqlite3.connect("progress.db")

    cursor = connection.cursor()

    cursor.execute(
        "SELECT topic FROM progress"
    )

    data = cursor.fetchall()

    connection.close()

    return data



def save_score(topic, score, total):

    connection = sqlite3.connect("progress.db")

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO scores(topic, score, total)
        VALUES(?,?,?)
        """,
        (topic, score, total)
    )

    connection.commit()

    connection.close()



def get_scores():

    connection = sqlite3.connect("progress.db")

    cursor = connection.cursor()

    cursor.execute(
        "SELECT score,total FROM scores"
    )

    data = cursor.fetchall()

    connection.close()

    return data



create_database()



# Page settings

st.set_page_config(
    page_title="AI Learning Buddy",
    layout="wide"
)



# Session memory

if "messages" not in st.session_state:

    st.session_state.messages = []


if "quiz_data" not in st.session_state:

    st.session_state.quiz_data = None



# Title

st.title("AI Learning Buddy")

st.write(
    "Your personal AI tutor to learn concepts easily."
)



# Dashboard

st.header("Learning Dashboard")


completed_topics = get_topics()

topic_count = len(completed_topics)


scores = get_scores()


col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "Topics Completed",
        topic_count
    )


with col2:

    st.metric(
        "Subjects Available",
        6
    )


with col3:

    if len(scores) > 0:

        total_score = sum(
            item[0] for item in scores
        )

        total_questions = sum(
            item[1] for item in scores
        )

        average = int(
            (total_score / total_questions) * 100
        )

        st.metric(
            "Average Quiz Score",
            f"{average}%"
        )

    else:

        st.metric(
            "Average Quiz Score",
            "0%"
        )



if topic_count > 0:

    progress = min(
        topic_count / 10,
        1.0
    )

    st.progress(progress)

    st.write(
        f"Learning Progress: {int(progress * 100)}%"
    )


else:

    st.write(
        "Start learning to track progress."
    )



# Sidebar

st.sidebar.header("Learning Options")


subject = st.sidebar.selectbox(
    "Select Subject",
    [
        "Python",
        "Data Structures",
        "Cyber Security",
        "Artificial Intelligence",
        "Database Management",
        "Computer Networks"
    ]
)



st.sidebar.header("Completed Topics")


topics = get_topics()


if len(topics) == 0:

    st.sidebar.write(
        "No topics completed yet."
    )


else:

    for item in topics:

        st.sidebar.write(
            item[0]
        )



# User input

topic = st.text_input(
    "Enter the topic you want to learn"
)



activity = st.selectbox(
    "Select Learning Activity",
    [
        "Explain Topic",
        "Real Life Example",
        "Create Quiz",
        "Interview Questions",
        "Feedback"
    ]
)



# Generate response

if st.button("Generate Answer"):


    if topic.strip() == "":

        st.warning(
            "Please enter a topic."
        )


    else:


        if activity == "Create Quiz":


            prompt = f"""

            Create a multiple choice quiz.

            Subject: {subject}

            Topic: {topic}


            Generate 5 questions.


            Use this format:


            Question:
            question text


            Options:
            A) option
            B) option
            C) option
            D) option


            Answer:
            correct option letter


            Explanation:
            short explanation

            """

        else:


            prompt = f"""

            You are an AI tutor.


            Subject: {subject}

            Topic: {topic}

            Activity: {activity}


            Explain in simple student-friendly language.

            Give examples wherever required.

            """



        try:


            st.session_state.messages.append(
                {
                    "role": "user",
                    "content": prompt
                }
            )


            response = client.chat.completions.create(

                model="llama-3.1-8b-instant",

                messages=st.session_state.messages

            )


            answer = response.choices[0].message.content



            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": answer
                }
            )



            if activity == "Create Quiz":

                st.session_state.quiz_data = answer


            else:

                save_topic(topic)

                st.subheader(
                    "AI Tutor Response"
                )

                st.write(answer)



        except Exception as error:


            st.error(
                "Unable to generate response."
            )

            st.write(error)



# Quiz Section


if st.session_state.quiz_data:


    st.subheader(
        "Quiz"
    )


    questions = st.session_state.quiz_data.split(
        "Question:"
    )


    answers = []

    total_questions = 0



    for question in questions[1:]:


        lines = question.strip().split("\n")


        question_text = lines[0]


        st.write(
            question_text
        )


        options = []

        correct_answer = ""



        for line in lines:


            line = line.strip()


            if line.startswith(("A)", "B)", "C)", "D)")):

                options.append(line)


            if line.startswith("Answer:"):

                correct_answer = line.replace(
                    "Answer:",
                    ""
                ).strip()



        if options:


            selected = st.radio(

                "Select answer",

                options,

                key=question_text

            )


            answers.append(
                (
                    selected[0],
                    correct_answer
                )
            )


        total_questions += 1




    if st.button("Submit Quiz"):


        score = 0


        for answer in answers:


            if answer[0] == answer[1]:

                score += 1



        save_score(
            topic,
            score,
            total_questions
        )


        st.success(
            f"Your Score: {score}/{total_questions}"
        )



# Chat history

st.subheader(
    "Conversation History"
)


for message in st.session_state.messages:


    if message["role"] == "user":

        st.write("You:")
        st.write(message["content"])


    else:

        st.write("AI Tutor:")
        st.write(message["content"])
