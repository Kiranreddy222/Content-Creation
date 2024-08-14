# -*- coding: utf-8 -*-
"""
Created on Wed Aug 14 12:09:56 2024

@author: reddy
"""

import streamlit as st
import textwrap
import google.generativeai as genai
import os
from langchain.prompts import PromptTemplate
from datetime import datetime

# Function to convert text to Markdown for display
def to_markdown(text):
    text = text.replace('•', '  *')
    return textwrap.indent(text, '>', predicate=lambda _: True)

# Set up API key and configure the model
os.environ["GOOGLE_API_KEY"] = "AIzaSyDe--BJfueorI6Had8T4Q-euyILn0EXgv0"  # Ensure your API key is correctly set
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

model = genai.GenerativeModel('gemini-1.5-flash')

# Define general prompt template for generating questions
def get_general_prompt_template(question_type, topic):
    if question_type == "multiple-choice":
        return PromptTemplate.from_template(f"""
        Generate a unique set of 10 multiple-choice questions on the topic '{topic}'. Each question should include 4 options with one correct answer. 
        Ensure questions are distinct and do not repeat previous ones.

        Format: 
        Q1: [Question] 
        a. [Option A] 
        b. [Option B] 
        c. [Option C] 
        d. [Option D] 
        Answer: [Correct Option]

        (Repeat for 10 questions)
        """)
    elif question_type == "short-answer":
        return PromptTemplate.from_template(f"""
        Generate a unique set of 10 short-answer questions on the topic '{topic}'. Each question should require a brief response.

        Format: 
        Q1: [Question] 
        Answer: [Short Answer]

        (Repeat for 10 questions)
        """)
    elif question_type == "long-answer":
        return PromptTemplate.from_template(f"""
        Generate a unique set of 10 long-answer questions on the topic '{topic}'. Each question should require a detailed and in-depth response.

        Format: 
        Q1: [Question] 
        Answer: [Long Answer]

        (Repeat for 10 questions)
        """)

# Define general prompt template for answering questions
def get_general_answer_prompt(question):
    return PromptTemplate.from_template(f"""
    Provide a detailed and accurate answer to the following question:

    Question:
    {question}

    Answer:
    """)

# Define refinement prompt
def get_refinement_prompt():
    return PromptTemplate.from_template("""
    Review and refine the following content using the following techniques:

    1. **Chain of Thought:** Reflect on each step of the content generation process.
    2. **React:** Consider how the content will be perceived by the user.
    3. **Input/Output:** Ensure clarity and structure in the content.
    4. **Analogical Reasoning:** Use analogies to enhance the content.
    5. **Step Back:** Review the overall content and process.
    6. **Plan-Solve:** Ensure that the content generation plan is effectively implemented.
    7. **Self-Critique:** Critique the content to improve quality.
    8. **Self-Refinement:** Review and enhance the content by evaluating its own output, identifying improvements, and applying those improvements.

    Content:
    {initial_content}
    """)

# Function to generate and refine content
def generate_and_refine_content(prompt_template, previously_generated):
    try:
        prompt = prompt_template.format()
        initial_response = model.generate_content(prompt)
        
        # Check if the response contains valid content
        if not initial_response or not hasattr(initial_response, 'text'):
            st.error("Failed to generate content. The response is invalid or blocked.")
            return "No content generated.", set()
        
        initial_content = initial_response.text
        
        content_lines = set(line.strip() for line in initial_content.split('\n') if line.strip())
        new_content_lines = content_lines - previously_generated
        if not new_content_lines:
            return "No new unique content was generated.", content_lines
        
        refinement_prompt_template = get_refinement_prompt()
        refinement_prompt = refinement_prompt_template.format(initial_content='\n'.join(new_content_lines))
        refinement_response = model.generate_content(refinement_prompt)
        
        # Check if the response contains valid content
        if not refinement_response or not hasattr(refinement_response, 'text'):
            st.error("Failed to generate refined content. The response is invalid or blocked.")
            return "No refined content generated.", content_lines
        
        refined_content = refinement_response.text
        
        return refined_content, content_lines
    
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return "An error occurred during content generation.", set()

# Function to generate answers to general questions
def answer_user_question(question):
    try:
        answer_prompt = get_general_answer_prompt(question)
        initial_response = model.generate_content(answer_prompt.format(question=question))
        
        # Check if the response contains valid content
        if not initial_response or not hasattr(initial_response, 'text'):
            st.error("Failed to generate an answer. The response is invalid or blocked.")
            return "No answer generated."
        
        initial_answer = initial_response.text

        refinement_prompt_template = get_refinement_prompt()
        refinement_response = model.generate_content(refinement_prompt_template.format(initial_content=initial_answer))
        
        # Check if the response contains valid content
        if not refinement_response or not hasattr(refinement_response, 'text'):
            st.error("Failed to generate refined answer. The response is invalid or blocked.")
            return "No refined answer generated."
        
        refined_answer = refinement_response.text
        
        return refined_answer
    
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return "An error occurred during answer generation."

# Streamlit application
def main():
    st.title("General Question Answerer")
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.write(f"Current Date and Time: {current_time}")

    tab1, tab2 = st.tabs(["Generate Questions", "Ask a Question"])

    with tab1:
        st.write("Generate questions")
        
        # Input field for topic
        topic = st.text_input("Enter the topic for the questions:")
        
        # Dropdown for question type
        question_type = st.selectbox("Select the type of questions to generate", 
                                    ["multiple-choice", "short-answer", "long-answer"])

        if st.button("Generate and Refine Questions"):
            if topic:
                prompt_template = get_general_prompt_template(question_type, topic)
                with st.spinner(f"Generating and refining {question_type} questions on '{topic}'..."):
                    refined_content, _ = generate_and_refine_content(prompt_template, set())
                    st.markdown(to_markdown(refined_content))
            else:
                st.warning("Please enter a topic to generate questions.")
    
    with tab2:
        st.write("Ask a question")
        user_question = st.text_area("Enter your question here:")

        if st.button("Get Answer"):
            if user_question:
                with st.spinner("Generating answer..."):
                    answer = answer_user_question(user_question)
                    st.markdown(to_markdown(answer))
            else:
                st.warning("Please enter a question to get an answer.")

if __name__ == "__main__":
    main()
