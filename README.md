# Smart Water Usage Controller using Fuzzy Logic and Neural Network

This is a web-based project built using Python, Flask, HTML, CSS, JavaScript, and NumPy.  
It helps recommend water usage decisions based on two inputs:

- Water Usage in liters
- Water Availability in percentage

The project combines:

- Fuzzy Logic for human-like decision making
- Neural Network for learning from data and making predictions

## Features

- Interactive web interface
- Smooth scrolling and modern UI
- Fuzzy logic-based recommendations
- Neural network prediction
- Dataset upload and retraining support
- Human-readable output instead of only numbers

## How to Run

Install the required libraries:

- pip install flask numpy werkzeug

Run the application:

- python app.py

Open the browser and go to:

http://127.0.0.1:5000

Dataset Format:

The dataset should contain columns like: usage_liters,availability_percent,recommendation_index or usage_liters,availability_percent,recommendation_label