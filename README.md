# Airbnb Price Prediction

## Introduction
This project aims to predict Airbnb rental prices using machine learning models. It leverages various data processing, analysis, and modeling techniques to provide a user-friendly price prediction tool. The application benefits both Airbnb hosts and guests by offering fair and optimized price estimates.

---

## Project Workflow

1. **Data Collection**:
   - The data was sourced from the [Airbnb Listings dataset](https://public.opendatasoft.com/explore/dataset/air-bnb-listings/table/?flg=en-us&disjunctive.neighbourhood&disjunctive.column_10&disjunctive.city).
   - Data extraction was orchestrated using **Apache Airflow**, which fetched data from the API in batches, ensuring rate limits were respected.

2. **Data Processing**:
   - The data was extracted, transformed, and cleaned before being stored in a **PostgreSQL** database.
   - **Extract**:
     - Extract data from the public API from the data source.
       
   - **Transformations**:
     - Cleaning missing values and invalid entries.
     - Encoding categorical features into numerical IDs.
     - Clipping numerical values to remove outliers.
       
   - **Load**:
     - The cleaned data was loaded into a normalized schema in PostgreSQL using Airflow's ETL pipeline:
     - Lookup tables were populated.
     - Listings were inserted into a main table, with relationships established via foreign keys.

3. **Exploratory Data Analysis (EDA)**:
   - Analyzed the distribution of features such as prices, property types, and room availability.
   - Visualized relationships between features using:
     - Scatter plots to understand correlations between numerical features and price.
     - Pie charts to explore property types and cancellation policies.
     - Bar graphs to analyze top amenities and their frequency.
   - Identified and handled outliers to improve model performance.
   - Calculated correlations between features to select significant predictors for modeling.

4. **Modeling**:
   - Various regression models were tested to predict Airbnb prices, including:
     - Linear Regression
     - Ridge Regression
     - Lasso Regression
     - Random Forest Regressor
     - CatBoost Regressor
     - LightGBM Regressor
     - XGBoost Regressor
     - Sequential Neural Networks
   - **XGBoost Regressor** was selected as the final model due to its superior performance with:
     - R-squared: 0.88
     - RMSE: 55.42
     - MAE: 21.78

5. **Deployment**:
   - A **Streamlit** application was developed to provide an interactive frontend for price prediction.
   - Users can input property details and receive price predictions, along with visual insights.

---

## Features
- **Fair Pricing Recommendations**:
  - Helps Airbnb hosts optimize rental prices.
  - Enables guests to find properties within their budget.

- **Interactive Visualizations**:
  - Insights on property types, amenities, and other factors influencing price.

- **Dynamic Price Prediction**:
  - Accurate and quick predictions based on user inputs.

---

## Tools & Technologies
- **Backend**:
  - Python, PostgreSQL
  - Machine Learning Libraries: XGBoost, LightGBM, Scikit-learn, TensorFlow

- **Orchestration**:
  - Apache Airflow

- **Frontend**:
  - Streamlit for the web interface
